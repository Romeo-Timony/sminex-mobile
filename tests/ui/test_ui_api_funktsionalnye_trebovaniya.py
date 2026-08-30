import pytest
import allure

@pytest.mark.jira("KAN-1")
@pytest.mark.qase("0")
@pytest.mark.ui
@allure.epic("UI Автотесты")
@allure.feature("[API] Функциональные требования")
@allure.issue("https://romeo-timony.atlassian.net/browse/KAN-1", "KAN-1")
@allure.id("0")
def test_api_funktsionalnye_trebovaniya():
    """
    Jira Ticket: KAN-1 (https://romeo-timony.atlassian.net/browse/KAN-1)
    Qase Case ID: 0
    Предусловия: Переход на страницу с обязательными функциональными требованиями к разрабатываемой системе или приложению.
    """
    with allure.step("Нажать на ссылку с функциональными требованиями."):
        # Ожидаемый результат: Открытие страницы с функциональными требованиями.
        pass  # TODO: Реализовать логику шага
    with allure.step("Ознакомиться с перечнем обязательных требований."):
        # Ожидаемый результат: Понимание обязательных функциональных требований к разрабатываемой системе или приложению.
        pass  # TODO: Реализовать логику шага
