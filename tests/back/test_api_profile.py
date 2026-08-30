import pytest
import allure
import requests

@allure.epic("API Автотесты")
@allure.feature("Получение информации о профиле пользователя")
@allure.id("AS-102")
def test_get_user_profile():
    """
    Предусловия: Пользователь авторизован.
    """
    with allure.step("Отправить GET запрос на /api/v1/profile с токеном авторизации"):
        # В реальности: response = requests.get(f'{URL}/api/v1/profile', headers=headers)
        pass
        
    with allure.step("Проверить, что статус ответа равен 200"):
        # В реальности: assert response.status_code == 200
        pass
        
    with allure.step("Проверить, что в теле ответа присутствуют поля 'username' и 'email'"):
        # В реальности: assert 'username' in response.json()
        pass
