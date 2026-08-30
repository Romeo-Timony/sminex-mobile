"""API contract checks for phone authorization and OTP verification on WireMock."""

import allure
import pytest

from clients.auth_api_client import AuthApiClient
from mocks.auth_mappings import (
    MOCK_OTP_CODE,
    invalid_token_exchange_mapping,
    otp_login_mapping,
    otp_request_error_mapping,
    token_exchange_mapping,
)


INVALID_PHONES = ("", "+7909", "invalid")
INVALID_OTP_CODES = ("9999", "12", "abcd")


@pytest.fixture()
def auth_api_client(settings) -> AuthApiClient:
    if not settings.app_api_base_url:
        pytest.skip("APP_API_BASE_URL is required for mock API tests")
    return AuthApiClient(settings.app_api_base_url)


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.positive
@allure.epic("Авторизация")
@allure.feature("API отправки OTP")
@allure.id("API-AUTH-001")
@allure.title("[API-AUTH-001] Авторизация — запрос OTP для валидного номера — возвращается код 1111")
def test_request_otp_for_valid_phone_returns_mock_code(
    wiremock, auth_api_client, test_user
):
    wiremock.register_mapping(otp_login_mapping())

    response = auth_api_client.request_phone_otp(test_user.phone)

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json() == {"code": MOCK_OTP_CODE}


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.negative
@pytest.mark.parametrize("phone", INVALID_PHONES)
@allure.epic("Авторизация")
@allure.feature("API отправки OTP")
@allure.id("API-AUTH-002")
@allure.title("[API-AUTH-002] Авторизация — запрос OTP с невалидным номером — возвращается ошибка валидации")
def test_request_otp_for_invalid_phone_returns_validation_error(
    wiremock, auth_api_client, phone
):
    wiremock.register_mapping(otp_request_error_mapping(phone))

    response = auth_api_client.request_phone_otp(phone)

    assert response.status_code == 400
    assert response.json()["message"] == "Invalid phone number"


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.positive
@allure.epic("Авторизация")
@allure.feature("API проверки OTP")
@allure.id("API-OTP-003")
@allure.title("[API-OTP-003] Проверка OTP — корректный код 1111 — возвращается пара токенов")
def test_exchange_correct_otp_returns_access_and_refresh_tokens(
    wiremock, auth_api_client, test_user
):
    wiremock.register_mapping(token_exchange_mapping())

    response = auth_api_client.exchange_phone_otp(test_user.phone, MOCK_OTP_CODE)

    body = response.json()
    assert response.status_code == 200
    assert body["token_type"] == "Bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] > 0


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.negative
@pytest.mark.parametrize("code", INVALID_OTP_CODES)
@allure.epic("Авторизация")
@allure.feature("API проверки OTP")
@allure.id("API-OTP-004")
@allure.title("[API-OTP-004] Проверка OTP — неверный, неполный или нечисловой код — возвращается ошибка авторизации")
def test_exchange_invalid_otp_returns_authorization_error(
    wiremock, auth_api_client, test_user, code
):
    wiremock.register_mapping(invalid_token_exchange_mapping(code))

    response = auth_api_client.exchange_phone_otp(test_user.phone, code)

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid OTP code"
