import logging
import pickle
import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

#login.py -> scrapers -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COOKIE_FILE = PROJECT_ROOT / "data" / "amazon_cookies.pkl"


def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(options=options)


def auto_login(driver, cookie_file=DEFAULT_COOKIE_FILE):

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

    logger.info("Amazon login successful")
