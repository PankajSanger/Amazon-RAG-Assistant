"""deepeval evaluation of the product and review RAG pipelines.

Requires OPENAI_API_KEY (used both by the pipeline and by deepeval's
default LLM-judge metrics) and scraped data already loaded into
data/amazon_data.db + chroma_store/ (run the scrapers and index once
before running these tests).

Run with:
    deepeval test run tests/test_rag_evaluation.py
or plain:
    pytest tests/test_rag_evaluation.py
"""
import os

import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

from src.rag.pipeline import (
    document_ids,
    document_loader,
    load_environment,
    rag_pipeline,
    retrieve_documents,
    retrieve_review_documents,
    review_document_ids,
    review_document_loader,
    review_rag_pipeline,
    format_product_docs,
    format_review_docs,
    vector_store,
)
from src.storage.database import load_products, load_reviews

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY is required to run the pipeline and the LLM-judge metrics.",
)

requires_products = pytest.mark.skipif(
    load_products().empty,
    reason="No product data in data/amazon_data.db - scrape and index products first.",
)
requires_reviews = pytest.mark.skipif(
    load_reviews().empty,
    reason="No review data in data/amazon_data.db - scrape and index reviews first.",
)

PRODUCT_QUERIES = [
    "Which hair oil is best for hair fall control?",
    "Suggest a hair oil under 500 rupees with a good rating.",
]

REVIEW_QUERIES = [
    "What do customers say about the smell of the hair oil?",
    "Are there any complaints about leakage or packaging?",
]


def _product_test_case(query):
    llm, embedding_model = load_environment()
    store = vector_store(
        embedding_model,
        lambda: document_loader(load_products()),
        collection_name="product_details",
        id_fn=document_ids,
    )
    docs = retrieve_documents(llm, store, query)

    return LLMTestCase(
        input=query,
        actual_output=rag_pipeline(query),
        retrieval_context=[format_product_docs([doc]) for doc in docs],
    )


def _review_test_case(query):
    llm, embedding_model = load_environment()
    store = vector_store(
        embedding_model,
        lambda: review_document_loader(load_reviews()),
        collection_name="customer_reviews",
        id_fn=review_document_ids,
    )
    docs = retrieve_review_documents(llm, store, query)

    return LLMTestCase(
        input=query,
        actual_output=review_rag_pipeline(query),
        retrieval_context=[format_review_docs([doc]) for doc in docs],
    )


@requires_products
@pytest.mark.parametrize("query", PRODUCT_QUERIES)
def test_product_rag_quality(query):
    assert_test(
        _product_test_case(query),
        [AnswerRelevancyMetric(threshold=0.7), FaithfulnessMetric(threshold=0.7)],
    )


@requires_reviews
@pytest.mark.parametrize("query", REVIEW_QUERIES)
def test_review_rag_quality(query):
    assert_test(
        _review_test_case(query),
        [AnswerRelevancyMetric(threshold=0.7), FaithfulnessMetric(threshold=0.7)],
    )
