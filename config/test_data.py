from dataclasses import dataclass

from config.settings import Settings


@dataclass(frozen=True)
class TestUser:
    phone: str


def get_test_user(settings: Settings) -> TestUser:
    return TestUser(phone=settings.test_phone)
