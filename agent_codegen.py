import os
import json
import sys
import ast
import urllib.request
import urllib.error
import subprocess
import socket
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Базовая папка для тестов на ревью
REVIEW_BASE_FOLDER = "tests/review"

# Конфигурация Qase для прямого импорта из PyCharm Agent
QASE_TOKEN = "0a18fa9527fd31956a9353995bb62ccc94a23e547272b959484224cfda98bce6"
PROJECT_CODE = "ROMEO"
QASE_AUTOMATION_SUITES = {
    "UI": 5,   # UI Автотесты в сьюте 🤖 Автоматизация
    "API": 6,  # API Автотесты в сьюте 🤖 Автоматизация
    "E2E": 7   # E2E Автотесты в сьюте 🤖 Автоматизация
}

# Шаблоны кода тестов для генерации с поддержкой привязки к Jira, Qase и маркеру review
TEST_TEMPLATE_UI = """import pytest
import allure

@pytest.mark.review
@pytest.mark.jira("{jira_key}")
@pytest.mark.qase_case("{allure_id}")
@pytest.mark.ui
@allure.epic("UI Автотесты (На ревью)")
@allure.feature("{title}")
@allure.issue("https://romeo-timony.atlassian.net/browse/{jira_key}", "{jira_key}")
@allure.id("{allure_id}")
def test_{func_name}():
    \"\"\"
    [НА РЕВЬЮ]
    Jira Ticket: {jira_key} (https://romeo-timony.atlassian.net/browse/{jira_key})
    Qase Case ID: {allure_id}
    Предусловия: {preconditions}
    \"\"\"
{steps_code}
"""

TEST_TEMPLATE_API = """import pytest
import allure
import requests

@pytest.mark.review
@pytest.mark.jira("{jira_key}")
@pytest.mark.qase_case("{allure_id}")
@pytest.mark.api
@allure.epic("API Автотесты (На ревью)")
@allure.feature("{title}")
@allure.issue("https://romeo-timony.atlassian.net/browse/{jira_key}", "{jira_key}")
@allure.id("{allure_id}")
def test_{func_name}():
    \"\"\"
    [НА РЕВЬЮ]
    Jira Ticket: {jira_key} (https://romeo-timony.atlassian.net/browse/{jira_key})
    Qase Case ID: {allure_id}
    Предусловия: {preconditions}
    \"\"\"
{steps_code}
"""

TEST_TEMPLATE_E2E = """import pytest
import allure

@pytest.mark.review
@pytest.mark.jira("{jira_key}")
@pytest.mark.qase_case("{allure_id}")
@pytest.mark.e2e
@allure.epic("E2E Автотесты (На ревью)")
@allure.feature("{title}")
@allure.issue("https://romeo-timony.atlassian.net/browse/{jira_key}", "{jira_key}")
@allure.id("{allure_id}")
def test_{func_name}():
    \"\"\"
    [НА РЕВЬЮ]
    Jira Ticket: {jira_key} (https://romeo-timony.atlassian.net/browse/{jira_key})
    Qase Case ID: {allure_id}
    Предусловия: {preconditions}
    \"\"\"
{steps_code}
"""

def sanitize_func_name(title):
    trans = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    title = str(title).lower()
    res = []
    for c in title:
        if c.isalnum() or c == ' ':
            res.append(trans.get(c, c))
    name = "".join(res).replace(" ", "_")
    return name[:50]

def parse_step_item(step):
    action = ""
    expected = ""
    if isinstance(step, dict):
        action = step.get("action", "")
        expected = step.get("expected_result", step.get("expected", ""))
    elif isinstance(step, str):
        step_str = step.strip()
        if step_str.startswith("{") and step_str.endswith("}"):
            try:
                obj = json.loads(step_str)
                action = obj.get("action", "")
                expected = obj.get("expected_result", obj.get("expected", ""))
            except Exception:
                try:
                    obj = ast.literal_eval(step_str)
                    action = obj.get("action", "")
                    expected = obj.get("expected_result", obj.get("expected", ""))
                except Exception:
                    action = step_str
        else:
            action = step_str
    
    if not action:
        action = str(step)
    return action, expected

def generate_steps_code(steps):
    code_lines = []
    for step in steps:
        action, expected = parse_step_item(step)
        clean_action = action.replace('"', "'")
        code_lines.append(f'    with allure.step("{clean_action}"):')
        if expected and expected != "Шаг должен быть выполнен успешно.":
            clean_expected = expected.replace('"', "'")
            code_lines.append(f'        # Ожидаемый результат: {clean_expected}')
        code_lines.append('        pass  # TODO: Реализовать логику шага')
    return "\n".join(code_lines)

def update_manifest(manifest_entries):
    manifest_path = os.path.join(REVIEW_BASE_FOLDER, "manifest.json")
    os.makedirs(REVIEW_BASE_FOLDER, exist_ok=True)
    try:
        data = {"last_updated": datetime.now().isoformat(), "generated_tests_on_review": []}
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        data["last_updated"] = datetime.now().isoformat()
        existing = {t["file_path"]: t for t in data.get("generated_tests_on_review", [])}
        for entry in manifest_entries:
            existing[entry["file_path"]] = entry
        data["generated_tests_on_review"] = list(existing.values())
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка обновления реестра манифеста: {e}")

def patch_qase_case_on_promotion(qase_id, tc_type="UI"):
    """Обновляет существующий Qase Case ID: переводит в automation: 2 (Automated) и перемещает в сьют 🤖 Автоматизация (БЕЗ ДУБЛИКАТОВ)."""
    if not qase_id or str(qase_id) == "0":
        return False
    
    clean_id = str(qase_id).split("-")[-1]
    if not clean_id.isdigit():
        return False
        
    suite_id = QASE_AUTOMATION_SUITES.get(tc_type.upper(), 5)
    req_url = f"https://api.qase.io/v1/case/{PROJECT_CODE}/{clean_id}"
    
    payload = {
        "automation": 2,
        "is_flaky": 0,
        "suite_id": suite_id
    }
    
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(req_url, data=data_bytes, headers={
        "Token": QASE_TOKEN,
        "Content-Type": "application/json; charset=utf-8"
    }, method="PATCH")
    
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Qase Case #{clean_id} успешно обновлен до Automated в сьюте {suite_id} (HTTP {resp.status})")
            return True
    except Exception as e:
        print(f"⚠️ Ошибка PATCH обновления Qase Case #{clean_id}: {e}")
        return False

def sync_generated_autotests_to_qase(test_cases, jira_key="KAN-1"):
    """Регистрирует / обновляет существующие ручные кейсы Qase до статуса Automated без создания дубликатов."""
    print(f"🚀 Синхронизация {len(test_cases)} автотестов с Qase TMS (Раздел '🤖 Автоматизация')...")
    updated_ids = []
    
    for index, tc in enumerate(test_cases):
        tc_type = tc.get("type", "UI").upper()
        qase_id = str(tc.get("id", f"{jira_key}-{index+1}"))
        
        # Обновление существующего кейса без создания дубликатов
        success = patch_qase_case_on_promotion(qase_id, tc_type=tc_type)
        if success:
            updated_ids.append(qase_id)

    return True, {"updated_ids": updated_ids}

def generate_tests(test_cases, jira_key="KAN-1", apply=True):
    if not apply:
        print(f"Dry run (apply=False): Пропущена генерация файлов для {jira_key}.")
        return {"status": "dry_run", "message": f"Dry run complete for {jira_key}. Set apply=true to create files."}

    print(f"Начало генерации автотестов на ревью для задачи {jira_key} (apply=True)...")
    
    folders = {
        "UI": os.path.join(REVIEW_BASE_FOLDER, jira_key, "ui"),
        "API": os.path.join(REVIEW_BASE_FOLDER, jira_key, "back"),
        "E2E": os.path.join(REVIEW_BASE_FOLDER, jira_key, "e2e")
    }

    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "__init__.py"), "w") as f:
            pass

    manifest_entries = []

    for tc in test_cases:
        tc_type = tc.get("type", "UI").upper()
        folder = folders.get(tc_type)
        if not folder:
            tc_type = "UI"
            folder = folders["UI"]

        func_name = sanitize_func_name(tc.get("title", "test"))
        steps_code = generate_steps_code(tc.get("steps", []))
        allure_id = str(tc.get("id", "0"))
        
        if tc_type == "UI":
            template = TEST_TEMPLATE_UI
            filename = f"test_ui_{func_name}.py"
        elif tc_type == "API":
            template = TEST_TEMPLATE_API
            filename = f"test_api_{func_name}.py"
        else:
            template = TEST_TEMPLATE_E2E
            filename = f"test_e2e_{func_name}.py"

        content = template.format(
            title=tc.get("title", ""),
            allure_id=allure_id,
            jira_key=jira_key,
            preconditions=tc.get("preconditions", "Не указаны"),
            func_name=func_name,
            steps_code=steps_code
        )

        filepath = os.path.join(folder, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Сгенерирован файл теста на ревью: {filepath}")

        manifest_entries.append({
            "jira_key": jira_key,
            "qase_id": allure_id,
            "type": tc_type,
            "title": tc.get("title", ""),
            "file_path": filepath,
            "function_name": f"test_{func_name}",
            "status": "pending_review"
        })

    update_manifest(manifest_entries)
    print("Генерация автотестов на ревью завершена.")

    # В соответствии со сценарием, исходный кейс Qase остается в статусе Manual на этапе генерации.
    # Обновление полей автоматизации происходит только после успешной проверки и переноса (promotion).
    
    return {
        "status": "success",
        "message": f"Generated {len(test_cases)} tests for review under tests/review/{jira_key}/. Qase cases remain Manual.",
        "jira_key": jira_key,
        "qase_autotests_synced": False,
        "qase_automation_suite": "https://app.qase.io/ai-test-generator/ROMEO/autotest",
        "review_folder": f"tests/review/{jira_key}"
    }

# HTTP обработчик для вебхука из N8N
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/agent/trigger-codegen':
            # Проверка токена авторизации Bearer
            auth_header = self.headers.get("Authorization", "")
            n8n_agent_token = os.getenv("N8N_AGENT_TOKEN", "n8n_agent_secret_token")
            expected_auth = f"Bearer {n8n_agent_token}"
            if auth_header != expected_auth:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"status": "error", "message": "Unauthorized: Invalid or missing N8N token"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                test_cases = data.get("testCases", [])
                jira_key = data.get("jiraKey", data.get("jira_key", data.get("jira_issue_key", "KAN-1")))
                apply_flag = data.get("apply", True) # Default to True for automated pipeline
                
                result = generate_tests(test_cases, jira_key=jira_key, apply=apply_flag)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"Сервер агента успешно запущен на порту {port}. Ожидание вебхуков...")
    print(f"Эндпоинт для N8N: http://localhost:{port}/agent/trigger-codegen")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")

def start_appium_if_needed():
    port = 4723
    # Проверка, открыт ли уже порт Appium
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', port)) == 0:
            print(f"[APPIUM] Appium-сервер уже запущен на порту {port}.")
            return

    cmd = ["appium.cmd"] if sys.platform == "win32" else ["appium"]
    print(f"[APPIUM] Запуск Appium на порту {port}...")
    try:
        # Запускаем в фоне
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=(sys.platform == "win32"))
        # Ожидаем доступности порта
        for _ in range(15):
            time.sleep(1)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                if s2.connect_ex(('127.0.0.1', port)) == 0:
                    print("[APPIUM] Appium-сервер успешно запущен!")
                    return
        print("[APPIUM] Предупреждение: Процесс Appium запущен, но порт не отвечает.")
    except Exception as e:
        print(f"[APPIUM] Ошибка запуска Appium: {e}")

def main():
    # Запускаем Appium для Android UI/E2E-проверок
    start_appium_if_needed()

    port = 5000
    if len(sys.argv) > 2 and sys.argv[1] == "--port":
        port = int(sys.argv[2])
    run_server(port)

if __name__ == '__main__':
    main()
