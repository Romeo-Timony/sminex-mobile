import pytest
import allure

@allure.epic("E2E Автотесты")
@allure.feature("Сквозной процесс: Покупка товара гостем")
@allure.id("AS-103")
def test_guest_checkout():
    """
    Предусловия: Товар в наличии на складе.
    """
    with allure.step("Добавить товар в корзину"):
        pass
        
    with allure.step("Перейти в корзину и заполнить форму оформления заказа"):
        pass
        
    with allure.step("Выбрать оплату картой при получении"):
        pass
        
    with allure.step("Подтвердить заказ"):
        pass
        
    with allure.step("Проверить в БД создание заказа в статусе 'Новый'"):
        pass
