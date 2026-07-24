# amazon_review_scraper.py

import logging
import re

import pandas as pd

from bs4 import BeautifulSoup as soup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


def scrape_reviews(driver, product_urls, on_progress=None):

    data = []

    for idx, raw_url in enumerate(product_urls, start=1):

        logger.info("Scraping reviews %d/%d", idx, len(product_urls))

        match = re.search(
            r'/(?:dp|product-reviews|customer-reviews)/([A-Z0-9]{10})',
            raw_url
        )

        if not match:
            logger.warning("Invalid URL: %s", raw_url)
            continue

        asin = match.group(1)

        review_base_url = (
            f"https://www.amazon.in/product-reviews/{asin}"
        )

        driver.get(review_base_url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-hook="review"]')
                )
            )
        except Exception as exc:
            logger.warning("Reviews not loaded for ASIN %s: %s", asin, exc)
            continue

        page_source = driver.page_source

        if 'data-hook="show-more-button"' in page_source:
            mode = "dynamic"
            logger.info("Mode: Dynamic")
        else:
            mode = "pagination"
            logger.info("Mode: Pagination")

        seen_reviews = set()

        # ==================================================
        # DYNAMIC MODE
        # ==================================================

        if mode == "dynamic":

            while True:

                page_soup = soup(
                    driver.page_source,
                    "html.parser"
                )

                reviews = page_soup.select(
                    '[data-hook="review"]'
                )

                logger.info("Visible Reviews: %d", len(reviews))

                new_count = 0

                for review in reviews:

                    review_data = extract_review(
                        review,
                        asin
                    )

                    if not review_data:
                        continue

                    if review_data["url"] in seen_reviews:
                        continue

                    seen_reviews.add(
                        review_data["url"]
                    )

                    data.append(review_data)

                    new_count += 1

                    if on_progress:
                        on_progress(
                            product_idx=idx,
                            total_products=len(product_urls),
                            asin=asin,
                            total_reviews=len(data),
                            review=review_data,
                        )

                logger.info("New Reviews Added: %d", new_count)

                if new_count == 0:
                    break

                try:

                    button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//a[@data-hook='show-more-button']")
                        )
                    )

                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);",
                        button
                    )

                    driver.execute_script(
                        "arguments[0].click();",
                        button
                    )

                    logger.info("Clicked Show More")

                    previous_review_count = len(reviews)

                    try:
                        WebDriverWait(driver, 10).until(
                            lambda d: len(
                                d.find_elements(By.CSS_SELECTOR, '[data-hook="review"]')
                            ) > previous_review_count
                        )
                    except Exception:
                        #No additional reviews rendered in time - the next
                        #loop iteration's new_count == 0 check ends the scrape.
                        pass

                except Exception as exc:
                    logger.info("No More Reviews: %s", exc)
                    break

        # ==================================================
        # PAGINATION MODE
        # ==================================================

        else:

            page_num = 1

            while True:

                page_url = (
                    f"{review_base_url}"
                    f"?pageNumber={page_num}"
                    f"&sortBy=recent"
                    f"&reviewerType=all_reviews"
                )

                driver.get(page_url)

                try:
                    WebDriverWait(driver, 6).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, '[data-hook="review"]')
                        )
                    )
                except Exception:
                    #Most likely the last page (no reviews) - fall through
                    #and let the empty `reviews` list below end the loop.
                    pass

                page_soup = soup(
                    driver.page_source,
                    "html.parser"
                )

                reviews = page_soup.select(
                    '[data-hook="review"]'
                )

                logger.info(
                    "ASIN %s | Page %d | Reviews: %d",
                    asin, page_num, len(reviews)
                )

                if not reviews:
                    break

                new_count = 0

                for review in reviews:

                    review_data = extract_review(
                        review,
                        asin
                    )

                    if not review_data:
                        continue

                    if review_data["url"] in seen_reviews:
                        continue

                    seen_reviews.add(
                        review_data["url"]
                    )

                    data.append(review_data)

                    new_count += 1

                    if on_progress:
                        on_progress(
                            product_idx=idx,
                            total_products=len(product_urls),
                            asin=asin,
                            total_reviews=len(data),
                            review=review_data,
                        )

                logger.info(
                    "Page %d | New Reviews: %d",
                    page_num, new_count
                )

                if new_count == 0:
                    break

                page_num += 1

    # ==================================================
    # DATAFRAME
    # ==================================================

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    df = df.drop_duplicates(
        subset=["url"]
    )

    df["guid"] = df["url"]

    columns = [
        "author",
        "rating",
        "url",
        "date",
        "product_name",
        "contents",
        "title",
        "guid"
    ]

    return df[columns]


def extract_review(review, asin):

    try:

        title_tag = review.find(
            "a",
            {"data-hook": "review-title"}
        )

        review_url = (
            "https://www.amazon.in"
            + title_tag["href"]
        )

        title = title_tag.get_text(
            strip=True
        )

    except Exception as exc:
        logger.warning("Skipping review for ASIN %s - no title/url: %s", asin, exc)
        return None

    try:

        rating_text = review.find(
            "span",
            class_="a-icon-alt"
        ).get_text()

        rating = float(
            re.search(
                r"\d+\.?\d*",
                rating_text
            ).group()
        )

    except Exception as exc:
        logger.debug("No rating found for ASIN %s: %s", asin, exc)
        rating = None

    try:

        author = review.find(
            "span",
            class_="a-profile-name"
        ).get_text(strip=True)

        if len(author) > 50:
            author = "Amazon Customer"

    except Exception as exc:
        logger.debug("No author found for ASIN %s: %s", asin, exc)
        author = "Amazon Customer"

    try:

        date_text = review.find(
            "span",
            {"data-hook": "review-date"}
        ).get_text()

        date_text = (
            date_text
            .replace(
                "Reviewed in India on ",
                ""
            )
            .strip()
        )

        review_date = pd.to_datetime(
            date_text,
            errors="coerce"
        )

    except Exception as exc:
        logger.debug("No date found for ASIN %s: %s", asin, exc)
        review_date = None

    try:

        contents = review.find(
            "span",
            {"data-hook": "review-body"}
        ).get_text(
            " ",
            strip=True
        )

    except Exception as exc:
        logger.debug("No review body found for ASIN %s: %s", asin, exc)
        contents = ""

    return {
        "author": author,
        "rating": rating,
        "url": review_url,
        "date": review_date,
        "product_name": asin,
        "contents": contents,
        "title": title
    }
