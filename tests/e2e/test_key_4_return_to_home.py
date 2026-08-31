import pytest
from pages.auth_page import AuthPage
from pages.otp_page import OtpPage
from pages.pin_setup_page import PinSetupPage
from pages.home_page import HomePage
from pages.system_dialog_page import SystemDialogPage
from pages.update_dialog import UpdateDialog

@pytest.mark.e2e
def test_key_4_return_to_home(logged_out_driver, test_user):
    driver = logged_out_driver
    # Authorization flow
    auth_page = AuthPage(driver)
    auth_page.enter_phone(test_user.phone)
    auth_page.accept_privacy_policy()
    assert auth_page.can_request_otp()
    auth_page.request_otp()
    otp_page = OtpPage(driver)
    code = otp_page.get_displayed_debug_code()
    otp_page.enter_code(code)
    pin_page = PinSetupPage(driver)
    pin_page.skip_if_opened()
    SystemDialogPage(driver).allow_notifications_if_requested()
    UpdateDialog(driver).postpone_if_opened()
    home_page = HomePage(driver)
    assert home_page.is_opened()
    # Navigate to payments
    home_page.click(HomePage.payments_tab)
    assert home_page.is_visible(HomePage.payments_tab)
    # STEP: Press back to return to home screen
    driver.back()
    home_page = HomePage(driver)
    assert home_page.is_opened()
    assert home_page.is_visible(HomePage.payments_tab)
