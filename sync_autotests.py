import os
import sys
import json
import ast
import urllib.request
import urllib.error

# Установка UTF-8 для вывода консоли на Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Конфигурация Qase и N8N
QASE_TOKEN = "0a18fa9527fd31956a9353995bb62ccc94a23e547272b959484224cfda98bce6"
PROJECT_CODE = "ROMEO"
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/qase-sync-autotests"

# Сьюты автоматизации в Qase (Сьют 4 🤖 Автоматизация)
SUITE_MAP = {
    "UI": 5,   # UI Автотесты
    "API": 6,  # API Автотесты
    "E2E": 7   # E2E Автотесты
}

def parse_py_file(filepath):
    """Парсит Python-файл автотеста и извлекает метки, title, тип и шаги allure."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)
    except Exception as e:
        print(f"Ошибка чтения {filepath}: {e}")
        return []

    tests_data = []
    
    # Определение категории по папке
    lower_path = filepath.lower().replace("\\", "/")
    if "/ui/" in lower_path:
        test_type = "UI"
    elif "/api/" in lower_path or "/back/" in lower_path:
        test_type = "API"
    elif "/e2e/" in lower_path:
        test_type = "E2E"
    else:
        test_type = "UI"

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            title = node.name
            jira_key = "KAN-1"
            qase_id = "0"
            steps = []

            # Анализ декораторов (@allure.title, @pytest.mark.qase, etc.)
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    func = decorator.func
                    if isinstance(func, ast.Attribute) and func.attr == "title":
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            title = decorator.args[0].value
                    elif isinstance(func, ast.Attribute) and func.attr == "qase":
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            qase_id = str(decorator.args[0].value)
                    elif isinstance(func, ast.Attribute) and func.attr == "jira":
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            jira_key = str(decorator.args[0].value)

            # Извлечение шагов из with allure.step("..."):
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.With):
                    for item in stmt.items:
                        ctx = item.context_expr
                        if isinstance(ctx, ast.Call) and isinstance(ctx.func, ast.Attribute) and ctx.func.attr == "step":
                            if ctx.args and isinstance(ctx.args[0], ast.Constant):
                                action_text = str(ctx.args[0].value)
                                steps.append({"action": action_text, "expected": "Успешное выполнение шага автотеста"})

            if not steps:
                steps = [{"action": f"Запуск автотеста {node.name}", "expected": "Автотест выполнен без ошибок"}]

            tests_data.append({
                "title": f"[AUTOTEST] [{test_type}] {title}",
                "type": test_type,
                "jira_key": jira_key,
                "qase_id": qase_id,
                "suite_id": SUITE_MAP.get(test_type, 5),
                "automation": 2,
                "steps": steps,
                "filepath": filepath
            })

    return tests_data

def scan_all_autotests(base_dir="tests"):
    """Рекурсивно сканирует все папки с автотестами."""
    all_tests = []
    if not os.path.exists(base_dir):
        print(f"Директория {base_dir} не найдена.")
        return all_tests

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                filepath = os.path.join(root, file)
                tests = parse_py_file(filepath)
                all_tests.extend(tests)

    return all_tests

def send_to_n8n_webhook(autotests, jira_key="KAN-2"):
    """Отправляет выгрузку автотестов на N8N вебхук."""
    payload = {
        "jiraKey": jira_key,
        "autotests": autotests
    }
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(N8N_WEBHOOK_URL, data=data_bytes, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req) as resp:
            res_text = resp.read().decode("utf-8")
            print(f"[N8N Webhook OK] Response ({resp.status}): {res_text}")
            return True
    except Exception as e:
        print(f"[N8N Webhook Warning] ({N8N_WEBHOOK_URL}): {e}")
        return False

def sync_direct_to_qase(autotests):
    """Прямой импорт в Qase TMS через REST API (фоллбек)."""
    qase_cases = []
    for t in autotests:
        qase_cases.append({
            "title": t["title"],
            "suite_id": t["suite_id"],
            "automation": 2,
            "is_flaky": 0,
            "tags": ["autotest", "pytest", "pycharm"],
            "steps": t["steps"]
        })

    req_url = f"https://api.qase.io/v1/case/{PROJECT_CODE}/bulk"
    payload = {"cases": qase_cases}
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(req_url, data=data_bytes, headers={
        "Token": QASE_TOKEN,
        "Content-Type": "application/json; charset=utf-8"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            res_text = resp.read().decode("utf-8")
            print(f"[Qase API Direct OK] Bulk Response ({resp.status}): {res_text}")
            return True
    except Exception as e:
        print(f"[Qase API Direct Error]: {e}")
        return False

def main():
    target_dir = "tests"
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]

    print(f"[SCAN] Сканирование автотестов PyCharm в директории: {target_dir}...")
    autotests = scan_all_autotests(target_dir)
    print(f"[FOUND] Найдено автотестов для экспорта в Qase: {len(autotests)}")

    if not autotests:
        print("Тесты для экспорта не найдены.")
        return

    for t in autotests:
        print(f"  • [{t['type']}] {t['title']} (Suite ID: {t['suite_id']})")

    print("\n[SEND] Отправка автотестов в N8N...")
    success = send_to_n8n_webhook(autotests)
    if not success:
        print("[FALLBACK] Прямая синхронизация с Qase TMS API...")
        sync_direct_to_qase(autotests)

if __name__ == "__main__":
    main()
