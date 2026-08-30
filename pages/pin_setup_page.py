from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class PinSetupPage(BasePage):
    pin_input = (
        AppiumBy.XPATH,
        "//*[@resource-id='pin_code_screen_create_pin_field']",
    )
    setup_later_button = (
        AppiumBy.XPATH,
        "//*[@resource-id='pin_code_screen_setup_later_button']",
    )

    def skip_if_opened(self) -> bool:
        button = self.find_optional(self.setup_later_button, timeout=10)
        if not button:
            return False
        button.click()
        return True

    def is_opened(self) -> bool:
        return self.is_visible(self.pin_input, timeout=5) or self.is_visible(
            self.setup_later_button, timeout=2
        )

    def enter_pin(self, pin: str) -> None:
        """Enter a four-digit PIN through the application's Compose keypad."""
        if len(pin) != 4 or not pin.isdigit():
            raise ValueError("PIN must contain exactly four digits")

        for digit in pin:
            # The Compose keypad exposes digit text but no resource IDs.
            self.click(
                (
                    AppiumBy.XPATH,
                    f"//*[@text='{digit}']/ancestor::*[@clickable='true'][1]",
                )
            )
