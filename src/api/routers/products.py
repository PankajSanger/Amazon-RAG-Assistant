from fastapi import APIRouter, HTTPException

from src.rag.pipeline import load_environment, rag_pipeline, reindex_products
from src.storage.database import load_products, load_reviews
from src.api.schemas import AskRequest, AskResponse, ReindexResponse, StatsResponse
from src.api.utils import records

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products")
def list_products():
    return records(load_products())


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    products = load_products()
    reviews = load_reviews()

    rating_distribution = {str(star): 0 for star in range(1, 6)}
    if not products.empty:
        for rating in products["rating"].dropna():
            bucket = str(min(5, max(1, round(rating))))
            rating_distribution[bucket] += 1

    return StatsResponse(
        product_count=len(products),
        review_count=len(reviews),
        avg_product_rating=float(products["rating"].mean()) if not products.empty else None,
        avg_review_rating=float(reviews["rating"].mean()) if not reviews.empty else None,
        rating_distribution=rating_distribution,
    )


@router.post("/products/reindex", response_model=ReindexResponse)
def reindex():
    try:
        _, embedding_model = load_environment()
        indexed_count = reindex_products(embedding_model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ReindexResponse(indexed_count=indexed_count)


@router.post("/products/ask", response_model=AskResponse)
def ask_products(request: AskRequest):
    try:
        answer, docs = rag_pipeline(request.query, include_sources=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    sources = [
        {
            "asin": doc.metadata.get("asin"),
            "title": doc.metadata.get("title"),
            "rating": doc.metadata.get("rating"),
            "no_of_ratings": doc.metadata.get("no_of_ratings"),
            "price": doc.metadata.get("price"),
            "url": doc.metadata.get("url"),
        }
        for doc in docs
    ]

    return AskResponse(answer=answer, sources=sources)
