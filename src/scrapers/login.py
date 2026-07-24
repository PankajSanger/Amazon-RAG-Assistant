import logging
import pickle
import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

#login.py -> scrapers -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COOKIE_FILE = PROJECT_ROOT / "data" / "amazon_cookies.pkl"

ACCOUNT_NAV_SELECTOR = "#nav-link-accountList-nav-line-1"


class AutoLoginError(Exception):
    """Raised when the Amazon session cookies didn't produce a signed-in session."""


def get_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")

    if os.getenv("CHROME_BIN"):
        options.binary_location = os.getenv("CHROME_BIN")

    if os.getenv("SCRAPER_HEADLESS") == "1":
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
    else:
        options.add_argument("--start-maximized")

    return webdriver.Chrome(options=options)


def _is_signed_in(driver, timeout=10):
    try:
        account_nav = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ACCOUNT_NAV_SELECTOR))
        )
        text = account_nav.text.strip().lower()
    except Exception:
        return False

    return "sign in" not in text


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

    if not _is_signed_in(driver):
        raise AutoLoginError(
            "Amazon session appears to be expired or invalid (still showing "
            "'Sign in'). Refresh data/amazon_cookies.pkl by running: "
            "python -m src.scrapers.login"
        )

    logger.info("Amazon login successful")


def save_cookies_interactive(cookie_file=DEFAULT_COOKIE_FILE, timeout=300):
    """Opens a real, visible Chrome window for the user to log into Amazon by
    hand (including any CAPTCHA/2FA), then pickles the resulting session
    cookies to `cookie_file` for auto_login() to reuse. Must be run locally
    with a real display - there is no way to automate a CAPTCHA/2FA
    challenge, so this cannot run headless or inside a container."""

    if os.getenv("SCRAPER_HEADLESS") == "1":
        raise RuntimeError(
            "save_cookies_interactive() needs a visible browser for you to log "
            "in by hand - it can't run with SCRAPER_HEADLESS=1 (e.g. inside "
            "Docker). Run it locally instead: python -m src.scrapers.login"
        )

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.amazon.in/ap/signin")

        print(
            f"Log into Amazon in the opened browser window "
            f"(you have up to {timeout // 60} minutes)..."
        )

        try:
            WebDriverWait(driver, timeout).until(lambda d: _is_signed_in(d, timeout=1))
        except Exception as exc:
            raise AutoLoginError(
                f"Didn't detect a signed-in session within {timeout}s. "
                "Make sure you finished logging in before the timeout."
            ) from exc

        cookie_file = Path(cookie_file)
        cookie_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cookie_file, "wb") as f:
            pickle.dump(driver.get_cookies(), f)

        print(f"Saved Amazon session cookies to {cookie_file}")

    finally:
        driver.quit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    save_cookies_interactive()
