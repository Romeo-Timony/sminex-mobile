"""API checks for the profile data needed by the main screen."""

import allure
import pytest

from clients.home_api_client import HomeApiClient
from mocks.auth_mappings import (
    MOCK_ACCESS_TOKEN,
    authenticated_bootstrap_mappings,
    userinfo_mapping,
)


@pytest.fixture()
def home_api_client(settings) -> HomeApiClient:
    if not settings.app_api_base_url:
        pytest.skip("APP_API_BASE_URL is required for mock API tests")
    return HomeApiClient(settings.app_api_base_url)


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.positive
@allure.epic("Главный экран")
@allure.feature("API профиля пользователя")
@allure.id("API-HOME-001")
@allure.title("[API-HOME-001] Главный экран — профиль с проектом — возвращается список доступных проектов")
def test_user_profile_with_project_returns_data_for_main_screen(
    wiremock, home_api_client
):
    for mapping in authenticated_bootstrap_mappings():
        wiremock.register_mapping(mapping)

    response = home_api_client.get_user_profile(MOCK_ACCESS_TOKEN)

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json()["projects"]


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.positive
@allure.epic("Главный экран")
@allure.feature("API профиля пользователя")
@allure.id("API-HOME-003")
@allure.title("[API-HOME-003] Главный экран — валидный профиль — возвращаются подтверждённый телефон и имя пользователя")
def test_user_profile_returns_identity_attributes(wiremock, home_api_client):
    for mapping in authenticated_bootstrap_mappings():
        wiremock.register_mapping(mapping)

    body = home_api_client.get_user_profile(MOCK_ACCESS_TOKEN).json()

    assert body["name"] == "UI Mock"
    assert body["mobile_number"] == "+79097922999"
    assert body["isMobileNumberConfirmed"] is True


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.positive
@allure.epic("Главный экран")
@allure.feature("API профиля пользователя")
@allure.id("API-HOME-004")
@allure.title("[API-HOME-004] Главный экран — проект пользователя — возвращаются обязательные идентификатор и название")
def test_user_profile_returns_project_identity(wiremock, home_api_client):
    for mapping in authenticated_bootstrap_mappings():
        wiremock.register_mapping(mapping)

    project = home_api_client.get_user_profile(MOCK_ACCESS_TOKEN).json()["projects"][0]

    assert project["id"] == "mock-project-001"
    assert project["name"] == "Mock Residence"
    assert project["personalAccounts"] == []


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.negative
@allure.epic("Главный экран")
@allure.feature("API профиля пользователя")
@allure.id("API-HOME-002")
@allure.title("[API-HOME-002] Главный экран — профиль без проектов — возвращается пустой список проектов")
def test_user_profile_without_projects_returns_empty_projects_list(
    wiremock, home_api_client
):
    for mapping in authenticated_bootstrap_mappings(projects=[]):
        wiremock.register_mapping(mapping)

    response = home_api_client.get_user_profile(MOCK_ACCESS_TOKEN)

    assert response.status_code == 200
    assert response.json()["projects"] == []


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.negative
@pytest.mark.parametrize("status", (401, 403))
@allure.epic("Главный экран")
@allure.feature("API профиля пользователя")
@allure.id("API-HOME-005")
@allure.title("[API-HOME-005] Главный экран — отсутствует доступ к профилю — возвращается ошибка авторизации")
def test_user_profile_rejects_unauthorized_request(wiremock, home_api_client, status):
    wiremock.register_mapping(
        userinfo_mapping({"message": "Unauthorized"}, status=status)
    )

    response = home_api_client.get_user_profile(MOCK_ACCESS_TOKEN)

    assert response.status_code == status
    assert response.json()["message"] == "Unauthorized"


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.negative
@pytest.mark.parametrize("status", (500, 503))
@allure.epic("Главный экран")
@allure.feature("API профиля пользователя")
@allure.id("API-HOME-006")
@allure.title("[API-HOME-006] Главный экран — сервис профиля недоступен — возвращается серверная ошибка")
def test_user_profile_returns_server_error(wiremock, home_api_client, status):
    wiremock.register_mapping(
        userinfo_mapping({"message": "Service unavailable"}, status=status)
    )

    response = home_api_client.get_user_profile(MOCK_ACCESS_TOKEN)

    assert response.status_code == status
    assert response.json()["message"] == "Service unavailable"


@pytest.mark.api
@pytest.mark.mock
@pytest.mark.negative
@allure.epic("Главный экран")
@allure.feature("API профиля пользователя")
@allure.id("API-HOME-007")
@allure.title("[API-HOME-007] Главный экран — профиль без поля projects — контракт данных невалиден")
def test_user_profile_without_projects_field_is_not_a_valid_home_contract(
    wiremock, home_api_client
):
    wiremock.register_mapping(userinfo_mapping({"name": "UI Mock"}))

    body = home_api_client.get_user_profile(MOCK_ACCESS_TOKEN).json()

    assert "projects" not in body
