@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0\..\.."

set "AUTOMATION_LOG_DIR=run\automation"
set "NGROK_DOMAIN=stylish-mary-bluebelled.ngrok-free.dev"
set "NGROK_EXE=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"

if not exist "%AUTOMATION_LOG_DIR%" mkdir "%AUTOMATION_LOG_DIR%"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python environment was not found: .venv\Scripts\python.exe
    exit /b 1
)
if not exist ".n8n-agent.env" (
    echo [ERROR] .n8n-agent.env is missing.
    exit /b 1
)

echo [1/4] Starting n8n containers...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not ready.
    exit /b 1
)
docker inspect -f "{{.State.Running}}" n8n-dev-instance 2>nul | findstr /i /x "true" >nul
if not errorlevel 1 goto n8n_container_ready
docker inspect n8n-dev-instance >nul 2>&1
if not errorlevel 1 (
    docker start n8n-dev-instance >nul
    docker inspect searxng-dev >nul 2>&1
    if not errorlevel 1 docker start searxng-dev >nul
) else (
    docker inspect searxng-dev >nul 2>&1
    if not errorlevel 1 (
        echo [ERROR] Existing searxng-dev prevents a clean n8n compose startup.
        echo         Start n8n-dev-instance once, then run this file again.
        exit /b 1
    )
    docker compose -f docker-compose-n8n.yml up -d
    if errorlevel 1 exit /b 1
)
:n8n_container_ready
call :wait_for_url "http://127.0.0.1:5678/healthz" 60
if errorlevel 1 goto service_failed

echo [2/4] Starting the PyCharm agent when required...
call :url_is_ready "http://127.0.0.1:5000/health"
if not errorlevel 1 goto agent_ready
start "" /b cmd.exe /d /c "run\venv\start_n8n_agent.bat"
call :wait_for_url "http://127.0.0.1:5000/health" 45
if errorlevel 1 goto service_failed
:agent_ready

echo [3/4] Starting the public Jira webhook tunnel when required...
call :url_is_ready "http://127.0.0.1:4040/api/tunnels"
if not errorlevel 1 goto tunnel_ready
if not exist "%NGROK_EXE%" (
    echo [ERROR] ngrok.exe was not found. Install Ngrok.Ngrok with winget first.
    exit /b 1
)
start "" /b "%NGROK_EXE%" http --url=https://%NGROK_DOMAIN% 5678
call :wait_for_url "http://127.0.0.1:4040/api/tunnels" 20
if errorlevel 1 goto service_failed
:tunnel_ready

echo [4/4] Verifying the complete route...
call :wait_for_url "https://%NGROK_DOMAIN%/healthz" 20
if errorlevel 1 goto service_failed

echo.
echo [READY] Jira -^> n8n -^> PyCharm Agent -^> Appium -^> pytest -^> Qase -^> GitHub is enabled.
echo Incoming n8n requests with apply=true now create and start run\automation\KAN-*_auto_pipeline.bat automatically.
echo Logs are saved to run\automation\KAN-*_auto_pipeline.log.
exit /b 0

:wait_for_url
set "CHECK_URL=%~1"
set "CHECK_ATTEMPTS=%~2"
for /L %%I in (1,1,%CHECK_ATTEMPTS%) do (
    call :url_is_ready "%CHECK_URL%"
    if not errorlevel 1 exit /b 0
    timeout /t 1 /nobreak >nul
)
exit /b 1

:url_is_ready
powershell.exe -NoProfile -Command "try { $response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri '%~1'; exit 0 } catch { exit 1 }"
exit /b %ERRORLEVEL%

:service_failed
echo [ERROR] A required service did not become ready. Check Docker, run\automation logs, and the agent console.
exit /b 1
