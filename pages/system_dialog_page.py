from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class SystemDialogPage(BasePage):
    allow_notifications_button = (
        AppiumBy.ID,
        "com.android.permissioncontroller:id/permission_allow_button",
    )

    def allow_notifications_if_requested(self) -> bool:
        button = self.find_optional(self.allow_notifications_button, timeout=10)
        if not button:
            return False
        button.click()
        return True
