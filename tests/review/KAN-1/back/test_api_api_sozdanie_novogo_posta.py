import pytest
import allure
import requests

@pytest.mark.review
@pytest.mark.jira("KAN-1")
@pytest.mark.qase("KAN-1-5")
@pytest.mark.api
@allure.epic("API Автотесты (На ревью)")
@allure.feature("[API] Создание нового поста")
@allure.issue("https://romeo-timony.atlassian.net/browse/KAN-1", "KAN-1")
@allure.id("KAN-1-5")
def test_api_sozdanie_novogo_posta():
    """
    [НА РЕВЬЮ]
    Jira Ticket: KAN-1 (https://romeo-timony.atlassian.net/browse/KAN-1)
    Qase Case ID: KAN-1-5
    Предусловия: Не указаны
    """
    with allure.step("Отправить POST запрос на /api/posts с данными поста"):
        # Ожидаемый результат: Получен статус 201 и данные созданного поста
        pass  # TODO: Реализовать логику шага
