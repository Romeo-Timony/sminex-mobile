import pytest
import allure

@allure.epic("UI Автотесты")
@allure.feature("User is prompted to create a new password")
@allure.id("22")
def test_user_is_prompted_to_create_a_new_password():
    """
    Предусловия: 
    """
    with allure.step("{'action': '1. Click on the reset link.', 'expected': 'Шаг должен быть выполнен успешно.'}"):
        pass  # TODO: Реализовать шаг
    with allure.step("{'action': '2. Confirm that the user is prompted to create a new password.', 'expected': 'Шаг должен быть выполнен успешно.'}"):
        pass  # TODO: Реализовать шаг
