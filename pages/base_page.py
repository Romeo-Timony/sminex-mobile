from typing import TypeAlias

from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait


Locator: TypeAlias = tuple[str, str]


class BasePage:
    def __init__(self, driver: WebDriver, timeout: int = 20) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def click(self, locator: Locator) -> None:
        self.wait.until(
            lambda current: current.find_element(*locator).is_enabled()
            and current.find_element(*locator)
        ).click()

    def type_text(self, locator: Locator, value: str) -> None:
        element = self.wait.until(lambda current: current.find_element(*locator))
        element.click()
        element.clear()
        element.send_keys(value)

    def is_visible(self, locator: Locator, timeout: int = 3) -> bool:
        try:
            return WebDriverWait(self.driver, timeout).until(
                lambda current: current.find_element(*locator).is_displayed()
            )
        except TimeoutException:
            return False

    def is_enabled(self, locator: Locator, timeout: int = 3) -> bool:
        try:
            return bool(
                WebDriverWait(self.driver, timeout).until(
                    lambda current: current.find_element(*locator).is_enabled()
                )
            )
        except TimeoutException:
            return False

    def find_optional(self, locator: Locator, timeout: int = 3):
        try:
            return WebDriverWait(self.driver, timeout).until(
                lambda current: current.find_element(*locator)
            )
        except TimeoutException:
            return None
