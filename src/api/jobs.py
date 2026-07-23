import logging
import threading
import uuid
from io import BytesIO

import pandas as pd

from src.scrapers.login import get_driver, auto_login, AutoLoginError
from src.scrapers.product_page import scrape_products
from src.scrapers.keyword_search import search_scrape
from src.scrapers.reviews import scrape_reviews
from src.storage.database import save_products, save_reviews

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_JOBS: dict[str, dict] = {}

PREVIEW_ROWS = 20


def _new_job():
    return {
        "status": "queued",
        "progress": 0,
        "message": "Queued",
        "product_count": 0,
        "review_count": 0,
        "products_preview": [],
        "reviews_preview": [],
        "error": None,
        "excel_bytes": None,
    }


def create_job():
    job_id = str(uuid.uuid4())
    with _LOCK:
        _JOBS[job_id] = _new_job()
    return job_id


def get_job(job_id):
    with _LOCK:
        job = _JOBS.get(job_id)
        return dict(job) if job else None


def _update(job_id, **fields):
    with _LOCK:
        if job_id in _JOBS:
            _JOBS[job_id].update(fields)


def _preview(df):
    if df is None or df.empty:
        return []
    return df.head(PREVIEW_ROWS).where(pd.notnull(df.head(PREVIEW_ROWS)), None).to_dict("records")


def start_job(job_id, params):
    thread = threading.Thread(target=_run_job, args=(job_id, params), daemon=True)
    thread.start()


def _run_job(job_id, params):
    _update(job_id, status="running", message="Logging into Amazon...", progress=10)

    driver = get_driver()

    try:
        auto_login(driver)

        urls = params.get("urls") or []

        if params["input_type"] == "keyword":
            _update(job_id, message=f"Searching keyword '{params['keyword']}'...", progress=25)

            search_results = search_scrape(
                driver=driver,
                keyword=params["keyword"],
                pages=params["pages"]
            )

            search_df = pd.DataFrame(search_results)
            urls = search_df["URL"].dropna().tolist() if "URL" in search_df.columns else []

            _update(job_id, message=f"{len(urls)} products found", progress=40)

        product_df = None
        review_df = None

        if params["scrape_products"]:
            _update(job_id, message=f"Scraping product details for {len(urls)} products...", progress=55)

            product_data = scrape_products(driver=driver, urls=urls)
            product_df = pd.DataFrame(product_data)

            saved_count = save_products(product_df)

            _update(
                job_id,
                product_count=saved_count,
                products_preview=_preview(product_df),
            )

        if params["scrape_reviews"]:
            _update(job_id, message=f"Scraping customer reviews for {len(urls)} products...", progress=80)

            review_df = scrape_reviews(driver=driver, product_urls=urls)

            saved_review_count = save_reviews(review_df)

            _update(
                job_id,
                review_count=saved_review_count,
                reviews_preview=_preview(review_df),
            )

        _update(job_id, message="Preparing Excel file...", progress=95)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            if product_df is not None:
                product_df.to_excel(writer, sheet_name="Products", index=False)
            if review_df is not None:
                review_df.to_excel(writer, sheet_name="Reviews", index=False)

        _update(
            job_id,
            status="done",
            progress=100,
            message="Scraping completed successfully!",
            excel_bytes=output.getvalue(),
        )

    except FileNotFoundError as exc:
        logger.warning("Missing cookie file: %s", exc)
        _update(job_id, status="error", error=str(exc), message="Scraping failed")

    except AutoLoginError as exc:
        logger.warning("Amazon auto-login failed: %s", exc)
        _update(job_id, status="error", error=str(exc), message="Scraping failed")

    except Exception as exc:
        logger.exception("Scraping run failed")
        _update(job_id, status="error", error=str(exc), message="Scraping failed")

    finally:
        driver.quit()
