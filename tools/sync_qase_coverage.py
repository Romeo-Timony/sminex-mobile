"""Synchronize verified Python tests with coverage fields on manual Qase cases.

Only a test function carrying ``@pytest.mark.qase_case("<numeric id>")`` is
eligible.  This makes the manual-case relationship explicit and prevents a
title-based guess from updating the wrong Qase case.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = PROJECT_ROOT / "tests"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from clients.qase_api_client import QaseApiClient
FIELD_ENVIRONMENT_NAMES = {
    "coverage": "QASE_FIELD_AUTOMATION_COVERAGE",
    "type": "QASE_FIELD_AUTOMATION_TYPE",
    "code_path": "QASE_FIELD_AUTOMATION_CODE_PATH",
    "test_id": "QASE_FIELD_AUTOMATION_TEST_ID",
    "note": "QASE_FIELD_AUTOMATION_NOTE",
}


@dataclass(frozen=True)
class CoverageLink:
    qase_case_id: int
    automation_type: str
    code_path: str
    test_id: str


def marker_argument(decorator: ast.expr, marker_name: str) -> str | None:
    if not isinstance(decorator, ast.Call) or not decorator.args:
        return None
    function = decorator.func
    if not (
        isinstance(function, ast.Attribute)
        and function.attr == marker_name
        and isinstance(function.value, ast.Attribute)
        and function.value.attr == "mark"
    ):
        return None
    value = decorator.args[0]
    return value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None


def allure_id(decorator: ast.expr) -> str | None:
    if not isinstance(decorator, ast.Call) or not decorator.args:
        return None
    if not isinstance(decorator.func, ast.Attribute) or decorator.func.attr != "id":
        return None
    value = decorator.args[0]
    return value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None


def discover_links(paths: list[Path]) -> list[CoverageLink]:
    links: list[CoverageLink] = []
    for path in paths:
        relative = path.resolve().relative_to(PROJECT_ROOT).as_posix()
        parts = path.resolve().relative_to(TEST_ROOT).parts
        if not parts or parts[0] not in {"ui", "api", "e2e"}:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            qase_id = next((value for item in node.decorator_list if (value := marker_argument(item, "qase_case"))), None)
            if qase_id is None:
                continue
            if not qase_id.isdecimal():
                raise ValueError(f"{relative}:{node.lineno} qase_case must be a numeric Qase case ID")
            test_identifier = next((value for item in node.decorator_list if (value := allure_id(item))), node.name)
            links.append(CoverageLink(int(qase_id), parts[0].upper(), relative, test_identifier))
    return links


def configured_field_ids() -> dict[str, int]:
    values: dict[str, int] = {}
    for key, environment_name in FIELD_ENVIRONMENT_NAMES.items():
        value = os.environ.get(environment_name, "")
        if not value.isdecimal():
            raise RuntimeError(f"{environment_name} must be a numeric Qase custom-field ID")
        values[key] = int(value)
    return values


def sync(paths: list[Path], apply: bool) -> list[CoverageLink]:
    load_dotenv(PROJECT_ROOT / ".env")
    links = discover_links(paths)
    if not apply or not links:
        return links
    token = os.environ.get("QASE_API_TOKEN", "")
    project_code = os.environ.get("QASE_PROJECT_CODE", "")
    if not token or not project_code:
        raise RuntimeError("QASE_API_TOKEN and QASE_PROJECT_CODE must be configured")
    client = QaseApiClient(token, project_code)
    field_ids = configured_field_ids()
    for link in links:
        client.update_manual_case_coverage(
            link.qase_case_id,
            field_ids=field_ids,
            automation_type=link.automation_type,
            code_path=link.code_path,
            test_id=link.test_id,
            note="Verified Python test is maintained in this repository.",
        )
    return links


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Test files under tests/ui, tests/api, or tests/e2e")
    parser.add_argument("--apply", action="store_true", help="Write coverage values to Qase")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = [Path(item).resolve() for item in args.paths]
    for path in paths:
        if not path.is_file() or TEST_ROOT not in path.parents:
            raise ValueError(f"Not a test file inside tests/: {path}")
    links = sync(paths, args.apply)
    for link in links:
        print(f"ROMEO-{link.qase_case_id}: {link.automation_type} -> {link.code_path} ({link.test_id})")
    print(f"Qase coverage {'updated' if args.apply else 'preview'}: {len(links)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
