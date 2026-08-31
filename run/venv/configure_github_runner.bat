@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion

set "RUNNER_DIR=C:\actions-runner"
set "REPOSITORY_URL=https://github.com/Romeo-Timony/sminex-mobile"
set "RUNNER_NAME=autotest-mobile-windows"

if not exist "%RUNNER_DIR%\config.cmd" (
    echo [ERROR] GitHub Actions runner is not installed in %RUNNER_DIR%.
    exit /b 1
)

set "RUNNER_TOKEN=%~1"
if "%RUNNER_TOKEN%"=="" set /p "RUNNER_TOKEN=Paste the one-time GitHub runner token: "
if "%RUNNER_TOKEN%"=="" (
    echo [ERROR] The registration token is required.
    exit /b 1
)

pushd "%RUNNER_DIR%"
call config.cmd --unattended --replace --url "%REPOSITORY_URL%" --token "%RUNNER_TOKEN%" --name "%RUNNER_NAME%" --labels "self-hosted,windows,autotest-mobile" --work "_work"
if errorlevel 1 (
    popd
    exit /b 1
)

popd

echo [READY] Local GitHub Actions runner is registered.
echo Start it manually when needed: C:\actions-runner\run.cmd
exit /b 0
