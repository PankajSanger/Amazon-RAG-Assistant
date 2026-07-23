import pandas as pd
from fastapi import APIRouter, HTTPException

from src.rag.pipeline import load_environment, review_rag_pipeline, reindex_reviews
from src.storage.database import load_reviews
from src.api.schemas import AskRequest, AskResponse, ReindexResponse

router = APIRouter(prefix="/api", tags=["reviews"])


@router.get("/reviews")
def list_reviews():
    df = load_reviews()
    if df.empty:
        return []
    return df.where(pd.notnull(df), None).to_dict("records")


@router.post("/reviews/reindex", response_model=ReindexResponse)
def reindex():
    try:
        _, embedding_model = load_environment()
        indexed_count = reindex_reviews(embedding_model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ReindexResponse(indexed_count=indexed_count)


@router.post("/reviews/ask", response_model=AskResponse)
def ask_reviews(request: AskRequest):
    try:
        answer, docs = review_rag_pipeline(request.query, include_sources=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    sources = [
        {
            "asin": doc.metadata.get("asin"),
            "author": doc.metadata.get("author"),
            "rating": doc.metadata.get("rating"),
            "date": doc.metadata.get("date"),
            "url": doc.metadata.get("url"),
        }
        for doc in docs
    ]

    return AskResponse(answer=answer, sources=sources)
