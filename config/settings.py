from dataclasses import dataclass
from os import getenv
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _required(name: str) -> str:
    value = getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Set {name} in .env or CI variables")
    return value


def _as_bool(name: str, default: bool = False) -> bool:
    return getenv(name, str(default)).strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    appium_server: str
    platform_name: str
    device_name: str
    automation_name: str
    app_mode: str
    app_package: str
    app_activity: str
    app_path: Path | None
    udid: str | None
    explicit_wait_seconds: int
    test_phone: str
    debug_otp_enabled: bool
    backend_mode: str
    wiremock_admin_url: str | None
    app_api_base_url: str | None
    api_base_url: str | None
    otp_request_path: str | None
    otp_request_success_status: int | None
    otp_request_invalid_status: int | None
    mock_otp_request_path: str | None

def get_settings() -> Settings:
    app_mode = getenv("APP_MODE", "installed").strip().lower()
    if app_mode not in {"installed", "apk"}:
        raise RuntimeError("APP_MODE must be either 'installed' or 'apk'")

    backend_mode = getenv("BACKEND_MODE", "live").strip().lower()
    if backend_mode not in {"live", "mock"}:
        raise RuntimeError("BACKEND_MODE must be either 'live' or 'mock'")
    wiremock_admin_url = getenv("WIREMOCK_ADMIN_URL") or None
    app_api_base_url = getenv("APP_API_BASE_URL") or None
    if backend_mode == "mock" and (not wiremock_admin_url or not app_api_base_url):
        raise RuntimeError(
            "BACKEND_MODE=mock requires WIREMOCK_ADMIN_URL and APP_API_BASE_URL"
        )

    app_path: Path | None = None
    if app_mode == "apk":
        app_path = Path(_required("APP_PATH"))
        if not app_path.is_file():
            raise RuntimeError(f"APK does not exist: {app_path}")

    return Settings(
        appium_server=getenv("APPIUM_SERVER", "http://127.0.0.1:4723"),
        platform_name=getenv("PLATFORM_NAME", "Android"),
        device_name=getenv("DEVICE_NAME", "Android Emulator"),
        automation_name=getenv("AUTOMATION_NAME", "UiAutomator2"),
        app_mode=app_mode,
        app_package=getenv("APP_PACKAGE", "com.sminex.sminex_app"),
        app_activity=getenv("APP_ACTIVITY", "com.sminex.sminex_app.MainActivity"),
        app_path=app_path,
        udid=getenv("UDID") or None,
        explicit_wait_seconds=int(getenv("EXPLICIT_WAIT_SECONDS", "20")),
        test_phone=_required("TEST_PHONE"),
        debug_otp_enabled=_as_bool("DEBUG_OTP_ENABLED"),
        backend_mode=backend_mode,
        wiremock_admin_url=wiremock_admin_url,
        app_api_base_url=app_api_base_url,
        api_base_url=getenv("API_BASE_URL") or None,
        otp_request_path=getenv("OTP_REQUEST_PATH") or None,
        otp_request_success_status=(
            int(getenv("OTP_REQUEST_SUCCESS_STATUS"))
            if getenv("OTP_REQUEST_SUCCESS_STATUS")
            else None
        ),
        otp_request_invalid_status=(
            int(getenv("OTP_REQUEST_INVALID_STATUS"))
            if getenv("OTP_REQUEST_INVALID_STATUS")
            else None
        ),
        mock_otp_request_path=getenv("MOCK_OTP_REQUEST_PATH", "/api/v1/auth/send"),
    )
