@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python environment was not found: .venv\Scripts\python.exe
    pause
    exit /b 1
)

".venv\Scripts\python.exe" tools\promote_review_tests.py %*
set "PROMOTE_EXIT_CODE=%ERRORLEVEL%"

echo.
echo Promotion finished with exit code %PROMOTE_EXIT_CODE%.
pause
exit /b %PROMOTE_EXIT_CODE%
