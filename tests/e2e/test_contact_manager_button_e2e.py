import allure
import pytest

from pages.auth_page import AuthPage
from pages.home_page import HomePage
from pages.otp_page import OtpPage
from pages.pin_setup_page import PinSetupPage
from pages.system_dialog_page import SystemDialogPage
from pages.update_dialog import UpdateDialog


def _open_home_via_debug_otp(logged_out_driver, test_user, settings) -> HomePage:
    if not settings.debug_otp_enabled:
        pytest.skip("DEBUG_OTP_ENABLED=true is required for this E2E check")

    auth_page = AuthPage(logged_out_driver)
    auth_page.enter_phone(test_user.phone)
    auth_page.accept_privacy_policy()
    auth_page.request_otp()

    otp_page = OtpPage(logged_out_driver)
    assert otp_page.is_opened(), "OTP screen did not open"
    with allure.step("Authenticate with the debug OTP displayed by the app"):
        otp_page.enter_code(otp_page.get_displayed_debug_code())

    PinSetupPage(logged_out_driver).skip_if_opened()
    SystemDialogPage(logged_out_driver).allow_notifications_if_requested()
    UpdateDialog(logged_out_driver).postpone_if_opened()

    home_page = HomePage(logged_out_driver)
    assert home_page.is_opened(), "Home screen did not open after OTP entry"
    return home_page
@pytest.mark.e2e
@pytest.mark.positive
@pytest.mark.requires_debug_otp
@allure.id("KAN-2-12")
@allure.title("[KAN-2-12] User sees the contact-manager action on Home")
def test_user_sees_contact_manager_button_on_home(
    logged_out_driver, test_user, settings
):
    home_page = _open_home_via_debug_otp(logged_out_driver, test_user, settings)
    assert home_page.is_contact_manager_available(), (
        "Contact-manager action is not visible on Home"
    )
