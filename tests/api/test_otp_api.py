import pytest
import allure


@pytest.mark.api
@pytest.mark.positive
@allure.epic("Авторизация")
@allure.feature("OTP API")
@allure.id("API-OTP-001")
@allure.title("[API-OTP-001] Запрос OTP — зарегистрированный тестовый номер — возвращается успешный статус")
def test_otp_request_accepts_registered_test_phone(
    auth_api_client, otp_api_contract, test_user
):
    response = auth_api_client.request_phone_otp(test_user.phone)
    expected_success_status, _ = otp_api_contract
    assert response.status_code == expected_success_status


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.parametrize(
    "phone",
    (
        pytest.param("", id="пустое-поле"),
        pytest.param("+7909", id="слишком-короткий-номер"),
        pytest.param("invalid", id="недопустимые-символы"),
    ),
)
@allure.epic("Авторизация")
@allure.feature("OTP API")
@allure.id("API-OTP-002")
@allure.title("[API-OTP-002] Запрос OTP — некорректный номер — возвращается статус ошибки валидации")
def test_otp_request_rejects_invalid_phone(auth_api_client, otp_api_contract, phone):
    response = auth_api_client.request_phone_otp(phone)
    _, expected_invalid_status = otp_api_contract
    assert response.status_code == expected_invalid_status
