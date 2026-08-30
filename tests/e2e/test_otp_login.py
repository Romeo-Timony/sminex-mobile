import pytest
import allure

from pages.auth_page import AuthPage
from pages.home_page import HomePage
from pages.otp_page import OtpPage
from pages.pin_setup_page import PinSetupPage
from pages.system_dialog_page import SystemDialogPage
from pages.update_dialog import UpdateDialog
from mocks.auth_mappings import (
    MOCK_OTP_CODE,
    authenticated_bootstrap_mappings,
    phone_login_mappings,
    unauthenticated_bootstrap_mappings,
)


@pytest.fixture()
def mock_auth_ready(wiremock, settings):
    """Register all public and auth stubs before Android starts the app."""
    for mapping in [
        *unauthenticated_bootstrap_mappings(),
        *phone_login_mappings(settings.mock_otp_request_path),
        *authenticated_bootstrap_mappings(),
    ]:
        wiremock.register_mapping(mapping)
    return wiremock


@pytest.fixture()
def mock_logged_out_driver(mock_auth_ready, logged_out_driver):
    """Start the mock APK only after WireMock contracts are ready."""
    return logged_out_driver


@pytest.mark.e2e
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.requires_debug_otp
@allure.epic("Авторизация")
@allure.feature("Вход по OTP")
@allure.story("Вход по номеру телефона")
@allure.id("E2E-AUTH-001")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("[E2E-AUTH-001] Вход по телефону — ввод полученного OTP — открывается главный экран")
def test_otp_login_opens_home_screen(logged_out_driver, test_user, settings):
    """A user receives the displayed OTP, enters it, and reaches the home screen."""
    if not settings.debug_otp_enabled:
        pytest.skip("DEBUG_OTP_ENABLED=true is required for the debug OTP E2E test")

    auth_page = AuthPage(logged_out_driver)
    auth_page.enter_phone(test_user.phone)
    auth_page.accept_privacy_policy()

    auth_page.request_otp()
    otp_page = OtpPage(logged_out_driver)
    assert otp_page.is_opened(), "OTP screen did not open"

    with allure.step("Enter OTP displayed by the debug build"):
        otp_page.enter_code(otp_page.get_displayed_debug_code())

    PinSetupPage(logged_out_driver).skip_if_opened()
    SystemDialogPage(logged_out_driver).allow_notifications_if_requested()
    UpdateDialog(logged_out_driver).postpone_if_opened()
    assert HomePage(logged_out_driver).is_opened(), "Home screen did not open after OTP entry"


@pytest.mark.e2e
@pytest.mark.ui_mock
@pytest.mark.critical
@pytest.mark.requires_debug_otp
@allure.epic("Авторизация")
@allure.feature("Вход по OTP")
@allure.story("Вход по номеру телефона с моковым OTP")
@allure.id("E2E-AUTH-002")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("[E2E-AUTH-002] Вход по телефону — ввод мокового OTP 1111 — открывается главный экран")
def test_otp_login_with_mocked_code_1111(
    mock_logged_out_driver, test_user, settings
):
    """A mock build renders and accepts deterministic OTP ``1111``."""
    if not settings.debug_otp_enabled:
        pytest.skip("DEBUG_OTP_ENABLED=true is required for the debug OTP UI test")
    auth_page = AuthPage(mock_logged_out_driver)
    auth_page.enter_phone(test_user.phone)
    auth_page.accept_privacy_policy()
    auth_page.request_otp()

    otp_page = OtpPage(mock_logged_out_driver)
    assert otp_page.is_opened(), "OTP screen did not open from the mock response"
    assert otp_page.get_displayed_debug_code() == MOCK_OTP_CODE

    with allure.step("Enter mocked OTP"):
        otp_page.enter_code(MOCK_OTP_CODE)

    PinSetupPage(mock_logged_out_driver).skip_if_opened()
    SystemDialogPage(mock_logged_out_driver).allow_notifications_if_requested()
    UpdateDialog(mock_logged_out_driver).postpone_if_opened()
    assert HomePage(mock_logged_out_driver).is_opened(), "Home screen did not open after OTP 1111"
