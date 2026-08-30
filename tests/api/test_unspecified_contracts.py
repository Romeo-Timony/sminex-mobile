import allure
import pytest

from clients.home_api_client import HomeApiClient
from mocks.auth_mappings import MOCK_ACCESS_TOKEN, json_mapping


PROJECT_INFO_PATH = "/api/v2/deals/projects/info"
PROJECT_ID = "traffic-project-001"


@pytest.fixture()
def home_bootstrap_api_client(settings) -> HomeApiClient:
    if not settings.app_api_base_url:
        pytest.skip("APP_API_BASE_URL is required for WireMock API checks")
    return HomeApiClient(settings.app_api_base_url)
@pytest.mark.api
@pytest.mark.positive
@allure.id("KAN-2-10")
@allure.title("[API] Home projects bootstrap returns project data")
def test_deals_projects_info_returns_project_data(
    wiremock, home_bootstrap_api_client
):
    """Endpoint was observed in Android OkHttp traffic after successful login."""
    wiremock.register_mapping(
        json_mapping(
            method="GET",
            request_path=PROJECT_INFO_PATH,
            name="KAN-2 projects bootstrap response",
            response_body={
                "data": [
                    {
                        "id": PROJECT_ID,
                        "name": "Traffic Test Residence",
                        "images": [],
                    }
                ]
            },
        )
    )

    with allure.step("Request project bootstrap data with a Bearer token"):
        response = home_bootstrap_api_client.get_deals_projects_info(
            MOCK_ACCESS_TOKEN
        )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json()["data"][0]["id"] == PROJECT_ID
    assert response.json()["data"][0]["name"] == "Traffic Test Residence"
@pytest.mark.api
@pytest.mark.negative
@allure.id("KAN-2-11")
@allure.title("[API] Home projects bootstrap requires a Bearer token")
def test_deals_projects_info_rejects_request_without_token(
    wiremock, home_bootstrap_api_client
):
    wiremock.register_mapping(
        json_mapping(
            method="GET",
            request_path=PROJECT_INFO_PATH,
            name="KAN-2 projects bootstrap rejects anonymous request",
            status=401,
            response_body={"message": "Unauthorized"},
        )
    )

    with allure.step("Request project bootstrap data without a token"):
        response = home_bootstrap_api_client.get_deals_projects_info()

    assert response.status_code == 401
    assert response.json()["message"] == "Unauthorized"
