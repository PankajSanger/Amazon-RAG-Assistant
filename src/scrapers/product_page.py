import logging
import re

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ASIN_PATTERN = re.compile(r'/(?:dp|product-reviews|customer-reviews)/([A-Z0-9]{10})')


def scrape_product(driver, url):

    driver.get(url)

    page_soup = BeautifulSoup(
        driver.page_source,
        "html.parser"
    )

    all_data = page_soup.find(
        "div",
        class_="centerColAlign"
    )

    if not all_data:
        return None

    match = ASIN_PATTERN.search(url)

    data = {
        "asin": match.group(1) if match else None,
        "url": url
    }

    title = all_data.find("span", id="productTitle")
    data["title"] = title.get_text(strip=True) if title else None

    rating = all_data.find(
        "span",
        class_="a-size-small a-color-base"
    )
    data["rating"] = rating.get_text(strip=True) if rating else None

    reviews = all_data.find(
        "span",
        id="acrCustomerReviewText"
    )
    data["no_of_ratings"] = (
        reviews.get_text(strip=True)
        if reviews
        else None
    )

    price = all_data.find(
        "span",
        class_="a-price-whole"
    )
    data["price"] = (
        price.get_text(strip=True)
        if price
        else None
    )

    about = all_data.find(
        "div",
        id="feature-bullets"
    )

    data["about"] = (
        about.get_text(" ", strip=True)
        if about
        else None
    )

    return data

def scrape_products(driver, urls):

    products = []

    for url in urls:

        try:
            data = scrape_product(driver, url)

            if data:
                products.append(data)

        except Exception:
            logger.exception("Error scraping %s", url)

    return products