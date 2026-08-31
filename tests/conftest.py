import base64
import os
import shutil
import subprocess
import time
from urllib.error import URLError
from urllib.request import urlopen

import allure
import pytest
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from clients.auth_api_client import AuthApiClient
from clients.wiremock_admin_client import WireMockAdminClient
from config.settings import Settings, get_settings
from config.test_data import TestUser, get_test_user
from pages.auth_page import AuthPage


AUTH_PHONE_INPUT = (AppiumBy.XPATH, "//*[@resource-id='auth_screen_phone_email_input']")
ANDROID_COMPATIBILITY_WARNING_OK = (AppiumBy.ID, "android:id/button1")


def _appium_is_ready(server_url: str) -> bool:
    try:
        with urlopen(f"{server_url.rstrip('/')}/status", timeout=2) as response:
            return response.status == 200
    except (URLError, TimeoutError):
        return False


def _ensure_appium(server_url: str) -> None:
    """Start a local Appium server when a UI test is run without one."""
    if _appium_is_ready(server_url):
        return

    appium_command = os.getenv("APPIUM_COMMAND")
    if appium_command:
        command = appium_command.split()
    else:
        appium = shutil.which("appium.cmd") or shutil.which("appium")
        command = [appium] if appium else ["npx.cmd", "appium"]

    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError as exc:
        raise RuntimeError(f"Unable to start Appium with {command!r}: {exc}") from exc

    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if _appium_is_ready(server_url):
            return
        time.sleep(1)

    raise RuntimeError(f"Appium did not become ready at {server_url} within 30 seconds")


def _attach_failure_artifacts(driver) -> None:
    """Attach diagnostic artifacts without masking the original test failure."""
    try:
        allure.attach(
            driver.get_screenshot_as_png(),
            name="Screenshot on failure",
            attachment_type=allure.attachment_type.PNG,
        )
    except WebDriverException:
        pass

    try:
        allure.attach(
            driver.page_source,
            name="Page source on failure",
            attachment_type=allure.attachment_type.XML,
        )
    except WebDriverException:
        pass

    if getattr(driver, "_failure_video_attached", False):
        return
    try:
        video = driver.stop_recording_screen()
        driver._failure_video_attached = True
        if video:
            allure.attach(
                base64.b64decode(video),
                name="Screen recording on failure",
                attachment_type=allure.attachment_type.MP4,
            )
    except (ValueError, WebDriverException):
        pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed and (active_driver := item.funcargs.get("driver")):
        _attach_failure_artifacts(active_driver)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def test_user(settings: Settings) -> TestUser:
    return get_test_user(settings)


@pytest.fixture(scope="session")
def driver(settings: Settings):
    """One Appium session per test run; state is reset by child fixtures."""
    _ensure_appium(settings.appium_server)
    options = UiAutomator2Options()
    options.platform_name = settings.platform_name
    options.device_name = settings.device_name
    options.automation_name = settings.automation_name
    options.app_package = settings.app_package
    options.app_activity = settings.app_activity
    options.new_command_timeout = 120
    options.set_capability("appium:uiautomator2ServerLaunchTimeout", 90000)
    options.no_reset = True
    if settings.app_mode == "apk":
        options.app = str(settings.app_path)
    if settings.udid:
        options.udid = settings.udid

    session = webdriver.Remote(settings.appium_server, options=options)
    try:
        yield session
    finally:
        session.quit()


@pytest.fixture()
def test_recording(driver):
    """Create an individual failure video while keeping the Appium session alive."""
    driver._failure_video_attached = False
    try:
        driver.start_recording_screen()
    except WebDriverException:
        pass

    yield

    if not getattr(driver, "_failure_video_attached", False):
        try:
            driver.stop_recording_screen()
        except WebDriverException:
            pass


def _open_logged_out_application(driver, settings: Settings) -> None:
    driver.execute_script("mobile: clearApp", {"appId": settings.app_package})
    driver.activate_app(settings.app_package)
    try:
        WebDriverWait(driver, 10).until(
            lambda current: current.find_element(*ANDROID_COMPATIBILITY_WARNING_OK)
        ).click()
    except TimeoutException:
        pass

    driver.activate_app(settings.app_package)
    WebDriverWait(driver, settings.explicit_wait_seconds).until(
        lambda current: current.find_element(*AUTH_PHONE_INPUT)
    )


@pytest.fixture()
def logged_out_driver(driver, settings: Settings, test_recording):
    """Clean application data before stateful UI and E2E scenarios."""
    _open_logged_out_application(driver, settings)
    return driver


@pytest.fixture()
def auth_form_driver(driver, settings: Settings, test_recording):
    """Reset only the authorization form when the app is already on that screen."""
    auth_page = AuthPage(driver)
    if not auth_page.is_opened():
        _open_logged_out_application(driver, settings)
        auth_page = AuthPage(driver)

    auth_page.reset_form()
    return driver


@pytest.fixture()
def auth_api_client(settings: Settings) -> AuthApiClient:
    if not settings.api_base_url or not settings.otp_request_path:
        pytest.skip("Set API_BASE_URL and OTP_REQUEST_PATH for API tests")
    return AuthApiClient(settings.api_base_url, settings.otp_request_path)


@pytest.fixture(scope="session")
def wiremock_admin_client(settings: Settings) -> WireMockAdminClient:
    if settings.backend_mode != "mock" or not settings.wiremock_admin_url:
        pytest.skip("Set BACKEND_MODE=mock and WIREMOCK_ADMIN_URL for mock UI tests")
    client = WireMockAdminClient(settings.wiremock_admin_url)
    client.healthcheck()
    return client


@pytest.fixture()
def wiremock(wiremock_admin_client: WireMockAdminClient):
    """Provide a clean mock server state to every UI mock scenario."""
    wiremock_admin_client.reset()
    yield wiremock_admin_client
    wiremock_admin_client.reset()


@pytest.fixture()
def otp_api_contract(settings: Settings) -> tuple[int, int]:
    if (
        settings.otp_request_success_status is None
        or settings.otp_request_invalid_status is None
    ):
        pytest.skip(
            "Set OTP_REQUEST_SUCCESS_STATUS and OTP_REQUEST_INVALID_STATUS for API tests"
        )
    return settings.otp_request_success_status, settings.otp_request_invalid_status
