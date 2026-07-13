from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def search_scrape(driver, keyword, pages=1):

    results = []

    # Open Amazon homepage
    driver.get("https://www.amazon.in")

    # Search
    search_box = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "twotabsearchtextbox"))
    )

    search_box.clear()
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.ENTER)

    for page in range(1, pages + 1):

        print(f"Scraping page {page}")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-component-type="s-search-result"]')
            )
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        products = soup.select(
            '[data-component-type="s-search-result"]'
        )

        for product in products:

            asin = product.get("data-asin")

            if not asin:
                continue

            # Title
            title_tag = product.select_one("h2 span")
            title = title_tag.get_text(strip=True) if title_tag else None

            # Product URL
            url = f"https://www.amazon.in/dp/{asin}"

            # Rating
            rating_tag = product.select_one("span.a-icon-alt")
            rating = (
                rating_tag.get_text(strip=True).split()[0]
                if rating_tag
                else None
            )

            # Number of Ratings
            ratings_elem = product.select_one(
                'a[aria-label*="ratings"]'
            )

            no_of_ratings = None

            if ratings_elem:
                no_of_ratings = (
                    ratings_elem["aria-label"]
                    .replace(" ratings", "")
                    .replace(",", "")
                )

            results.append(
                {
                    "Title": title,
                    "Rating": rating,
                    "No_of_Ratings": no_of_ratings,
                    "URL": url
                }
            )

        # Go to next page
        if page < pages:

            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "a.s-pagination-next")
                    )
                )

                driver.execute_script(
                    "arguments[0].click();",
                    next_button
                )

            except Exception:
                print("No more pages available")
                break

    return results