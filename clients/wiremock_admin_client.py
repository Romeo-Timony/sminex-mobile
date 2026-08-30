from typing import Any

import requests


class WireMockAdminClient:
    """Small, explicit client for the WireMock administrative API."""

    def __init__(self, admin_url: str, timeout_seconds: int = 10) -> None:
        self.admin_url = admin_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def healthcheck(self) -> None:
        response = self.session.get(
            f"{self.admin_url}/__admin/health", timeout=self.timeout_seconds
        )
        response.raise_for_status()

    def reset(self) -> None:
        response = self.session.post(
            f"{self.admin_url}/__admin/mappings/reset", timeout=self.timeout_seconds
        )
        response.raise_for_status()

    def register_mapping(self, mapping: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(
            f"{self.admin_url}/__admin/mappings",
            json=mapping,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def received_requests(self) -> list[dict[str, Any]]:
        response = self.session.get(
            f"{self.admin_url}/__admin/requests", timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return response.json().get("requests", [])
