import pytest
import allure

from pages.auth_page import AuthPage


INVALID_PHONE_FORMATS = ("+70000000000", "abc")
INVALID_PHONE_LENGTHS = ("+7909", "+790979229990")
INVALID_EMAILS = (
    "email",
    "user@",
    "@example.ru",
    "user@@example.ru",
    "user name@example.ru",
)


@pytest.mark.ui
@allure.epic("Авторизация")
@allure.feature("Экран авторизации")
class TestAuthScreen:
    """Позитивные и негативные UI-проверки основного экрана авторизации."""

    @pytest.mark.smoke
    @pytest.mark.positive
    @allure.id("AUTH-001")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("[AUTH-001] Экран авторизации — открытие — экран отображается")
    def test_authorization_screen_is_opened(self, auth_form_driver):
        assert AuthPage(auth_form_driver).is_opened()

    @pytest.mark.positive
    @allure.id("AUTH-002")
    @allure.title("[AUTH-002] Экран авторизации — загрузка — отображаются основные элементы")
    def test_authorization_screen_contains_all_main_controls(self, auth_form_driver):
        assert AuthPage(auth_form_driver).has_all_controls()

    @pytest.mark.positive
    @allure.title("[AUTH-003] Экран авторизации — выбор входа по email — отображается поле email")
    def test_authorization_user_can_switch_to_email_tab(self, auth_form_driver):
        auth_page = AuthPage(auth_form_driver)

        auth_page.switch_to_email()

        assert auth_page.is_visible(auth_page.phone_or_email_input)

    @pytest.mark.positive
    @allure.title("[AUTH-004] Экран авторизации — возврат к входу по телефону — отображается поле телефона")
    def test_authorization_user_can_switch_back_to_phone_tab(self, auth_form_driver):
        auth_page = AuthPage(auth_form_driver)
        auth_page.switch_to_email()

        auth_page.switch_to_phone()

        assert auth_page.is_opened()

    @pytest.mark.positive
    @allure.title("[AUTH-005] Экран авторизации — очистка телефона — поле становится пустым")
    def test_authorization_clear_button_removes_entered_phone(
        self, auth_form_driver, test_user
    ):
        auth_page = AuthPage(auth_form_driver)
        auth_page.enter_phone(test_user.phone)

        auth_page.clear_phone_or_email()

        assert not auth_page.phone_or_email_value()

    @pytest.mark.negative
    @allure.title("[AUTH-006] Экран авторизации — отправка пустого телефона — отображается информер обязательного поля")
    def test_authorization_empty_phone_shows_required_informer(self, auth_form_driver):
        auth_page = AuthPage(auth_form_driver)

        auth_page.request_otp()

        assert auth_page.has_required_field_error()

    @pytest.mark.negative
    @allure.title("[AUTH-007] Экран авторизации — отправка пустого email — отображается информер обязательного поля")
    def test_authorization_empty_email_shows_required_informer(self, auth_form_driver):
        auth_page = AuthPage(auth_form_driver)
        auth_page.switch_to_email()

        auth_page.request_otp()

        assert auth_page.has_required_field_error()

    @pytest.mark.negative
    @pytest.mark.parametrize("phone", INVALID_PHONE_FORMATS)
    @allure.title("[AUTH-008] Экран авторизации — ввод телефона в неверном формате — отображается ошибка валидации")
    def test_authorization_invalid_phone_shows_validation_error(
        self, auth_form_driver, phone
    ):
        auth_page = AuthPage(auth_form_driver)
        auth_page.enter_phone(phone)
        auth_page.request_otp()

        assert auth_page.has_invalid_phone_error()

    @pytest.mark.negative
    @pytest.mark.parametrize("phone", INVALID_PHONE_LENGTHS)
    @allure.title("[AUTH-009] Экран авторизации — ввод телефона неверной длины — отображается ошибка валидации")
    def test_authorization_invalid_phone_length_shows_validation_error(
        self, auth_form_driver, phone
    ):
        auth_page = AuthPage(auth_form_driver)
        auth_page.enter_phone(phone)
        auth_page.request_otp()

        assert auth_page.has_invalid_phone_error()

    @pytest.mark.negative
    @pytest.mark.parametrize("email", INVALID_EMAILS)
    @allure.title("[AUTH-010] Экран авторизации — ввод некорректного email — отображается ошибка валидации")
    def test_authorization_invalid_email_shows_validation_error(
        self, auth_form_driver, email
    ):
        auth_page = AuthPage(auth_form_driver)
        auth_page.switch_to_email()
        auth_page.enter_email(email)
        auth_page.request_otp()

        assert auth_page.has_invalid_email_error()

    @pytest.mark.negative
    @allure.title("[AUTH-011] Экран авторизации — отправка телефона без согласия — отображается информер согласия")
    def test_authorization_phone_without_consent_shows_validation_error(
        self, auth_form_driver, test_user
    ):
        auth_page = AuthPage(auth_form_driver)
        auth_page.enter_phone(test_user.phone)
        auth_page.request_otp()

        assert auth_page.has_consent_required_error()

    @pytest.mark.positive
    @allure.title("[AUTH-012] Экран авторизации — принятие политики — согласие отмечено")
    def test_authorization_user_can_accept_privacy_policy(self, auth_form_driver):
        auth_page = AuthPage(auth_form_driver)

        auth_page.accept_privacy_policy()

        assert auth_page.is_privacy_policy_accepted()

    @pytest.mark.regression
    @pytest.mark.positive
    @allure.title("[AUTH-013] Экран авторизации — обращение в поддержку — открывается действие поддержки")
    def test_authorization_contact_support_opens_support_action(self, auth_form_driver):
        auth_page = AuthPage(auth_form_driver)

        auth_page.open_contact_support()
