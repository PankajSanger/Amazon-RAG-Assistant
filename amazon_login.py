from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pickle
import os


def get_driver():
    options = Options()
    options.add_argument("--start-maximized") 
    options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(options=options)


def auto_login(driver, cookie_file="amazon_cookies.pkl"):

    if not os.path.exists(cookie_file):
        raise FileNotFoundError(
            f"{cookie_file} not found."
        )

    driver.get("https://www.amazon.in/")

    with open(cookie_file, "rb") as f:
        cookies = pickle.load(f)

    for cookie in cookies:
        driver.add_cookie(cookie)

    driver.refresh()

    print("Amazon login successful")
