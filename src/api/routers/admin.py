import logging
import os
import secrets

from fastapi import APIRouter, HTTPException

from src.rag.pipeline import clear_collections
from src.storage.database import clear_all
from src.api.schemas import ClearDatabaseRequest, ClearDatabaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
