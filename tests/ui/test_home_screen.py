"""UI checks for the main screen on the debug test environment."""

import allure
import pytest

from pages.auth_page import AuthPage
from pages.home_page import HomePage
from pages.otp_page import OtpPage
from pages.pin_setup_page import PinSetupPage
from pages.system_dialog_page import SystemDialogPage
from pages.update_dialog import UpdateDialog


def _request_debug_otp(driver, phone: str) -> OtpPage:
    auth_page = AuthPage(driver)
    auth_page.enter_phone(phone)
    auth_page.accept_privacy_policy()
    auth_page.request_otp()

    otp_page = OtpPage(driver)
    assert otp_page.is_opened(), "Экран ввода OTP не открылся"
    return otp_page


def _complete_login(driver, phone: str) -> None:
    otp_page = _request_debug_otp(driver, phone)
    otp_page.enter_code(otp_page.get_displayed_debug_code())

    PinSetupPage(driver).skip_if_opened()
    SystemDialogPage(driver).allow_notifications_if_requested()
    UpdateDialog(driver).postpone_if_opened()


@pytest.fixture()
def authenticated_home_driver(logged_out_driver, settings, test_user):
    """Open a declared, isolated main-screen state for every UI scenario."""
    if not settings.debug_otp_enabled:
        pytest.skip("DEBUG_OTP_ENABLED=true is required for home UI tests")

    _complete_login(logged_out_driver, test_user.phone)
    assert HomePage(logged_out_driver).is_opened(), "Главный экран не открылся"
    return logged_out_driver


@pytest.mark.ui
@pytest.mark.positive
@pytest.mark.requires_debug_otp
@allure.epic("Главный экран")
@allure.feature("Отображение главного экрана")
@allure.id("UI-HOME-001")
@allure.title("[UI-HOME-001] Главный экран — успешный вход по debug OTP — отображается вкладка «Главная»")
def test_main_screen_is_opened_after_successful_debug_otp_login(
    authenticated_home_driver, test_recording
):
    assert HomePage(authenticated_home_driver).is_opened()


@pytest.mark.ui
@pytest.mark.positive
@pytest.mark.requires_debug_otp
@allure.epic("Главный экран")
@allure.feature("Нижняя навигация")
@allure.id("UI-HOME-003")
@allure.title("[UI-HOME-003] Главный экран — загрузка — отображаются все вкладки нижней навигации")
def test_main_screen_displays_all_bottom_navigation_tabs(
    authenticated_home_driver, test_recording
):
    assert HomePage(authenticated_home_driver).has_bottom_navigation()


@pytest.mark.ui
@pytest.mark.positive
@pytest.mark.requires_debug_otp
@allure.epic("Главный экран")
@allure.feature("Основные карточки")
@allure.id("UI-HOME-004")
@allure.title("[UI-HOME-004] Главный экран — загрузка — отображаются основные карточки пользователя")
def test_main_screen_displays_primary_user_cards(authenticated_home_driver, test_recording):
    assert HomePage(authenticated_home_driver).has_primary_cards()


@pytest.mark.ui
@pytest.mark.negative
@allure.epic("Главный экран")
@allure.feature("Защита доступа к главному экрану")
@allure.id("UI-HOME-005")
@allure.title("[UI-HOME-005] Главный экран — пользователь без авторизации — вкладка «Главная» не отображается")
def test_main_screen_is_not_displayed_before_authorization(logged_out_driver):
    assert not HomePage(logged_out_driver).is_opened(timeout=3)


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.requires_debug_otp
@allure.epic("Главный экран")
@allure.feature("Защита доступа к главному экрану")
@allure.id("UI-HOME-002")
@allure.title("[UI-HOME-002] Главный экран — неверный OTP — главный экран не открывается")
def test_main_screen_is_not_opened_after_invalid_otp(
    logged_out_driver, test_user, settings
):
    if not settings.debug_otp_enabled:
        pytest.skip("DEBUG_OTP_ENABLED=true is required for this UI test")
    otp_page = _request_debug_otp(logged_out_driver, test_user.phone)
    otp_page.enter_code("0000")

    assert not HomePage(logged_out_driver).is_opened(timeout=5)
