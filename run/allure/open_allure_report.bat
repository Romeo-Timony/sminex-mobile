@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\..\.."

if not exist "allure-results" (
    echo [ERROR] Directory allure-results was not found.
    echo Run tests first to create Allure results.
    call :wait
    exit /b 1
)

dir /b "allure-results\*.json" "allure-results\*.xml" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No Allure result files were found in allure-results.
    echo Run tests first, then start this file again.
    call :wait
    exit /b 1
)

set "ALLURE_COMMAND=allure"
set "ALLURE_FOUND="
where allure >nul 2>&1
if not errorlevel 1 set "ALLURE_FOUND=1"
if not defined ALLURE_FOUND (
    for /d %%p in ("%LOCALAPPDATA%\JetBrains\PyCharm*") do (
        for /d %%n in ("%%~fp\acp-agents\.runtimes\node\*") do (
            if exist "%%~fn\allure.cmd" (
                set "ALLURE_COMMAND=%%~fn\allure.cmd"
                set "ALLURE_FOUND=1"
            )
        )
    )
)
if not defined ALLURE_FOUND (
    for /f "usebackq delims=" %%i in (`npm.cmd prefix -g 2^>nul`) do set "NPM_PREFIX=%%i"
    if defined NPM_PREFIX if exist "%NPM_PREFIX%\allure.cmd" (
        set "ALLURE_COMMAND=%NPM_PREFIX%\allure.cmd"
        set "ALLURE_FOUND=1"
    )
)

if not defined ALLURE_FOUND (
    echo [ERROR] Allure CLI was not found.
    echo Install it with: npm install -g allure
    call :wait
    exit /b 1
)

echo Generating Allure report from allure-results...
call "%ALLURE_COMMAND%" generate allure-results --output allure-report --open
set "REPORT_EXIT_CODE=%ERRORLEVEL%"

echo.
echo Allure finished with exit code %REPORT_EXIT_CODE%.
call :wait
exit /b %REPORT_EXIT_CODE%

:wait
echo.
echo Press any key to close...
pause >nul
exit /b
