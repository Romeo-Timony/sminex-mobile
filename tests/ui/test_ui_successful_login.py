import pytest
import allure

@allure.epic("UI Автотесты")
@allure.feature("Успешная авторизация пользователя")
@allure.id("AS-101")
def test_successful_login():
    """
    Предусловия: Пользователь зарегистрирован в системе.
    """
    with allure.step("Открыть страницу авторизации"):
        pass  # В реальности: page.goto('/login')
        
    with allure.step("Ввести логин 'test_user' и пароль 'password123'"):
        pass  # В реальности: page.fill('#username', 'test_user'), page.fill('#password', 'password123')
        
    with allure.step("Нажать кнопку 'Войти'"):
        pass  # В реальности: page.click('#submit')
        
    with allure.step("Проверить, что отображается главная страница"):
        pass  # В реальности: expect(page.locator('#dashboard')).to_be_visible()
