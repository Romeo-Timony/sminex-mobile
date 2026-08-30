# Быстрый запуск тестов

Перед запуском создайте `.env` на основе `.env.example` и укажите переменные
соответствующего контура. Appium и, для изолированных UI-сценариев, WireMock
должны быть запущены заранее.

- `api/run_api_tests.bat` — изолированные API-тесты на WireMock; `.env` не требуется.
- `ui/run_ui_tests.bat` — UI-тесты через Appium.
- `e2e/run_e2e_tests.bat` — end-to-end сценарии через Appium и тестовый backend.
- `dev/run_debug_apk_ui_tests.bat` — установка `app-dev-debug.apk` и видимый запуск UI-тестов на запущенном Android Studio эмуляторе.
- `venv/open_venv_console.bat` — отдельная командная строка с активированным `.venv`.
- `allure/open_allure_report.bat` — генерация `allure-report` из `allure-results` и открытие отчёта в браузере.

BAT-файлы сохраняют код завершения pytest и не закрывают окно консоли, чтобы
результат запуска был виден при запуске двойным кликом.

Для просмотра отчёта используется установленный Allure CLI. Тесты уже
складывают результаты в `allure-results`.

Dev-запускатор требует запущенный Android Studio эмулятор, Android SDK Platform
Tools и Appium. Он устанавливает debug APK, при необходимости запускает Appium
в отдельном окне и выполняет UI-сценарии, совместимые с dev backend. Сценарии
`ui_mock` запускаются отдельно только на APK, подтверждённо направляющей трафик
в WireMock.
