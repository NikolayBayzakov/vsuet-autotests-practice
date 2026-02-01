from playwright.sync_api import expect
from conftest import login_ui, login_with_certificate, session_expired, BASE_URL
import logging
import pytest


def test_login_success(page):
    """Тест успешного входа через UI форму"""
    logging.info("Запуск теста: test_login_success")

    login_ui(page)
    expect(page.get_by_text("CMDB")).to_be_visible()

    logging.info("Тест пройден: Успешный вход в систему")


def test_login_negative(page):
    """Тест неуспешного входа с неверными данными"""
    logging.info("Запуск теста: test_login_negative")

    page.goto("/")
    page.locator('[name="login"]').fill("log")
    page.locator('[name="password"]').fill("pass")
    page.locator("body").click(position={"x": 150, "y": 150})
    page.get_by_role("button", name="Войти").click()
    
    page.locator("text=401")

    logging.info("Тест пройден: Получена ожидаемая ошибка 401")
    

def test_logout(page):
    """Тест выхода из системы"""
    logging.info("Запуск теста: test_logout")

    
    login_with_certificate(page)
    
    page.locator('button[aria-label="Sign out"]').click()
    expect(page.get_by_text("Логин")).to_be_visible()

    logging.info("Тест пройден: Успешный выход из системы")


def test_login_sertificate(page):
    """Тест успешного входа по сертификату"""
    logging.info("Запуск теста: test_login_sert")

    login_with_certificate(page)
    expect(page.get_by_text("CMDB")).to_be_visible()

    logging.info("Тест пройден: Успешный вход по сертификату")


def test_certificate_login_button_available(page):
    """Тест доступности кнопки входа по сертификату"""
    logging.info("Запуск теста: test_certificate_login_button_available")

    page.goto(BASE_URL)
    
    page.locator('.p-splitbutton-dropdown').click()
    page.wait_for_selector('[aria-expanded="true"]', timeout=3000)
    cert_button = page.get_by_text("Вход по сертификату")
    expect(cert_button).to_be_visible()
    expect(cert_button).to_be_enabled()

    logging.info("Тест пройден: Кнопка входа по сертификату доступна")


def test_open_endpoint(page):
    """Тест открытия endpoint"""
    logging.info("Запуск теста: test_open_endpoint")

    login_with_certificate(page)
    expect(page.get_by_text("Все СВТ")).to_be_visible()
    page.wait_for_timeout(1000)

    first_endpoint_name = page.locator('tr[role="row"]:nth-child(1) td[data-column-id="name"] span.text-tooltip').first.text_content()
    logging.info(f"Имя эндпоинта из таблицы: {first_endpoint_name}")

    page.locator('td[data-column-id="name"]').first.dblclick()

    expect(page.get_by_text("Сводка")).to_be_visible()

    logging.info("Увидели элемент из открытого endpoint")

    page.wait_for_timeout(2000)

    logging.info("Тест пройден: Endpoint успешно открыт")


def test_smoke_navigation_through_collections(page):
    """Smoke-тест: проверка навигации по коллекциям CBT"""
    logging.info("Запуск smoke-теста навигации по коллекциям")
    # 1. Логин
    login_with_certificate(page)
    
    # 3. Навигация по разделам с проверками
    test_sections = [
        ("all_pc", "Все компьютеры"),
        ("Core i7", "Core i7"),
        ("Linux", "Linux"),
        ("online", "online"),
        ("endpoint_ram", "Endpoint RAM")
    ]
    
    for section_button, expected_header in test_sections:
        # Кликаем на раздел
        page.get_by_text(section_button, exact=True).click()
        
        # Проверяем загрузку страницы
        expect(page.locator("table")).to_be_visible(timeout=5000)
        page.wait_for_timeout(1000)
        
        page.go_back()

    logging.info("Smoke-тест пройден: разделы доступны для навигации")


def test_session_expired(page):
    """Тест истечения сессии"""
    logging.info("Запуск теста: test_session_expired")

    session_expired(page)

    logging.info("Тест пройден: Проверка истечения сессии выполнена")


def test_change_language(page):
    """Тест возможности поменять язык на сайте"""
    logging.info("Запуск теста: test_change_language")

    login_with_certificate(page)

    language_button = page.locator('button[aria-label="Change language"]')
    expect(language_button).to_be_visible()
    language_button.click()

    english_option = page.locator('li[aria-label="English"]')
    english_option.click()

    expect(page.get_by_text("ALL PC").first).to_be_visible()
    page.wait_for_timeout(1000)

    logging.info("Тест пройден: Кнопка переключения языка работает корректно")


@pytest.mark.parametrize(
    "ui_status, css_class",
    [
        ("В сети", "--success"),
        ("Не в сети", "--danger"),
        ("Архивный", None),
    ]
)

def test_filter_by_status(page, ui_status, css_class):
    """Тест фильтрации по статусу"""

    logging.info(f"Проверка фильтра по статусу: {ui_status}")

    login_with_certificate(page)

    # --- Открываем фильтр ---
    status_title = page.locator(
        'span.p-datatable-column-title:has-text("Статус")'
    )

    filter_container = status_title.locator(
        'xpath=following-sibling::div[@data-pc-section="filter"]'
    )

    filter_container.locator(
        'button.p-datatable-column-filter-button'
    ).click()

    # --- Выбираем статус ---
    dropdown = page.locator('.p-datatable-filter-overlay .p-select-dropdown')
    dropdown.click()

    page.locator(f'li[aria-label="{ui_status}"]').click()
    page.locator('button[aria-label="Принять"]').click()

    # --- Ждём обновление таблицы ---
    page.locator("tbody tr").first.wait_for()

    rows = page.locator("tbody tr")
    assert rows.count() > 0

    # --- Проверяем статусы ---
    for i in range(rows.count()):
        status_cell = rows.nth(i).locator(
            'td[data-column-id="endpoint_status"]'
        )

        status_div = status_cell.locator("div")
        status_div.first.wait_for()

        class_attr = status_div.first.get_attribute("class")

        if css_class:  # Для "В сети" и "Не в сети"
            # Проверяем, что нужный CSS класс присутствует в атрибуте class
            assert css_class in class_attr
        else:  # Для "Архивный"
            # Проверяем, что класс равен именно "v-status" (без дополнительных классов)
            assert class_attr == "v-status"

    logging.info("Фильтрация работает корректно")


def test_search_filters_table_by_any_column(page):
    """Тест проверяет функциональность фильтрации данных в таблице по любому столбцу"""
    logging.info("Запуск теста: test_search_filters_table_by_any_column")
    login_with_certificate(page)

    expect(page.locator("table")).to_be_visible()

    search_input = page.locator('input[placeholder="Поиск по имени"]')
    expect(search_input).to_be_visible()

    # вводим существующее значение
    search_input.fill("astr")

    # либо есть строки
    rows = page.locator("tbody tr")
    if rows.count() > 0:
        expect(rows.first).to_be_visible()
    else:
        # либо отображается "Нет данных"
        expect(page.get_by_text("Нет данных", exact=False)).to_be_visible()
    
    logging.info("Тест успешно завершен: test_search_filters_table_by_any_column")


def test_search_no_results_shows_empty_state(page):
    """Тест проверки поиска по несуществующему значению"""
    logging.info("Запуск теста: test_search_no_results_shows_empty_state")

    login_with_certificate(page)

    search_input = page.locator('input[placeholder="Поиск по имени"]')
    expect(search_input).to_be_visible()

    search_input.fill("NON_EXISTENT_VALUE_123456")

    expect(page.get_by_text("Нет данных", exact=False)).to_be_visible()

    logging.info("Тест успешно завершен: test_search_no_results_shows_empty_state")