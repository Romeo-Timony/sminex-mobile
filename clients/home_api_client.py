"""HTTP client for authenticated main-screen bootstrap data."""

import requests


class HomeApiClient:
    """Client for the profile consumed while opening the main screen."""

    def __init__(self, api_base_url: str, timeout_seconds: int = 15) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get_user_profile(self, access_token: str) -> requests.Response:
        return requests.get(
            f"{self.api_base_url}/api/v1/auth/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=self.timeout_seconds,
        )

    def get_deals_projects_info(
        self, access_token: str | None = None
    ) -> requests.Response:
        """Return the projects bootstrap payload requested by the Android home screen."""
        headers = (
            {"Authorization": f"Bearer {access_token}"} if access_token else None
        )
        return requests.get(
            f"{self.api_base_url}/api/v2/deals/projects/info",
            headers=headers,
            timeout=self.timeout_seconds,
        )
