import pytest
import allure
import requests

@pytest.mark.review
@pytest.mark.jira("KAN-1")
@pytest.mark.qase("KAN-1-2")
@pytest.mark.api
@allure.epic("API Автотесты (На ревью)")
@allure.feature("[API] Проверка получения списка пользователей")
@allure.issue("https://romeo-timony.atlassian.net/browse/KAN-1", "KAN-1")
@allure.id("KAN-1-2")
def test_api_proverka_polucheniya_spiska_polzovateley():
    """
    [НА РЕВЬЮ]
    Jira Ticket: KAN-1 (https://romeo-timony.atlassian.net/browse/KAN-1)
    Qase Case ID: KAN-1-2
    Предусловия: Не указаны
    """
    with allure.step("Отправить GET запрос на /api/users"):
        # Ожидаемый результат: Получен статус 200 и список пользователей
        pass  # TODO: Реализовать логику шага
    with allure.step("Проверить структуру ответа"):
        # Ожидаемый результат: Ответ содержит массив пользователей с необходимыми полями
        pass  # TODO: Реализовать логику шага
