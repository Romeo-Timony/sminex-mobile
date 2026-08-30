@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0\..\.."

set "AGENT_CONFIG=.n8n-agent.env"
if exist "%AGENT_CONFIG%" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%AGENT_CONFIG%") do set "%%A=%%B"
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment was not found.
    exit /b 1
)

if "%OPENAI_API_KEY%"=="" (
    echo [ERROR] OPENAI_API_KEY is missing. Add it to .n8n-agent.env.
    exit /b 1
)

if "%N8N_AGENT_TOKEN%"=="" (
    echo [ERROR] N8N_AGENT_TOKEN is missing. Add it to .n8n-agent.env.
    exit /b 1
)

".venv\Scripts\python.exe" "tools\n8n_agent_server.py"
