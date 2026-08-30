import requests

import pytest
import allure

from mocks.auth_mappings import (
    MOCK_OTP_CODE,
    phone_login_mappings,
    otp_login_mapping,
    otp_request_mapping,
)


@pytest.mark.mock
@allure.epic("Тестовая инфраструктура")
@allure.feature("WireMock")
@allure.id("MOCK-001")
@allure.title("[MOCK-001] WireMock — регистрация изолированного маппинга OTP — возвращается настроенный ответ")
def test_wiremock_registers_isolated_otp_mapping(wiremock, settings):
    mapping = otp_request_mapping(
        request_path="/test/otp/request",
        status=202,
        response_body={"requestId": "mock-otp-request"},
        name="mock OTP request success",
    )
    wiremock.register_mapping(mapping)

    response = requests.post(
        f"{settings.app_api_base_url}/test/otp/request",
        json={"phone": "+79097922999"},
        timeout=10,
    )

    assert response.status_code == 202
    assert response.json() == {"requestId": "mock-otp-request"}
    assert any(
        request["request"]["url"] == "/test/otp/request"
        for request in wiremock.received_requests()
    )


@pytest.mark.mock
@allure.epic("Тестовая инфраструктура")
@allure.feature("WireMock")
@allure.id("MOCK-002")
@allure.title("[MOCK-002] WireMock — запрос OTP — возвращается моковый код 1111")
def test_wiremock_returns_mocked_otp_code_1111(wiremock, settings):
    request_path = "/api/v1/auth/send"
    wiremock.register_mapping(otp_login_mapping(request_path))

    response = requests.post(
        f"{settings.app_api_base_url}{request_path}",
        data={"phone_number": "+79097922999"},
        timeout=10,
    )

    assert response.status_code == 200
    assert response.json() == {"code": MOCK_OTP_CODE}


@pytest.mark.mock
@allure.epic("Тестовая инфраструктура")
@allure.feature("WireMock")
@allure.id("MOCK-003")
@allure.title("[MOCK-003] WireMock — обмен OTP на токен — возвращается валидный моковый токен")
def test_wiremock_stubs_complete_phone_otp_exchange(wiremock, settings):
    for mapping in phone_login_mappings():
        wiremock.register_mapping(mapping)

    response = requests.post(
        f"{settings.app_api_base_url}/api/v1/auth/token",
        data={
            "client_id": "mobile",
            "grant_type": "password",
            "code": MOCK_OTP_CODE,
            "phone_number": "+79097922999",
        },
        timeout=10,
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "Bearer"
    assert response.json()["access_token"].count(".") == 2
