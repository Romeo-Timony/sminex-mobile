@echo off
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment was not found: .venv\Scripts\activate.bat
    pause
    exit /b 1
)

echo Opening a command prompt with the project virtual environment activated...
cmd /k call ".venv\Scripts\activate.bat"
