import io
import logging
import os
import pickle
import secrets

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.rag.pipeline import clear_collections
from src.scrapers.login import DEFAULT_COOKIE_FILE
from src.storage.database import clear_all
from src.api.schemas import ClearDatabaseRequest, ClearDatabaseResponse, UploadCookiesResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


class _RestrictedUnpickler(pickle.Unpickler):
    """Refuses to construct any class/function reference while unpickling -
    only plain dict/list/str/int/float/bool/None values are allowed. Cookie
    files are just lists of plain dicts, so this fully covers the legitimate
    shape while blocking arbitrary code execution from an uploaded file."""

    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"Refusing to unpickle {module}.{name}")


def _safe_load_cookies(data: bytes) -> list[dict]:
    try:
        cookies = _RestrictedUnpickler(io.BytesIO(data)).load()
    except Exception as exc:
        raise ValueError(f"Not a valid cookie file: {exc}") from exc

    if not isinstance(cookies, list) or not cookies:
        raise ValueError("Cookie file must contain a non-empty list of cookies.")

    for cookie in cookies:
        if not isinstance(cookie, dict) or "name" not in cookie or "value" not in cookie:
            raise ValueError("Cookie file contains an invalid cookie entry.")

    return cookies


@router.post("/clear-database", response_model=ClearDatabaseResponse)
def clear_database(request: ClearDatabaseRequest):
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_password:
        raise HTTPException(
            status_code=503,
            detail="Clear-database is disabled (ADMIN_PASSWORD is not configured on the server).",
        )

    if not secrets.compare_digest(request.password, admin_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    products_cleared, reviews_cleared = clear_all()
    clear_collections()

    logger.warning(
        "Database cleared via admin endpoint: %d product(s), %d review(s)",
        products_cleared,
        reviews_cleared,
    )

    return ClearDatabaseResponse(products_cleared=products_cleared, reviews_cleared=reviews_cleared)


@router.post("/upload-cookies", response_model=UploadCookiesResponse)
async def upload_cookies(password: str = Form(...), file: UploadFile = File(...)):
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_password:
        raise HTTPException(
            status_code=503,
            detail="Session upload is disabled (ADMIN_PASSWORD is not configured on the server).",
        )

    if not secrets.compare_digest(password, admin_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    data = await file.read()
    try:
        cookies = _safe_load_cookies(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    DEFAULT_COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DEFAULT_COOKIE_FILE, "wb") as f:
        pickle.dump(cookies, f)

    logger.warning("Amazon session cookies replaced via admin endpoint (%d cookies)", len(cookies))

    return UploadCookiesResponse(cookie_count=len(cookies))
