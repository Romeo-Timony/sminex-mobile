from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class UpdateDialog(BasePage):
    # The third-party update dialog has no stable resource ID.
    postpone_button = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Позже")')

    def postpone_if_opened(self) -> bool:
        button = self.find_optional(self.postpone_button, timeout=10)
        if not button:
            return False
        button.click()
        return True
