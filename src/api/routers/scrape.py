from io import BytesIO
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.api import jobs
from src.api.schemas import ScrapeJobCreated, ScrapeJobStatusResponse

router = APIRouter(prefix="/api/scrape", tags=["scrape"])


@router.post("/jobs", response_model=ScrapeJobCreated)
async def create_scrape_job(
    input_type: str = Form(...),
    url: Optional[str] = Form(None),
    keyword: Optional[str] = Form(None),
    pages: int = Form(1),
    scrape_products: bool = Form(True),
    scrape_reviews: bool = Form(False),
    file: Optional[UploadFile] = None,
):
    if not scrape_products and not scrape_reviews:
        raise HTTPException(status_code=400, detail="Please select at least one scraping option.")

    if input_type == "keyword":
        if not keyword:
            raise HTTPException(status_code=400, detail="Please enter a keyword.")
        params = {"input_type": "keyword", "keyword": keyword, "pages": pages}

    elif input_type == "file":
        if not file:
            raise HTTPException(status_code=400, detail="Please upload an Excel file.")

        contents = await file.read()
        df_urls = pd.read_excel(BytesIO(contents))

        if "url" not in df_urls.columns:
            raise HTTPException(status_code=400, detail="Excel file must contain a column named 'url'")

        urls = df_urls["url"].dropna().tolist()

        if not urls:
            raise HTTPException(status_code=400, detail="Please provide URL(s).")

        params = {"input_type": "file", "urls": urls}

    else:
        if not url:
            raise HTTPException(status_code=400, detail="Please provide URL(s).")

        params = {"input_type": "single", "urls": [url]}

    params["scrape_products"] = scrape_products
    params["scrape_reviews"] = scrape_reviews

    job_id = jobs.create_job()
    jobs.start_job(job_id, params)

    return ScrapeJobCreated(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=ScrapeJobStatusResponse)
def get_scrape_job(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return ScrapeJobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        product_count=job["product_count"],
        review_count=job["review_count"],
        products_preview=job["products_preview"],
        reviews_preview=job["reviews_preview"],
        live_review_count=job["live_review_count"],
        current_product=job["current_product"],
        latest_review=job["latest_review"],
        error=job["error"],
        download_ready=job["excel_bytes"] is not None,
    )


@router.get("/jobs/{job_id}/download")
def download_scrape_job(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "done" or job["excel_bytes"] is None:
        raise HTTPException(status_code=409, detail="Job is not finished yet")

    return StreamingResponse(
        BytesIO(job["excel_bytes"]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=amazon_scraper_output.xlsx"},
    )
