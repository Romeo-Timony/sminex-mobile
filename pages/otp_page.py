import re

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class OtpPage(BasePage):
    """Экран ввода одноразового кода."""

    code_input_ids = (
        "otp_screen_enter_otp_field_0",
        "otp_screen_enter_otp_field_1",
        "otp_screen_enter_otp_field_2",
        "otp_screen_enter_otp_field_3",
    )
    otp_debug_message = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("otpCodeDebug=")',
    )
    wrong_code_error = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textStartsWith("Неверно введ")',
    )
    auth_phone_input = (
        AppiumBy.XPATH,
        "//*[@resource-id='auth_screen_phone_email_input']",
    )

    def is_opened(self) -> bool:
        try:
            return bool(self.wait.until(self._is_otp_screen))
        except Exception:
            return False

    def _is_otp_screen(self, driver) -> bool:
        has_code_input = len(self.get_code_inputs(driver)) == 4
        is_auth_screen = bool(driver.find_elements(*self.auth_phone_input))
        return has_code_input and not is_auth_screen

    def get_code_inputs(self, driver=None):
        """Return OTP fields in their display order using stable resource IDs."""
        current_driver = driver or self.driver
        return [
            elements[0]
            for resource_id in self.code_input_ids
            if (
                elements := current_driver.find_elements(
                    AppiumBy.XPATH, f"//*[@resource-id='{resource_id}']"
                )
            )
        ]

    def enter_code(self, code: str) -> None:
        if not re.fullmatch(r"\d{4}", code):
            raise ValueError("OTP must contain exactly four digits")

        inputs = self.wait.until(
            lambda driver: self.get_code_inputs(driver) or False
        )
        if len(inputs) != 4:
            raise RuntimeError(f"Expected four OTP inputs, received {len(inputs)}")

        # The application moves focus itself after every digit. Clicking the
        # next cell manually interrupts that behaviour and drops a digit.
        for digit in code:
            focused_input = self.wait.until(
                lambda driver: next(
                    (
                        input_field
                        for input_field in self.get_code_inputs(driver)
                        if input_field.get_attribute("focused") == "true"
                    ),
                    False,
                )
            )
            focused_input.send_keys(digit)

    def enter_partial_code(self, code: str) -> None:
        """Enter one to three digits without triggering OTP validation."""
        if not re.fullmatch(r"\d{1,3}", code):
            raise ValueError("Partial OTP must contain from one to three digits")

        inputs = self.wait.until(
            lambda driver: self.get_code_inputs(driver) or False
        )
        if len(inputs) != 4:
            raise RuntimeError(f"Expected four OTP inputs, received {len(inputs)}")

        for digit in code:
            focused_input = self.wait.until(
                lambda driver: next(
                    (
                        input_field
                        for input_field in self.get_code_inputs(driver)
                        if input_field.get_attribute("focused") == "true"
                    ),
                    False,
                )
            )
            focused_input.send_keys(digit)

    def has_wrong_code_error(self) -> bool:
        return self.is_visible(self.wrong_code_error, timeout=5)

    def get_displayed_debug_code(self) -> str:
        """Возвращает OTP, отображённый приложением на экране подтверждения."""
        return self.wait.until(self._find_displayed_code)

    @staticmethod
    def _find_displayed_code(driver) -> str | bool:
        for element in driver.find_elements(*OtpPage.otp_debug_message):
            match = re.search(r"otpCodeDebug\s*=\s*(\d{4})(?!\d)", element.text)
            if match:
                return match.group(1)
        return False
