@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\..\.."

set "APK_PATH=%CD%\app-dev-debug.apk"
set "APPIUM_PORT=4723"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python environment was not found: .venv\Scripts\python.exe
    call :wait
    exit /b 1
)

if not exist "%APK_PATH%" (
    echo [ERROR] Debug APK was not found: %APK_PATH%
    call :wait
    exit /b 1
)

where adb >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Android SDK platform-tools ^(adb^) was not found in PATH.
    call :wait
    exit /b 1
)

for /f "tokens=1" %%i in ('adb devices ^| findstr /r "device$"') do (
    if not defined UDID set "UDID=%%i"
)
if not defined UDID (
    echo [ERROR] No running Android emulator or device was found.
    echo Start an Android Studio emulator, then run this file again.
    call :wait
    exit /b 1
)

where appium.cmd >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Appium was not found in PATH.
    echo Install Appium, then run this file again.
    call :wait
    exit /b 1
)

netstat -ano | findstr /r /c:":%APPIUM_PORT% .*LISTENING" >nul
if errorlevel 1 (
    echo Starting Appium in a separate minimized window...
    start "Appium server" /min cmd /k appium.cmd --address 127.0.0.1 --port %APPIUM_PORT%
)

for /l %%i in (1,1,15) do (
    netstat -ano | findstr /r /c:":%APPIUM_PORT% .*LISTENING" >nul && goto appium_ready
    timeout /t 1 /nobreak >nul
)
echo [ERROR] Appium did not start on port %APPIUM_PORT%.
call :wait
exit /b 1

:appium_ready
echo Installing debug APK on %UDID%...
adb -s "%UDID%" install -r "%APK_PATH%"
if not errorlevel 1 goto apk_ready

echo Existing application has an incompatible signature.
echo Removing only com.sminex.sminex_app from %UDID% and installing the debug APK again...
adb -s "%UDID%" uninstall com.sminex.sminex_app
if errorlevel 1 (
    echo [ERROR] Could not remove the incompatible application.
    call :wait
    exit /b 1
)

adb -s "%UDID%" install "%APK_PATH%"
if errorlevel 1 (
    echo [ERROR] APK installation failed after removing the incompatible build.
    call :wait
    exit /b 1
)

:apk_ready

set "APPIUM_SERVER=http://127.0.0.1:%APPIUM_PORT%"
set "UDID=%UDID%"
set "APP_MODE=installed"
set "APP_PACKAGE=com.sminex.sminex_app"
set "APP_ACTIVITY=com.sminex.sminex_app.MainActivity"
set "BACKEND_MODE=live"
set "TEST_PHONE=+79097922999"
set "DEBUG_OTP_ENABLED=true"

echo.
echo Running visible UI debug tests on the Android Studio emulator %UDID%...
".venv\Scripts\python.exe" -m pytest tests\ui -m "ui and not ui_mock"
set "TEST_EXIT_CODE=%ERRORLEVEL%"

echo.
echo Debug APK UI tests finished with exit code %TEST_EXIT_CODE%.
call :wait
exit /b %TEST_EXIT_CODE%

:wait
echo.
echo Press any key to close...
pause >nul
exit /b
