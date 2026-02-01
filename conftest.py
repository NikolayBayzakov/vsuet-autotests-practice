import os
import pytest

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

import logging
from logging_config import setup_logging

from datetime import datetime
from pathlib import Path

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "https://demo.u-system.tech")
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
CERT_PFX_PATH = os.getenv("CERT_PFX_PATH")
CERT_PFX_PASSWORD = os.getenv("CERT_PFX_PASSWORD", "")


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        yield b
        b.close()


def _new_context(browser):
    if CERT_PFX_PATH:
        return browser.new_context(
            base_url=BASE_URL,
            ignore_https_errors=True,
            client_certificates=[{
                "origin": BASE_URL,
                "pfxPath": CERT_PFX_PATH,
                "passphrase": CERT_PFX_PASSWORD,
            }],
        )
    return browser.new_context(base_url=BASE_URL, ignore_https_errors=True)


@pytest.fixture()
def page(browser):
    ctx = _new_context(browser)
    page = ctx.new_page()
    yield page
    ctx.close()


def pytest_configure(config):
    """Вызывается при старте тестов"""
    logger, log_file = setup_logging()
    logging.info(f"Начало выполнения тестов")
    logging.info(f"Лог файл: {log_file}")


def pytest_sessionfinish(session, exitstatus):
    """Вызывается при завершении тестов"""
    logging.info(f"Завершение выполнения тестов. Статус: {exitstatus}")


@pytest.fixture(scope="function")
def logger():
    """Фикстура для получения логгера в тестах"""
    return logging.getLogger()


def login_ui(page):
    if not LOGIN or not PASSWORD:
        raise RuntimeError("Set LOGIN/PASSWORD in .env")
    page.goto("/")
    page.locator('[name="login"]').fill(LOGIN)
    page.locator('[name="password"]').fill(PASSWORD)
    page.locator("body").click(position={"x": 150, "y": 150})
    page.get_by_role("button", name="Войти").click()
    expect(page.get_by_text("CMDB")).to_be_visible(timeout=15000)


def login_with_certificate(page):
    if CERT_PFX_PATH:
        page.goto("/")
        page.locator('.p-splitbutton-dropdown').click()
        page.wait_for_selector('[aria-expanded="true"]', timeout=3000)
        page.locator('text=Вход по сертификату').click()
        expect(page.get_by_text("CMDB")).to_be_visible(timeout=15000)


def session_expired(page):
    login_with_certificate(page)
    expect(page.get_by_text("CMDB")).to_be_visible(timeout=15000)

    page.context.clear_cookies()
    page.reload()

    expect(page.get_by_text("Войти")).to_be_visible()
    expect(page.locator('[name="login"]')).to_be_visible()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Хук для работы авто-скриншотов"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    """Автоматический скриншот при падении теста"""
    yield
    
    # Проверяем, упал ли тест на этапе выполнения (call)
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        # Создаем папку
        Path("artifacts/screenshots").mkdir(parents=True, exist_ok=True)
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name = request.node.name.replace("::", "_")  # заменяем :: на _ для имени файла
        path = f"artifacts/screenshots/FAIL_{test_name}_{timestamp}.png"
        
        # Делаем скриншот
        page.screenshot(path=path, full_page=True)
        print(f"📸 Скриншот при падении: {path}")


