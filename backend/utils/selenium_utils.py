import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def create_driver(headless: bool = True, logging: bool = False, logging_mode: str = "debug"):
    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("-headless")

    if logging:
        service = webdriver.FirefoxService(log_output=subprocess.STDOUT, service_args=["--log", logging_mode])

        driver = webdriver.Firefox(options=options, service=service)
    else:
        driver = webdriver.Firefox(options=options)

    return driver


def fetch_html(driver: webdriver.Firefox, url: str, locator: (By, str), timeout: int = 10):
    driver.get(url)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(locator)
    )
    return str(driver.page_source)
