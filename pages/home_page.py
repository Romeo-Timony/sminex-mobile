from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class HomePage(BasePage):
    # The current Compose build does not expose resource IDs on main-screen
    # navigation and cards. Exact UI text is the least fragile available fallback.
    home_tab = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Главная")')
    purchases_tab = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Мои покупки")',
    )
    payments_tab = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Платежи")')
    privileges_tab = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Привилегии")',
    )
    next_payment_card = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Ближайший платёж")',
    )
    construction_progress_card = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Динамика строительства")',
    )
    contact_manager_card = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Связаться с менеджером")',
    )

    def is_opened(self, timeout: int = 20) -> bool:
        return self.is_visible(self.home_tab, timeout=timeout)

    def has_bottom_navigation(self) -> bool:
        return all(
            self.is_visible(locator)
            for locator in (
                self.home_tab,
                self.purchases_tab,
                self.payments_tab,
                self.privileges_tab,
            )
        )

    def has_primary_cards(self) -> bool:
        return all(
            self.is_visible(locator)
            for locator in (
                self.next_payment_card,
                self.construction_progress_card,
                self.contact_manager_card,
            )
        )

    def is_contact_manager_available(self) -> bool:
        """Return whether the contact-manager action is visible and enabled."""
        return self.is_visible(self.contact_manager_card) and self.is_enabled(
            self.contact_manager_card
        )

    def contact_manager_label(self) -> str:
        return self.wait.until(
            lambda driver: driver.find_element(*self.contact_manager_card)
        ).text
