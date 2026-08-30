@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python environment was not found: .venv\Scripts\python.exe
    echo Create or restore the project virtual environment before running tests.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] Configuration file .env was not found.
    echo Copy .env.example to .env and set Appium, backend, and test-user variables.
    pause
    exit /b 1
)

echo Running end-to-end tests...
".venv\Scripts\python.exe" -m pytest tests\e2e -m e2e
set "TEST_EXIT_CODE=%ERRORLEVEL%"

echo.
echo End-to-end tests finished with exit code %TEST_EXIT_CODE%.
pause
exit /b %TEST_EXIT_CODE%
