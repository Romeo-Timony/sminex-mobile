import allure
import pytest

from pages.auth_page import AuthPage
from pages.home_page import HomePage
from pages.otp_page import OtpPage
from pages.pin_setup_page import PinSetupPage
from pages.system_dialog_page import SystemDialogPage
from pages.update_dialog import UpdateDialog


CONTACT_MANAGER_LABEL = "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f \u0441 \u043c\u0435\u043d\u0435\u0434\u0436\u0435\u0440\u043e\u043c"


def _open_home_via_debug_otp(logged_out_driver, test_user, settings) -> HomePage:
    if not settings.debug_otp_enabled:
        pytest.skip("DEBUG_OTP_ENABLED=true is required for these UI checks")

    with allure.step("Request a debug OTP"):
        auth_page = AuthPage(logged_out_driver)
        auth_page.enter_phone(test_user.phone)
        auth_page.accept_privacy_policy()
        auth_page.request_otp()

    with allure.step("Authenticate with the debug OTP displayed by the app"):
        otp_page = OtpPage(logged_out_driver)
        assert otp_page.is_opened(), "OTP screen did not open"
        otp_page.enter_code(otp_page.get_displayed_debug_code())

    with allure.step("Complete transient screens and open Home"):
        PinSetupPage(logged_out_driver).skip_if_opened()
        SystemDialogPage(logged_out_driver).allow_notifications_if_requested()
        UpdateDialog(logged_out_driver).postpone_if_opened()
        home_page = HomePage(logged_out_driver)
        assert home_page.is_opened(), "Home screen did not open after authentication"
    return home_page
@pytest.mark.ui
@pytest.mark.positive
@pytest.mark.requires_debug_otp
@pytest.mark.qase_case("1148")
@allure.id("KAN-2-1")
@allure.title("[KAN-2-1] Contact-manager action is visible and enabled on Home")
def test_contact_manager_action_is_visible_and_enabled(
    logged_out_driver, test_user, settings
):
    home_page = _open_home_via_debug_otp(logged_out_driver, test_user, settings)

    with allure.step("Verify that the contact-manager action is available"):
        assert home_page.is_contact_manager_available(), (
            "Contact-manager action is missing or disabled"
        )
@pytest.mark.ui
@pytest.mark.positive
@pytest.mark.requires_debug_otp
@pytest.mark.qase_case("1150")
@allure.id("KAN-2-3")
@allure.title("[KAN-2-3] Contact-manager action uses the expected label")
def test_contact_manager_action_has_expected_label(
    logged_out_driver, test_user, settings
):
    home_page = _open_home_via_debug_otp(logged_out_driver, test_user, settings)

    with allure.step("Verify the label of the contact-manager action"):
        assert home_page.contact_manager_label() == CONTACT_MANAGER_LABEL
