"""Isolated UI checks for OTP validation and the post-OTP PIN decision.

Every backend outcome is registered in WireMock before Android is started.
"""

import allure
import pytest

from mocks.auth_mappings import (
    MOCK_OTP_CODE,
    authenticated_bootstrap_mappings,
    invalid_token_exchange_mapping,
    otp_login_mapping,
    token_exchange_mapping,
    unauthenticated_bootstrap_mappings,
)
from pages.auth_page import AuthPage
from pages.home_page import HomePage
from pages.otp_page import OtpPage
from pages.pin_setup_page import PinSetupPage
from pages.system_dialog_page import SystemDialogPage
from pages.update_dialog import UpdateDialog


PIN_CODE = "2580"
WRONG_OTP_CODE = "9999"
MISMATCHED_PIN_CODE = "1111"

pytestmark = pytest.mark.requires_debug_otp


def _register_mappings(wiremock, *mappings) -> None:
    for mapping in [
        *unauthenticated_bootstrap_mappings(),
        *mappings,
    ]:
        wiremock.register_mapping(mapping)


@pytest.fixture()
def mock_otp_ready(wiremock, settings):
    _register_mappings(
        wiremock,
        otp_login_mapping(settings.mock_otp_request_path),
        *authenticated_bootstrap_mappings(),
        # A successful token exchange is deliberately bound to OTP 1111.
        # Unregistered codes cannot accidentally authenticate a test user.
        token_exchange_mapping(),
    )
    return wiremock


@pytest.fixture()
def mock_otp_driver(mock_otp_ready, logged_out_driver):
    return logged_out_driver


@pytest.fixture()
def mock_rejected_otp_ready(wiremock, settings):
    _register_mappings(
        wiremock,
        otp_login_mapping(settings.mock_otp_request_path),
        invalid_token_exchange_mapping(WRONG_OTP_CODE),
    )
    return wiremock


@pytest.fixture()
def mock_rejected_otp_driver(mock_rejected_otp_ready, logged_out_driver):
    return logged_out_driver


def _open_otp_screen(driver, phone: str) -> OtpPage:
    auth_page = AuthPage(driver)
    auth_page.enter_phone(phone)
    auth_page.accept_privacy_policy()
    auth_page.request_otp()
    otp_page = OtpPage(driver)
    assert otp_page.is_opened(), "OTP screen did not open"
    return otp_page


def _complete_otp_to_pin(driver, phone: str) -> PinSetupPage:
    otp_page = _open_otp_screen(driver, phone)
    assert otp_page.get_displayed_debug_code() == MOCK_OTP_CODE
    otp_page.enter_code(MOCK_OTP_CODE)
    pin_page = PinSetupPage(driver)
    assert pin_page.is_opened(), "PIN setup screen did not open after valid OTP"
    return pin_page


@pytest.mark.ui
@pytest.mark.ui_mock
@pytest.mark.positive
@allure.epic("Авторизация")
@allure.feature("Ввод OTP")
@allure.story("Экран ввода OTP")
@allure.id("UI-OTP-001")
@allure.title("[UI-OTP-001] Экран OTP — получение кода 1111 — отображаются код и четыре поля ввода")
def test_otp_screen_displays_mocked_code_and_four_inputs(mock_otp_driver, test_user):
    otp_page = _open_otp_screen(mock_otp_driver, test_user.phone)

    assert otp_page.get_displayed_debug_code() == MOCK_OTP_CODE
    assert len(otp_page.get_code_inputs()) == 4


@pytest.mark.ui
@pytest.mark.ui_mock
@pytest.mark.negative
@allure.epic("Авторизация")
@allure.feature("Ввод OTP")
@allure.story("Валидация OTP")
@allure.id("UI-OTP-002")
@allure.title("[UI-OTP-002] Экран OTP — ввод неполного кода — авторизация не запускается")
def test_partial_otp_does_not_leave_otp_screen(mock_otp_driver, test_user):
    otp_page = _open_otp_screen(mock_otp_driver, test_user.phone)

    otp_page.enter_partial_code("11")

    assert otp_page.is_opened(), "Partial OTP must not start authorization"
    assert not otp_page.has_wrong_code_error()


@pytest.mark.ui
@pytest.mark.ui_mock
@pytest.mark.negative
@allure.epic("Авторизация")
@allure.feature("Ввод OTP")
@allure.story("Валидация OTP")
@allure.id("UI-OTP-003")
@allure.title("[UI-OTP-003] Экран OTP — ввод неверного кода — отображается информер ошибки")
def test_invalid_otp_shows_error_and_keeps_user_on_otp_screen(
    mock_rejected_otp_driver, test_user
):
    otp_page = _open_otp_screen(mock_rejected_otp_driver, test_user.phone)

    otp_page.enter_code(WRONG_OTP_CODE)

    assert otp_page.is_opened(), "Invalid OTP must not authorize the user"
    assert otp_page.has_wrong_code_error(), "Wrong OTP informer was not displayed"


@pytest.mark.ui
@pytest.mark.ui_mock
@pytest.mark.positive
@allure.epic("Авторизация")
@allure.feature("Настройка PIN-кода")
@allure.story("Пропуск настройки PIN-кода")
@allure.id("UI-OTP-004")
@allure.title("[UI-OTP-004] Настройка PIN-кода — пропуск шага — открывается главный экран")
def test_user_can_skip_pin_setup_and_open_home(mock_otp_driver, test_user):
    pin_page = _complete_otp_to_pin(mock_otp_driver, test_user.phone)

    assert pin_page.skip_if_opened(), "PIN setup did not offer the skip action"
    SystemDialogPage(mock_otp_driver).allow_notifications_if_requested()
    UpdateDialog(mock_otp_driver).postpone_if_opened()
    assert HomePage(mock_otp_driver).is_opened()


@pytest.mark.ui
@pytest.mark.ui_mock
@pytest.mark.positive
@allure.epic("Авторизация")
@allure.feature("Настройка PIN-кода")
@allure.story("Создание PIN-кода")
@allure.id("UI-OTP-005")
@allure.title("[UI-OTP-005] Настройка PIN-кода — создание и подтверждение совпадающего кода — открывается главный экран")
def test_user_can_create_and_confirm_pin(mock_otp_driver, test_user):
    pin_page = _complete_otp_to_pin(mock_otp_driver, test_user.phone)

    with allure.step("Create PIN"):
        pin_page.enter_pin(PIN_CODE)
    with allure.step("Confirm PIN"):
        pin_page.enter_pin(PIN_CODE)

    SystemDialogPage(mock_otp_driver).allow_notifications_if_requested()
    UpdateDialog(mock_otp_driver).postpone_if_opened()
    assert HomePage(mock_otp_driver).is_opened()


@pytest.mark.ui
@pytest.mark.ui_mock
@pytest.mark.negative
@allure.epic("Авторизация")
@allure.feature("Настройка PIN-кода")
@allure.story("Создание PIN-кода")
@allure.id("UI-OTP-006")
@allure.title("[UI-OTP-006] Настройка PIN-кода — подтверждение несовпадающим кодом — пользователь остаётся на экране PIN")
def test_mismatched_pin_confirmation_does_not_open_home(mock_otp_driver, test_user):
    pin_page = _complete_otp_to_pin(mock_otp_driver, test_user.phone)

    pin_page.enter_pin(PIN_CODE)
    pin_page.enter_pin(MISMATCHED_PIN_CODE)

    assert pin_page.is_opened(), "PIN mismatch must keep the user in PIN setup"
    assert not HomePage(mock_otp_driver).is_opened()
