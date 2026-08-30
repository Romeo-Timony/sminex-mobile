"""Qase v1 client for preserving automation coverage on manual test cases."""

from __future__ import annotations

from typing import Any

import requests


class QaseApiClient:
    def __init__(
        self,
        token: str,
        project_code: str,
        base_url: str = "https://api.qase.io/v1",
        timeout_seconds: int = 30,
    ) -> None:
        self.project_code = project_code
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({"Token": token, "Content-Type": "application/json"})

    def update_manual_case_coverage(
        self,
        case_id: int,
        *,
        field_ids: dict[str, int],
        automation_type: str,
        code_path: str,
        test_id: str,
        note: str,
    ) -> None:
        """Record an automated implementation without changing Qase's Manual status."""
        values = {
            str(field_ids["coverage"]): "Automated",
            str(field_ids["type"]): automation_type,
            str(field_ids["code_path"]): code_path,
            str(field_ids["test_id"]): test_id,
            str(field_ids["note"]): note,
        }
        response = self.session.patch(
            f"{self.base_url}/case/{self.project_code}/{case_id}",
            json={"custom_field": values},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
