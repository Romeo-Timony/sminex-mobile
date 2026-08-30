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
        pytest.skip("DEBUG_OTP_ENABLED=true is required for this scenario")

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


@pytest.mark.review
@pytest.mark.e2e
@pytest.mark.positive
@pytest.mark.requires_debug_otp
@allure.id("KAN-2-1160")
@allure.title('[E2E] [Positive] Пользователь открывает главное экран приложения и видит кнопку "Связаться с менеджером".')
def test_user_sees_contact_manager_button_on_home_manual(logged_out_driver, test_user, settings):
    home_page = _open_home_via_debug_otp(logged_out_driver, test_user, settings)

    assert home_page.is_contact_manager_available(), (
        'Пользователь не видит доступную кнопку "Связаться с менеджером" на главном экране'
    )
