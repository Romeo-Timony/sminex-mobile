import pytest
import allure

@allure.epic("UI Автотесты")
@allure.feature("Password reset link is sent to registered email")
@allure.id("21")
def test_password_reset_link_is_sent_to_registered_email():
    """
    Предусловия: 
    """
    with allure.step("{'action': '1. Check the registered email for the password reset link.', 'expected': 'Шаг должен быть выполнен успешно.'}"):
        pass  # TODO: Реализовать шаг
    with allure.step("{'action': '2. Verify that the link is valid and not expired.', 'expected': 'Шаг должен быть выполнен успешно.'}"):
        pass  # TODO: Реализовать шаг
