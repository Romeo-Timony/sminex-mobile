import os
import sys
import json
import argparse
import subprocess
import socket
import time
import urllib.request
from datetime import datetime

# UTF-8 for console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

QASE_TOKEN = os.getenv("QASE_API_TOKEN", "0a18fa9527fd31956a9353995bb62ccc94a23e547272b959484224cfda98bce6")
PROJECT_CODE = os.getenv("QASE_PROJECT_CODE", "ROMEO")

REVIEW_MANIFEST = "tests/review/manifest.json"
MAIN_MANIFEST = "tests/manifest.json"

def is_appium_running(port=4723):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_appium_if_needed():
    port = 4723
    if is_appium_running(port):
        print(f"[APPIUM] Appium-сервер уже запущен на порту {port}.")
        return True

    cmd = ["appium.cmd"] if sys.platform == "win32" else ["appium"]
    print(f"[APPIUM] Запуск Appium на порту {port}...")
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=(sys.platform == "win32"))
        for _ in range(15):
            time.sleep(1)
            if is_appium_running(port):
                print("[APPIUM] Appium-сервер успешно запущен!")
                return True
        print("[APPIUM] Предупреждение: Процесс Appium запущен, но порт не отвечает.")
        return False
    except Exception as e:
        print(f"[APPIUM] Ошибка запуска Appium: {e}")
        return False

def run_verification(file_path):
    print(f"🔍 Запуск pytest верификации для файла: {file_path}")
    # Используем sys.executable для запуска pytest из текущего окружения
    cmd = [sys.executable, "-m", "pytest", file_path, "-v"]
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Ошибка вызова pytest: {e}")
        return False

def patch_qase_custom_fields(qase_id, test_type, relative_test_path):
    """Обновляет кастомные поля существующего кейса в Qase, не трогая системное поле Automation Status (остается Manual)."""
    if not qase_id or str(qase_id) == "0":
        print(f"⚠️ Пропуск обновления Qase: Некорректный Case ID ({qase_id})")
        return False
    
    # Qase ID может быть в формате KAN-4-1162, извлекаем только числовой ID (1162)
    clean_id = str(qase_id).split("-")[-1]
    if not clean_id.isdigit():
        print(f"⚠️ Пропуск обновления Qase: Невозможно распарсить числовой ID из '{qase_id}'")
        return False
        
    req_url = f"https://api.qase.io/v1/case/{PROJECT_CODE}/{clean_id}"
    
    # Карта кастомных полей:
    # 1: Automation Coverage -> Automated
    # 2: Automation Type -> UI / API / E2E
    # 3: Automation Code Path -> путь к Python-тесту
    # 4: Automation Test ID -> Allure ID (тот же qaseCaseId)
    # 5: Automation Note -> отметка о проверенном тесте
    payload = {
        "custom_field": {
            "1": "Automated",
            "2": test_type.upper(),
            "3": relative_test_path.replace("\\", "/"),
            "4": clean_id,
            "5": f"Автотест успешно проверен и перенесен. Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    }
    
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(req_url, data=data_bytes, headers={
        "Token": QASE_TOKEN,
        "Content-Type": "application/json; charset=utf-8"
    }, method="PATCH")
    
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Qase Case #{clean_id} кастомные поля успешно обновлены (HTTP {resp.status})")
            return True
    except Exception as e:
        print(f"⚠️ Ошибка PATCH обновления Qase Case #{clean_id}: {e}")
        return False

def strip_review_decorator(content):
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if line.strip() == "@pytest.mark.review":
            continue
        # Убираем пометку " (На ревью)" из Allure epic
        if 'allure.epic("' in line and '(На ревью)' in line:
            line = line.replace(" (На ревью)", "")
        new_lines.append(line)
    return "\n".join(new_lines) + "\n"

def clean_empty_directories(path):
    if not os.path.exists(path):
        return
    for root, dirs, files in os.walk(path, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            # Если папка пустая или содержит только пустые подпапки / __init__.py без других файлов
            inner_files = [f for f in os.listdir(dir_path) if f != "__init__.py"]
            if not inner_files:
                # Удаляем __init__.py если есть, и саму папку
                init_file = os.path.join(dir_path, "__init__.py")
                if os.path.exists(init_file):
                    try:
                        os.remove(init_file)
                    except Exception:
                        pass
                try:
                    os.rmdir(dir_path)
                    print(f"🗑️ Удалена пустая папка: {dir_path}")
                except Exception as e:
                    print(f"Не удалось удалить папку {dir_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Скрипт верификации и промоушна автотестов из review")
    parser.add_argument("--verify", action="store_true", help="Запустить pytest-верификацию перед переносом")
    parser.add_argument("--apply", action="store_true", help="Применить перенос файлов и обновить Qase")
    parser.add_argument("--jira-key", type=str, help="Фильтровать тесты по конкретному Jira Issue Key (например, KAN-4)")
    args = parser.parse_args()

    if not args.verify and not args.apply:
        print("❌ Укажите хотя бы один параметр: --verify, --apply или оба.")
        sys.exit(1)

    if not os.path.exists(REVIEW_MANIFEST):
        print(f"❌ Манифест ревью не найден: {REVIEW_MANIFEST}")
        sys.exit(1)

    with open(REVIEW_MANIFEST, "r", encoding="utf-8") as f:
        review_data = json.load(f)

    tests_on_review = review_data.get("generated_tests_on_review", [])
    pending_tests = [t for t in tests_on_review if t.get("status") == "pending_review"]

    if args.jira_key:
        pending_tests = [t for t in pending_tests if t.get("jira_key") == args.jira_key]

    if not pending_tests:
        print("🔔 Нет тестов в статусе pending_review для обработки.")
        sys.exit(0)

    print(f"📋 Найдено тестов для обработки: {len(pending_tests)}")

    # 1. Верификация
    if args.verify:
        has_ui_or_e2e = any(t.get("type", "UI").upper() in ["UI", "E2E"] for t in pending_tests)
        if has_ui_or_e2e:
            start_appium_if_needed()

        failed_tests = []
        for t in pending_tests:
            file_path = t["file_path"]
            if not os.path.exists(file_path):
                print(f"⚠️ Файл не найден: {file_path}")
                failed_tests.append(t)
                continue
            if not run_verification(file_path):
                print(f"❌ Тест провалил верификацию: {file_path}")
                failed_tests.append(t)
            else:
                print(f"✅ Тест успешно прошел верификацию: {file_path}")

        if failed_tests:
            print(f"❌ Верификация провалена для {len(failed_tests)} тестов. Перенос отменен.")
            sys.exit(1)
        print("🌟 Все тесты успешно прошли верификацию!")

    # 2. Перенос (Apply)
    if args.apply:
        print("🚀 Начинаем перенос тестов...")
        
        # Загружаем главный манифест
        main_data = {"last_updated": datetime.now().isoformat(), "generated_tests": []}
        if os.path.exists(MAIN_MANIFEST):
            try:
                with open(MAIN_MANIFEST, "r", encoding="utf-8") as f:
                    main_data = json.load(f)
            except Exception:
                pass

        promoted_count = 0
        for t in pending_tests:
            src_path = t["file_path"]
            if not os.path.exists(src_path):
                print(f"⚠️ Пропуск переноса: Файл не найден {src_path}")
                continue

            tc_type = t.get("type", "UI").upper()
            dest_dir = "tests/ui"
            if tc_type == "API":
                dest_dir = "tests/api"
            elif tc_type == "E2E":
                dest_dir = "tests/e2e"

            os.makedirs(dest_dir, exist_ok=True)
            filename = os.path.basename(src_path)
            dest_path = os.path.join(dest_dir, filename).replace("\\", "/")

            # Читаем исходный код и очищаем от review декоратора
            with open(src_path, "r", encoding="utf-8") as f:
                content = f.read()

            clean_content = strip_review_decorator(content)

            # Записываем в новое место
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(clean_content)

            # Удаляем старый файл
            try:
                os.remove(src_path)
            except Exception as e:
                print(f"⚠️ Не удалось удалить старый файл {src_path}: {e}")

            # Обновляем статус в манифесте ревью
            t["status"] = "promoted"
            t["file_path"] = dest_path

            # Добавляем в главный манифест (избегая дублирования по qase_id/file_path)
            main_tests = main_data.get("generated_tests", [])
            # Удаляем старые записи с таким же путем
            main_tests = [mt for mt in main_tests if mt.get("file_path") != dest_path]
            main_tests.append({
                "jira_key": t.get("jira_key"),
                "qase_id": t.get("qase_id"),
                "type": t.get("type"),
                "title": t.get("title"),
                "file_path": dest_path,
                "function_name": t.get("function_name")
            })
            main_data["generated_tests"] = main_tests

            # Обновляем Qase кастомные поля
            patch_qase_custom_fields(t.get("qase_id"), tc_type, dest_path)
            promoted_count += 1

        # Сохраняем обновленные манифесты
        review_data["last_updated"] = datetime.now().isoformat()
        with open(REVIEW_MANIFEST, "w", encoding="utf-8") as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)

        main_data["last_updated"] = datetime.now().isoformat()
        with open(MAIN_MANIFEST, "w", encoding="utf-8") as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)

        # Очищаем пустые папки в tests/review
        clean_empty_directories("tests/review")

        print(f"🎉 Промоушн завершен! Успешно перенесено тестов: {promoted_count}")

if __name__ == "__main__":
    main()
