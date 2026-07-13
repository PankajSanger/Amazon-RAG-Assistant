# amazon_review_scraper.py

import pandas as pd
import time
import re

from bs4 import BeautifulSoup as soup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_reviews(driver, product_urls):

    data = []

    for idx, raw_url in enumerate(product_urls, start=1):

        print(f"\nScraping reviews {idx}/{len(product_urls)}")

        match = re.search(
            r'/(?:dp|product-reviews|customer-reviews)/([A-Z0-9]{10})',
            raw_url
        )

        if not match:
            print(f"Invalid URL: {raw_url}")
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
        except Exception:
            print(f"Reviews not loaded for ASIN: {asin}")
            continue

        page_source = driver.page_source

        if 'data-hook="show-more-button"' in page_source:
            mode = "dynamic"
            print("Mode: Dynamic")
        else:
            mode = "pagination"
            print("Mode: Pagination")

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

                print(f"Visible Reviews: {len(reviews)}")

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

                print(f"New Reviews Added: {new_count}")

                if new_count == 0:
                    break

                try:

                    button = driver.find_element(
                        By.XPATH,
                        "//a[@data-hook='show-more-button']"
                    )

                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);",
                        button
                    )

                    time.sleep(1)

                    driver.execute_script(
                        "arguments[0].click();",
                        button
                    )

                    print("Clicked Show More")

                    time.sleep(3)

                except Exception:
                    print("No More Reviews")
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

                time.sleep(2)

                page_soup = soup(
                    driver.page_source,
                    "html.parser"
                )

                reviews = page_soup.select(
                    '[data-hook="review"]'
                )

                print(
                    f"ASIN {asin} | "
                    f"Page {page_num} | "
                    f"Reviews: {len(reviews)}"
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

                print(
                    f"Page {page_num} | "
                    f"New Reviews: {new_count}"
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

    except Exception:
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

    except Exception:
        rating = None

    try:

        author = review.find(
            "span",
            class_="a-profile-name"
        ).get_text(strip=True)

        if len(author) > 50:
            author = "Amazon Customer"

    except Exception:
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

    except Exception:
        review_date = None

    try:

        contents = review.find(
            "span",
            {"data-hook": "review-body"}
        ).get_text(
            " ",
            strip=True
        )

    except Exception:
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