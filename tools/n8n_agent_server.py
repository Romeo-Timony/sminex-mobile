"""Локальный мост: n8n -> OpenAI Responses API -> файлы проекта.

Запускайте этот файл только на компьютере, где находится проект. Сервер не
сохраняет API-ключ: он берёт его из переменной окружения OPENAI_API_KEY.
"""

from __future__ import annotations

import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import time
from threading import Lock
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOST = os.environ.get("N8N_AGENT_HOST", "0.0.0.0")
PORT = int(os.environ.get("N8N_AGENT_PORT", "5000"))
TOKEN = os.environ.get("N8N_AGENT_TOKEN", "")
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5")
EXCLUDED_PARTS = {".git", ".idea", ".venv", ".venv-project", "allure-report", "allure-results", "__pycache__"}
JIRA_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
MANIFEST_PATH = PROJECT_ROOT / "tests" / "review" / "manifest.json"
MANIFEST_LOCK = Lock()
APPIUM_SERVER = os.environ.get("APPIUM_SERVER", "http://127.0.0.1:4723")
APPIUM_START_TIMEOUT_SECONDS = int(os.environ.get("APPIUM_START_TIMEOUT_SECONDS", "30"))


def project_files() -> list[str]:
    """Return a concise, safe project inventory for the model context."""
    files: list[str] = []
    for path in PROJECT_ROOT.rglob("*"):
        if any(part in EXCLUDED_PARTS for part in path.relative_to(PROJECT_ROOT).parts):
            continue
        if path.is_file() and path.stat().st_size <= 100_000:
            files.append(path.relative_to(PROJECT_ROOT).as_posix())
    return sorted(files)[:250]


def safe_target(relative_path: str) -> Path:
    target = (PROJECT_ROOT / relative_path).resolve()
    if PROJECT_ROOT not in target.parents and target != PROJECT_ROOT:
        raise ValueError("Path must stay inside the project")
    parts = target.relative_to(PROJECT_ROOT).parts
    if not parts or any(part in EXCLUDED_PARTS for part in parts):
        raise ValueError("This path is protected")
    return target


def validate_jira_key(value: object) -> str:
    if not isinstance(value, str) or not JIRA_KEY_PATTERN.fullmatch(value):
        raise ValueError("'jiraKey' must look like 'KAN-1'")
    return value


def review_target(jira_key: str, generated_path: str) -> Path:
    relative = Path(generated_path)
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".py":
        raise ValueError("Generated test paths must be relative Python files")
    if not relative.parts or relative.parts[0] not in {"ui", "api", "e2e"}:
        raise ValueError("Generated tests must be placed in ui/, api/, or e2e/")
    return safe_target((Path("tests") / "review" / jira_key / relative).as_posix())


def update_manifest(jira_key: str, files: list[dict], mapping: list[dict]) -> None:
    """Record generated review files without overwriting records for other tasks."""
    with MANIFEST_LOCK:
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            manifest = {"files": []}
        except json.JSONDecodeError as error:
            raise RuntimeError("Review manifest is not valid JSON") from error
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            raise RuntimeError("Review manifest has an invalid format")

        case_ids_by_source: dict[str, list[str]] = {}
        for item in mapping:
            if not isinstance(item, dict):
                continue
            case_id = item.get("test_case_id")
            if not isinstance(case_id, str):
                continue
            for source in item.get("files", []):
                if isinstance(source, str):
                    case_ids_by_source.setdefault(source.replace("\\", "/"), []).append(case_id)

        generated_paths = {item["path"] for item in files}
        manifest["files"] = [item for item in manifest["files"] if item.get("path") not in generated_paths]
        manifest["files"].extend(
            {
                "jira_key": jira_key,
                "path": item["path"],
                "status": "pending_review",
                "test_case_ids": case_ids_by_source.get(item["source_path"], []),
            }
            for item in files
        )
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_review_task(jira_key: str) -> None:
    """Remove the previous generated set for one task before saving its replacement."""
    review_directory = PROJECT_ROOT / "tests" / "review" / jira_key
    with MANIFEST_LOCK:
        if review_directory.exists():
            shutil.rmtree(review_directory)
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except json.JSONDecodeError as error:
            raise RuntimeError("Review manifest is not valid JSON") from error
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            raise RuntimeError("Review manifest has an invalid format")
        manifest["files"] = [item for item in manifest["files"] if item.get("jira_key") != jira_key]
        MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def appium_is_ready() -> bool:
    try:
        with urlopen(f"{APPIUM_SERVER.rstrip('/')}/status", timeout=2) as response:
            payload = json.load(response)
        return bool(payload.get("value", {}).get("ready", False))
    except (URLError, TimeoutError, json.JSONDecodeError):
        return False


def appium_command() -> list[str]:
    configured = os.environ.get("APPIUM_COMMAND", "").strip()
    if configured:
        return configured.split()
    executable = shutil.which("appium.cmd") or shutil.which("appium")
    if executable:
        return [executable]
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if npx:
        return [npx, "appium"]
    raise RuntimeError("Appium CLI was not found; set APPIUM_COMMAND to the Appium executable")


def ensure_appium() -> None:
    if appium_is_ready():
        return
    command = appium_command()
    parsed_url = urlparse(APPIUM_SERVER)
    host = parsed_url.hostname or "127.0.0.1"
    port = parsed_url.port or 4723
    command.extend(["--address", host, "--port", str(port)])
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
    except OSError as error:
        raise RuntimeError("Unable to start Appium") from error

    deadline = time.monotonic() + APPIUM_START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if appium_is_ready():
            return
        time.sleep(1)
    raise RuntimeError("Appium did not become ready within the configured timeout")


def validate_test_cases(value: object) -> list[dict]:
    if not isinstance(value, list) or not value or len(value) > 100:
        raise ValueError("'testCases' must be a non-empty array containing no more than 100 cases")
    for case in value:
        if not isinstance(case, dict) or not all(isinstance(case.get(field), str) and case[field].strip() for field in ("id", "title")):
            raise ValueError("Every test case needs non-empty string fields 'id' and 'title'")
        qase_case_id = case.get("qaseCaseId", case.get("qase_case_id"))
        if qase_case_id is not None and (
            not isinstance(qase_case_id, (str, int)) or not str(qase_case_id).isdecimal()
        ):
            raise ValueError(f"Test case {case['id']} needs a numeric optional 'qaseCaseId'")
        steps = case.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"Test case {case['id']} must contain a non-empty 'steps' array")
        for step in steps:
            if not isinstance(step, dict) or not all(isinstance(step.get(field), str) and step[field].strip() for field in ("action", "expected")):
                raise ValueError(f"Every step in {case['id']} needs non-empty 'action' and 'expected' fields")
    return value


def project_context() -> dict[str, str]:
    context: dict[str, str] = {}
    for relative in project_files():
        if not relative.endswith(".py") or not relative.startswith(("pages/", "tests/", "config/")):
            continue
        content = (PROJECT_ROOT / relative).read_text(encoding="utf-8", errors="replace")
        if len(content) <= 15_000:
            context[relative] = content
        if len(context) == 20:
            break
    return context


def response_text(response: dict) -> str:
    """Extract text from the raw HTTP Responses API payload."""
    parts: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text" and isinstance(content.get("text"), str):
                parts.append(content["text"])
    if not parts:
        raise RuntimeError("The model response contains no text output")
    return "\n".join(parts)


def ask_model(task: str, platform: str, jira_key: str, test_cases: list[dict]) -> dict:
    instructions = """You edit a Python mobile-test project. Generate the smallest safe implementation for the
provided manual test cases using the page objects and test conventions in the project context. Never invent
unavailable selectors or APIs: list the affected test-case IDs and gaps in warnings. Never create `pass`, no-op,
or always-green tests. Generate code only for actions that can be executed through existing Page Object/API-client
methods and the configured Appium Android session. Use only relative paths starting with ui/, api/, or e2e/; the
server places them under the review directory. Every generated test must have @pytest.mark.review as well as the
existing relevant test markers. If a manual test case includes qaseCaseId, its generated test must include
@pytest.mark.qase_case("<qaseCaseId>") directly above its @allure.id decorator. This is the only allowed link to a
manual Qase case; do not change Qase's Automation Status. Use `logged_out_driver`, `auth_form_driver`, or another existing Appium fixture for
UI/E2E tests, and include an assertion that validates each executable expected result."""
    response_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "changes": {"type": "array", "items": {"type": "object", "additionalProperties": False, "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
            "test_case_mapping": {"type": "array", "items": {"type": "object", "additionalProperties": False, "properties": {"test_case_id": {"type": "string"}, "files": {"type": "array", "items": {"type": "string"}}}, "required": ["test_case_id", "files"]}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["changes", "test_case_mapping", "warnings"],
    }
    payload = {
        "model": MODEL,
        "instructions": instructions,
        "input": json.dumps({"task": task, "platform": platform, "jiraKey": jira_key, "testCases": test_cases, "project_context": project_context()}, ensure_ascii=False),
        "text": {"format": {"type": "json_schema", "name": "mobile_test_changes", "strict": True, "schema": response_schema}},
    }
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            data = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"OpenAI API returned HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError("Cannot reach the OpenAI API") from error

    try:
        result = json.loads(response_text(data))
        changes = result["changes"]
        mapping = result["test_case_mapping"]
        warnings = result["warnings"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError("The model returned an invalid change set") from error
    if not isinstance(changes, list) or not all(
        isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("content"), str)
        for item in changes
    ):
        raise RuntimeError("The model returned an invalid change set")
    if not isinstance(mapping, list) or not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
        raise RuntimeError("The model returned an invalid change set")
    return {"changes": changes, "test_case_mapping": mapping, "warnings": warnings}


class Handler(BaseHTTPRequestHandler):
    server_version = "N8nProjectAgent/1.0"

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")

    def respond(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.respond(HTTPStatus.OK, {"status": "ok", "project": PROJECT_ROOT.name})
        else:
            self.respond(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/agent/trigger-codegen":
            self.respond(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        if not TOKEN or not API_KEY:
            self.respond(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Server secrets are not configured"})
            return
        supplied = self.headers.get("Authorization", "").removeprefix("Bearer ")
        if not hmac.compare_digest(supplied, TOKEN):
            self.respond(HTTPStatus.UNAUTHORIZED, {"error": "Invalid authorization token"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 100_000:
                raise ValueError("Invalid request size")
            request = json.loads(self.rfile.read(length))
            task = request["task"]
            if not isinstance(task, str) or not task.strip() or len(task) > 30_000:
                raise ValueError("'task' must be a non-empty string")
            test_cases = validate_test_cases(request.get("testCases"))
            platform = request.get("platform", "android")
            if not isinstance(platform, str) or not platform.strip() or len(platform) > 50:
                raise ValueError("'platform' must be a non-empty string")
            jira_key = validate_jira_key(request.get("jiraKey", request.get("jira_key")))
            uses_appium = platform.strip().lower() == "android" and any(
                str(case.get("type", "")).upper() in {"UI", "E2E"}
                for case in test_cases
            )
            if uses_appium:
                ensure_appium()
            model_result = ask_model(task, platform, jira_key, test_cases)
            validated = []
            for item in model_result["changes"]:
                if "@pytest.mark.review" not in item["content"]:
                    raise RuntimeError("Generated tests must use @pytest.mark.review")
                path = review_target(jira_key, item["path"])
                validated.append({"source_path": item["path"].replace("\\", "/"), "path": str(path.relative_to(PROJECT_ROOT)), "content": item["content"]})
            if request.get("apply") is True:
                replace_review = request.get("replaceReview", True)
                if not isinstance(replace_review, bool):
                    raise ValueError("'replaceReview' must be a boolean")
                if replace_review:
                    replace_review_task(jira_key)
                for item in validated:
                    path = safe_target(item["path"])
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(item["content"], encoding="utf-8")
                update_manifest(jira_key, validated, model_result["test_case_mapping"])
                self.respond(HTTPStatus.OK, {"status": "applied", "jira_key": jira_key, "appium_ready": uses_appium, "replaced_review": replace_review, "changed_files": [item["path"] for item in validated], "manifest": str(MANIFEST_PATH.relative_to(PROJECT_ROOT)), "test_case_mapping": model_result["test_case_mapping"], "warnings": model_result["warnings"]})
            else:
                self.respond(HTTPStatus.OK, {"status": "preview", "jira_key": jira_key, "appium_ready": uses_appium, "changes": validated, "test_case_mapping": model_result["test_case_mapping"], "warnings": model_result["warnings"]})
        except (ValueError, KeyError, json.JSONDecodeError) as error:
            self.respond(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except RuntimeError as error:
            self.respond(HTTPStatus.BAD_GATEWAY, {"error": str(error)})


def main() -> None:
    missing = [name for name, value in {"OPENAI_API_KEY": API_KEY, "N8N_AGENT_TOKEN": TOKEN}.items() if not value]
    if missing:
        print("Missing environment variables: " + ", ".join(missing), file=sys.stderr)
        raise SystemExit(2)
    print(f"Serving {PROJECT_ROOT} on http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
