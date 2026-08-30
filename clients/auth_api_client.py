"""HTTP client for the phone authorization and OTP API contract."""

import requests


class AuthApiClient:
    """Explicit client for the same form-encoded requests as the Android app."""

    def __init__(
        self,
        api_base_url: str,
        otp_request_path: str = "/api/v1/auth/send",
        timeout_seconds: int = 15,
    ) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.otp_request_path = f"/{otp_request_path.lstrip('/')}"
        self.timeout_seconds = timeout_seconds

    def request_phone_otp(self, phone: str) -> requests.Response:
        return requests.post(
            f"{self.api_base_url}{self.otp_request_path}",
            data={"phone_number": phone},
            timeout=self.timeout_seconds,
        )

    def exchange_phone_otp(self, phone: str, code: str) -> requests.Response:
        return requests.post(
            f"{self.api_base_url}/api/v1/auth/token",
            data={
                "client_id": "front-client",
                "grant_type": "password",
                "phone_number": phone,
                "code": code,
            },
            timeout=self.timeout_seconds,
        )
