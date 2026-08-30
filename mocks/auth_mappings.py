from typing import Any
from urllib.parse import quote_plus


MOCK_OTP_CODE = "1111"
OTP_REQUEST_PATH = "/api/v1/auth/send"
TOKEN_REQUEST_PATH = "/api/v1/auth/token"
MOCK_ACCESS_TOKEN = (
    "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0."
    "eyJleHAiOjQxMDI0NDQ4MDAsInNpZCI6Im1vY2stc2Vzc2lvbiIsInNjb3BlIjoib3Bl"
    "bmlkIiwibmFtZSI6IlVJIE1vY2siLCJtb2JpbGVfbnVtYmVyIjoiKzc5MDk3OTIyOTk5"
    "In0.mock-signature"
)


def json_mapping(
    *,
    method: str,
    request_path: str,
    response_body: dict[str, Any],
    name: str,
    status: int = 200,
) -> dict[str, Any]:
    """Build an exact-path JSON response mapping."""
    return {
        "name": name,
        "request": {"method": method, "urlPath": request_path},
        "response": {
            "status": status,
            "headers": {"Content-Type": "application/json"},
            "jsonBody": response_body,
        },
    }


def otp_request_mapping(
    request_path: str,
    status: int,
    response_body: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    """Build a mapping for the OTP endpoint.

    The exact payload must be aligned with the mobile API contract before the
    mapping is enabled in a UI test.
    """
    return {
        "name": name,
        "request": {"method": "POST", "urlPath": request_path},
        "response": {
            "status": status,
            "headers": {"Content-Type": "application/json"},
            "jsonBody": response_body,
        },
    }


def otp_login_mapping(request_path: str = OTP_REQUEST_PATH) -> dict[str, Any]:
    """Stub the OTP-request response shown by the debug OTP screen.

    The Android auth DTO is ``OtpResponse(code: String)``.  The endpoint path
    remains a CI setting because it belongs to the mobile API contract.
    """
    mapping = otp_request_mapping(
        request_path=request_path,
        status=200,
        response_body={"code": MOCK_OTP_CODE},
        name=f"mock OTP request with code {MOCK_OTP_CODE}",
    )
    mapping["request"]["headers"] = {
        "Content-Type": {"contains": "application/x-www-form-urlencoded"}
    }
    mapping["request"]["bodyPatterns"] = [{"contains": "phone_number="}]
    return mapping


def token_exchange_mapping() -> dict[str, Any]:
    """Stub the phone OTP exchange at the same endpoint used for token refresh."""
    return {
        "name": f"mock phone sign-in with OTP {MOCK_OTP_CODE}",
        "priority": 10,
        "request": {
            "method": "POST",
            "urlPath": TOKEN_REQUEST_PATH,
            "headers": {
                "Content-Type": {"contains": "application/x-www-form-urlencoded"}
            },
            "bodyPatterns": [
                {"contains": f"code={MOCK_OTP_CODE}"},
                {"contains": "phone_number="},
            ],
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "jsonBody": {
                "access_token": MOCK_ACCESS_TOKEN,
                "expires_in": 3600,
                "not-before-policy": 0,
                "refresh_expires_in": 86400,
                "refresh_token": MOCK_ACCESS_TOKEN,
                "scope": "openid",
                "session_state": "mock-session",
                "token_type": "Bearer",
            },
        },
    }


def invalid_token_exchange_mapping(code: str = "9999") -> dict[str, Any]:
    """Return the authorization error displayed for an invalid four-digit OTP."""
    return {
        "name": f"mock rejected OTP {code}",
        "priority": 10,
        "request": {
            "method": "POST",
            "urlPath": TOKEN_REQUEST_PATH,
            "headers": {
                "Content-Type": {"contains": "application/x-www-form-urlencoded"}
            },
            "bodyPatterns": [
                {"contains": f"code={code}"},
                {"contains": "phone_number="},
            ],
        },
        "response": {
            "status": 401,
            "headers": {"Content-Type": "application/json"},
            "jsonBody": {"message": "Invalid OTP code"},
        },
    }


def otp_request_error_mapping(
    phone: str, status: int = 400, message: str = "Invalid phone number"
) -> dict[str, Any]:
    """Return a deterministic validation error for one invalid phone input."""
    mapping = otp_request_mapping(
        request_path=OTP_REQUEST_PATH,
        status=status,
        response_body={"message": message},
        name=f"mock rejected phone {phone or 'empty'}",
    )
    mapping["request"]["headers"] = {
        "Content-Type": {"contains": "application/x-www-form-urlencoded"}
    }
    mapping["request"]["bodyPatterns"] = [
        {"contains": f"phone_number={quote_plus(phone)}"}
    ]
    return mapping


def phone_login_mappings(
    otp_request_path: str = OTP_REQUEST_PATH,
) -> list[dict[str, Any]]:
    """All backend calls that form the phone + OTP authentication exchange."""
    return [otp_login_mapping(otp_request_path), token_exchange_mapping()]


def authenticated_bootstrap_mappings(
    projects: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Minimal authenticated profile used to open the main application shell.

    This mirrors ``UserInfoDTO`` from the debug APK.  The application treats a
    non-club user without projects as blocked, so the fixture has one minimal
    project; it is test data, not a dependency on a real resident account.
    """
    return [
        json_mapping(
            method="GET",
            request_path="/api/v1/auth/userinfo",
            name="mock authenticated user profile",
            response_body={
                "acr": "1",
                "allowed-origins": ["*"],
                "azp": "sminex-app",
                "email": "ui-mock@example.test",
                "email_verified": True,
                # UserInfoDTO models JWT timestamps as signed 32-bit integers.
                "exp": 2_000_000_000,
                "family_name": "Mock",
                "given_name": "UI",
                "guid1c": "mock-guid-1c",
                "iat": 1704067200,
                "isLegalEntity": False,
                "isMobileNumberConfirmed": True,
                "isProcessingPdAccepted": True,
                "isTechnicalAccount": False,
                "iss": "wiremock",
                "jti": "mock-jti",
                "locale": "ru",
                "middle_name": "",
                "mobile_number": "+79097922999",
                "name": "UI Mock",
                "preferred_username": "+79097922999",
                "projects": projects
                if projects is not None
                else [
                    {
                        "id": "mock-project-001",
                        "name": "Mock Residence",
                        "src": "mock",
                        "personalAccounts": [],
                    }
                ],
                "roles": ["resident"],
                "scope": "openid",
                "sid": "mock-session",
                "sub": "mock-user",
                "title": "",
                "typ": "Bearer",
                "isComfortUser": True,
                "isClubUser": False,
                "avatarUrl": None,
            },
        )
    ]


def userinfo_mapping(
    response_body: dict[str, Any], status: int = 200
) -> dict[str, Any]:
    """Create a configurable userinfo response for API contract checks."""
    return json_mapping(
        method="GET",
        request_path="/api/v1/auth/userinfo",
        name=f"mock userinfo response {status}",
        response_body=response_body,
        status=status,
    )


def unauthenticated_bootstrap_mappings() -> list[dict[str, Any]]:
    """Minimal public data required before the Android auth screen is shown."""
    return [
        json_mapping(
            method="GET",
            request_path="/api/v1/staticData/update",
            name="mock application update state",
            response_body={
                "version": "3.4.0 - SminexApp",
                "platform": "ANDROID",
                "state": "UP_TO_DATE",
                "notificate": False,
            },
        ),
        json_mapping(
            method="GET",
            request_path="/api/v1/staticData/basicinfo",
            name="mock public application information",
            response_body={
                "privacyLink": None,
                "agreementLink": None,
                "contactEmail": "ui-mock@example.test",
                "contactPhone": "+70000000000",
                "mobileAppsLinks": {
                    "ruStore": "https://example.test/rustore",
                    "googlePlay": "https://example.test/google-play",
                    "appGallery": None,
                },
            },
        ),
    ]
