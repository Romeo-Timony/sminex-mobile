import pytest
import allure

@pytest.mark.review
@pytest.mark.jira("KAN-1")
@pytest.mark.qase("0")
@pytest.mark.ui
@allure.epic("UI Автотесты (На ревью)")
@allure.feature("[UI] Test 1")
@allure.issue("https://romeo-timony.atlassian.net/browse/KAN-1", "KAN-1")
@allure.id("0")
def test_ui_test_1():
    """
    [НА РЕВЬЮ]
    Jira Ticket: KAN-1 (https://romeo-timony.atlassian.net/browse/KAN-1)
    Qase Case ID: 0
    Предусловия: Не указаны
    """
    with allure.step("Step 1"):
        # Ожидаемый результат: Result 1
        pass  # TODO: Реализовать логику шага
