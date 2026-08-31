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
        pytest.skip("DEBUG_OTP_ENABLED=true is required for this UI check")

    auth_page = AuthPage(logged_out_driver)
    auth_page.enter_phone(test_user.phone)
    auth_page.accept_privacy_policy()
    auth_page.request_otp()

    otp_page = OtpPage(logged_out_driver)
    assert otp_page.is_opened(), "OTP screen did not open"
    otp_page.enter_code(otp_page.get_displayed_debug_code())

    PinSetupPage(logged_out_driver).skip_if_opened()
    SystemDialogPage(logged_out_driver).allow_notifications_if_requested()
    UpdateDialog(logged_out_driver).postpone_if_opened()

    home_page = HomePage(logged_out_driver)
    assert home_page.is_opened(), "Home screen did not open after OTP entry"
    return home_page
@pytest.mark.positive
@pytest.mark.requires_debug_otp
@allure.id("KAN-6-1")
@allure.title("Privileges button is visible and enabled on the home screen")
def test_privileges_button_is_visible_and_enabled(logged_out_driver, test_user, settings):
    home_page = _open_home_via_debug_otp(logged_out_driver, test_user, settings)

    with allure.step("Verify that the Privileges button is displayed"):
        assert home_page.is_visible(home_page.privileges_tab), (
            "Privileges button is not displayed on the home screen"
        )

    with allure.step("Verify that the Privileges button is enabled"):
        assert home_page.is_enabled(home_page.privileges_tab), (
            "Privileges button is disabled on the home screen"
        )
