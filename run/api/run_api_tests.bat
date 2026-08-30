@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python environment was not found: .venv\Scripts\python.exe
    echo Create or restore the project virtual environment before running tests.
    call :wait
    exit /b 1
)

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop was not found in PATH.
    echo Docker is required to run the local WireMock API tests.
    call :wait
    exit /b 1
)

echo Starting WireMock...
docker compose -f docker-compose.test.yml up -d wiremock
if errorlevel 1 (
    echo [ERROR] WireMock did not start.
    call :wait
    exit /b 1
)

set "BACKEND_MODE=mock"
set "WIREMOCK_ADMIN_URL=http://127.0.0.1:8080"
set "APP_API_BASE_URL=http://127.0.0.1:8080"
set "API_BASE_URL=http://127.0.0.1:8080"
set "OTP_REQUEST_PATH=/api/v1/auth/send"
set "OTP_REQUEST_SUCCESS_STATUS=200"
set "OTP_REQUEST_INVALID_STATUS=400"
set "TEST_PHONE=+79097922999"

echo Running isolated API tests against WireMock...
".venv\Scripts\python.exe" -m pytest tests\api\test_auth_otp_mock_api.py -m api
set "TEST_EXIT_CODE=%ERRORLEVEL%"

echo.
echo API tests finished with exit code %TEST_EXIT_CODE%.
call :wait
exit /b %TEST_EXIT_CODE%

:wait
echo.
echo Press any key to close...
pause >nul
exit /b
