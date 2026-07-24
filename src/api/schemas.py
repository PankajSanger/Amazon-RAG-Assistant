from typing import Any, Literal, Optional

from pydantic import BaseModel


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]


class ReindexResponse(BaseModel):
    indexed_count: int


class StatsResponse(BaseModel):
    product_count: int
    review_count: int
    avg_product_rating: Optional[float]
    avg_review_rating: Optional[float]
    rating_distribution: dict[str, int]


class ScrapeJobCreated(BaseModel):
    job_id: str


JobStatus = Literal["queued", "running", "done", "error"]


class ScrapeJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    message: str
    product_count: int
    review_count: int
    products_preview: list[dict[str, Any]]
    reviews_preview: list[dict[str, Any]]
    live_review_count: int = 0
    current_product: Optional[str] = None
    latest_review: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    download_ready: bool


class ClearDatabaseRequest(BaseModel):
    password: str


class ClearDatabaseResponse(BaseModel):
    products_cleared: int
    reviews_cleared: int


class UploadCookiesResponse(BaseModel):
    cookie_count: int
