from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class AuthPage(BasePage):
    """Экран авторизации Sminex.

    Идентификаторы взяты из имеющегося набора Appium-тестов и должны быть
    подтверждены через Appium Inspector на целевой сборке.
    """

    phone_or_email_input = (
        AppiumBy.XPATH,
        "//*[@resource-id='auth_screen_phone_email_input']",
    )
    phone_tab = (AppiumBy.XPATH, "//*[@resource-id='auth_screen_phone_tab']")
    email_tab = (AppiumBy.XPATH, "//*[@resource-id='auth_screen_email_tab']")
    privacy_policy_checkbox = (
        AppiumBy.XPATH,
        "//*[@resource-id='auth_screen_private_policy_checkbox']"
        "//android.widget.CheckBox",
    )
    get_code_button = (
        AppiumBy.XPATH,
        "//*[@resource-id='auth_screen_get_otp_code_button']",
    )
    clear_input_button = (
        AppiumBy.XPATH,
        "//*[@resource-id='auth_screen_clear_input_button']",
    )
    contact_us_button = (
        AppiumBy.XPATH,
        "//*[@resource-id='auth_screen_contact_us_button']",
    )
    invalid_phone_error = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Введён некорректный номер телефона")',
    )
    invalid_email_error = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Введён некорректный email")',
    )
    required_field_error = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Поле обязательно для заполнения")',
    )
    consent_required_error = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Необходимо согласие")',
    )

    def enter_phone(self, phone: str) -> None:
        # The field displays the Russian +7 prefix itself and expects 10 digits.
        value = phone.removeprefix("+7")
        # This Compose input consumes the first key event after clear().
        self.type_text(self.phone_or_email_input, f"0{value}")

    def enter_email(self, email: str) -> None:
        # The first key event after clear() is lost by this Compose field.
        # A disposable prefix keeps the entered email unchanged on the screen.
        self.type_text(self.phone_or_email_input, f"x{email}")

    def is_opened(self) -> bool:
        return self.is_visible(self.phone_or_email_input)

    def has_all_controls(self) -> bool:
        return all(
            self.is_visible(locator)
            for locator in (
                self.phone_tab,
                self.email_tab,
                self.phone_or_email_input,
                self.privacy_policy_checkbox,
                self.get_code_button,
                self.contact_us_button,
            )
        )

    def switch_to_email(self) -> None:
        self.click(self.email_tab)

    def switch_to_phone(self) -> None:
        self.click(self.phone_tab)

    def accept_privacy_policy(self) -> None:
        checkbox = self.wait.until(
            lambda driver: driver.find_element(*self.privacy_policy_checkbox)
        )
        if checkbox.get_attribute("checked") == "true":
            return

        checkbox.click()
        self.wait.until(
            lambda driver: driver.find_element(*self.privacy_policy_checkbox).get_attribute(
                "checked"
            )
            == "true"
        )

    def can_request_otp(self) -> bool:
        return self.is_enabled(self.get_code_button)

    def request_otp(self) -> None:
        self.click(self.get_code_button)

    def clear_phone_or_email(self) -> None:
        self.click(self.clear_input_button)

    def reset_form(self) -> None:
        """Restore the neutral phone-login form without restarting the app."""
        self.click(self.phone_tab)
        clear_buttons = self.driver.find_elements(*self.clear_input_button)
        if clear_buttons and clear_buttons[0].is_displayed():
            clear_buttons[0].click()

        checkbox = self.wait.until(
            lambda driver: driver.find_element(*self.privacy_policy_checkbox)
        )
        if checkbox.get_attribute("checked") == "true":
            checkbox.click()
            self.wait.until(
                lambda driver: driver.find_element(
                    *self.privacy_policy_checkbox
                ).get_attribute("checked")
                != "true"
            )

    def phone_or_email_value(self) -> str:
        element = self.wait.until(
            lambda driver: driver.find_element(*self.phone_or_email_input)
        )
        return element.text

    def open_contact_support(self) -> None:
        previous_ui = self.driver.page_source
        self.click(self.contact_us_button)
        self.wait.until(
            lambda driver: driver.current_package != "com.sminex.sminex_app"
            or driver.page_source != previous_ui
        )

    def has_invalid_phone_error(self) -> bool:
        return self.is_visible(self.invalid_phone_error)

    def has_invalid_email_error(self) -> bool:
        return self.is_visible(self.invalid_email_error)

    def has_required_field_error(self) -> bool:
        return self.is_visible(self.required_field_error)

    def has_consent_required_error(self) -> bool:
        return self.is_visible(self.consent_required_error)

    def is_privacy_policy_accepted(self) -> bool:
        checkbox = self.wait.until(
            lambda driver: driver.find_element(*self.privacy_policy_checkbox)
        )
        return checkbox.get_attribute("checked") == "true"
