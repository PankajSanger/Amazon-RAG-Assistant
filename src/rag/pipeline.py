#product details and customer reviews
import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_classic.chains.query_constructor.schema import AttributeInfo
from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_community.query_constructors.chroma import ChromaTranslator
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import pandas as pd
import chromadb

from src.rag.guardrails import guard_answer, guard_query
from src.storage.database import load_products, load_reviews

logger = logging.getLogger(__name__)

#pipeline.py -> rag -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAG_DIR = str(PROJECT_ROOT / "chroma_store")


def load_environment():
    load_dotenv()
    llm = ChatOpenAI(model="gpt-5", temperature=0)
    embedding_model = OpenAIEmbeddings()
    return llm, embedding_model


#Shared row-to-Document builder: dedupes by id_column and delegates the
#dataset-specific page content / metadata shape to the passed-in callbacks.
def _build_documents(data, id_column, content_fn, metadata_fn):

    document = []
    seen = set()
    for row in range(data.shape[0]):
        id_value = str(data[id_column].iloc[row])

        if id_value in seen:
            continue
        seen.add(id_value)

        document.append(Document(
            page_content=content_fn(data, row),
            metadata=metadata_fn(data, row)
        ))

    return document


#Document Loading - products
def document_loader(data):

    def content(data, row):
        title = str(data['title'].iloc[row])
        about = str(data['about'].iloc[row])
        return f"""product title : {title},
        product details = {about}"""

    def metadata(data, row):
        meta = {
            "asin": str(data['asin'].iloc[row]),
            "title": str(data['title'].iloc[row]),
            "url": str(data['url'].iloc[row]),
        }

        #Chroma metadata values must be str/int/float/bool - omit fields that
        #are missing (NaN) in the source data rather than fabricating a 0,
        #which would misleadingly look like a real rating/price/count.
        rating = data['rating'].iloc[row]
        if pd.notna(rating):
            meta["rating"] = float(rating)

        no_of_ratings = data['no_of_ratings'].iloc[row]
        if pd.notna(no_of_ratings):
            meta["no_of_ratings"] = int(no_of_ratings)

        price = data['price'].iloc[row]
        if pd.notna(price):
            meta["price"] = int(price)

        return meta

    return _build_documents(data, "asin", content, metadata)


def document_ids(documents):
    return [doc.metadata["asin"] for doc in documents]


#Document Loading - customer reviews
def review_document_loader(data):

    def content(data, row):
        title = str(data['title'].iloc[row])
        contents = str(data['contents'].iloc[row])
        return f"""review title : {title},
        review contents = {contents}"""

    def metadata(data, row):
        rating = data['rating'].iloc[row]
        return {
            "url": str(data['url'].iloc[row]),
            "asin": str(data['asin'].iloc[row]),
            "author": str(data['author'].iloc[row]),
            "date": str(data['date'].iloc[row]),
            "rating": float(rating) if pd.notna(rating) else 0.0
        }

    return _build_documents(data, "url", content, metadata)


def review_document_ids(documents):
    return [doc.metadata["url"] for doc in documents]


#Vector Store
def vector_store(embedding_model, document_loader_fn, collection_name="product_details", id_fn=document_ids):
    client = chromadb.PersistentClient(path=RAG_DIR)

    existing_collections = [c.name for c in client.list_collections()]

    if collection_name in existing_collections:
        logger.info("Loading existing collection: %s", collection_name)

        store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=RAG_DIR
        )

    else:
        logger.info("Creating new collection: %s", collection_name)

        documents = document_loader_fn()

        if not documents:
            raise ValueError("No data found. Scrape it first.")

        store = Chroma.from_documents(
            documents=documents,
            ids=id_fn(documents),
            collection_name=collection_name,
            embedding=embedding_model,
            persist_directory=RAG_DIR
        )

    return store


#Reindex a dataset into the existing (or new) collection, keyed by id_fn,
#so re-running it updates existing rows instead of duplicating them.
def _reindex_collection(embedding_model, load_data_fn, document_loader_fn, id_fn, collection_name, empty_error):
    data = load_data_fn()

    if data.empty:
        raise ValueError(empty_error)

    documents = document_loader_fn(data)
    ids = id_fn(documents)

    store = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=RAG_DIR
    )

    #Purge rows no longer in the source data (deleted/replaced products,
    #or leftovers from earlier indexing schemes/ids) - otherwise stale
    #documents keep surfacing in retrieval indefinitely.
    existing_ids = store.get(include=[])["ids"]
    stale_ids = set(existing_ids) - set(ids)
    if stale_ids:
        store.delete(ids=list(stale_ids))

    #Chroma's add() silently skips ids that already exist rather than
    #updating their metadata/content, so a plain add_documents() here
    #would never actually refresh previously-indexed rows. Delete first
    #for real upsert semantics - delete() no-ops on ids that don't
    #already exist, so first-time indexing is unaffected.
    store.delete(ids=ids)
    store.add_documents(documents=documents, ids=ids)

    return len(documents)


def reindex_products(embedding_model):
    return _reindex_collection(
        embedding_model,
        load_products,
        document_loader,
        document_ids,
        "product_details",
        "No product data found. Scrape product details first."
    )


def reindex_reviews(embedding_model):
    return _reindex_collection(
        embedding_model,
        load_reviews,
        review_document_loader,
        review_document_ids,
        "customer_reviews",
        "No review data found. Scrape customer reviews first."
    )


#Self Query Retriever
#Passing structured_query_translator explicitly skips SelfQueryRetriever's
#_get_builtin_translator(), which unconditionally imports ~17 legacy vectorstore
#integrations from langchain-community even though only Chroma is used here -
#several of those (e.g. databricks, weaviate, qdrant) were split out into
#standalone packages and are no longer bundled in langchain-community, so that
#import chain breaks on a clean install.
def _self_query_retrieve(llm, store, query, metadata_field_info, document_contents):
    retriever = SelfQueryRetriever.from_llm(
        llm=llm,
        vectorstore=store,
        metadata_field_info=metadata_field_info,
        document_contents=document_contents,
        structured_query_translator=ChromaTranslator(),
        search_kwargs={"k": 3}
    )

    return retriever.invoke(query)


def retrieve_documents(llm, store, query):

    metadata_info_field = [
        AttributeInfo(name="title", description="title/product name", type="string"),
        AttributeInfo(name="rating", description="product rating", type="float"),
        AttributeInfo(name="no_of_ratings", description="number of product ratings", type="integer"),
        AttributeInfo(name="price", description="product price", type="integer")
    ]

    return _self_query_retrieve(
        llm, store, query, metadata_info_field,
        "Amazon product title and description containing benefits, ingredients, features and usage information."
    )


def retrieve_review_documents(llm, store, query):

    metadata_info_field = [
        AttributeInfo(name="asin", description="product identifier the review belongs to", type="string"),
        AttributeInfo(name="author", description="name of the reviewer", type="string"),
        AttributeInfo(name="rating", description="star rating given by the reviewer", type="float"),
        AttributeInfo(name="date", description="date the review was posted", type="string")
    ]

    return _self_query_retrieve(
        llm, store, query, metadata_info_field,
        "Amazon customer review title and content describing product experience, complaints, praise and usage feedback."
    )


def _format_docs(docs, formatter):
    return "\n\n".join(formatter(doc) for doc in docs)


def format_product_docs(docs):
    def fmt(doc):
        return f"""
        Rating: {doc.metadata.get('rating')}
        Number of Ratings: {doc.metadata.get('no_of_ratings')}
        Price: ₹{doc.metadata.get('price')}
        Description:
        {doc.page_content}
        """

    return _format_docs(docs, fmt)


def format_review_docs(docs):
    def fmt(doc):
        return f"""
        Author: {doc.metadata.get('author')}
        Rating: {doc.metadata.get('rating')}
        Date: {doc.metadata.get('date')}
        Review:
        {doc.page_content}
        """

    return _format_docs(docs, fmt)


def get_llm_response(llm, query, context):
    prompt = PromptTemplate(
        template="Answer the following query based only on the context provided below. If answer is not present in the context, say i don't know.\nQuery:{query}\nContext : {context}",
        input_variables=["query", "context"]
    )

    chain = prompt | llm
    response = chain.invoke({"query": query, "context": context})
    return response.content


def _answer(query, document_loader_fn, collection_name, id_fn, retrieve_fn, format_fn, redact_pii, include_sources=False):
    llm, embedding_model = load_environment()

    refusal = guard_query(llm, query)
    if refusal:
        return (refusal, []) if include_sources else refusal

    store = vector_store(
        embedding_model,
        document_loader_fn,
        collection_name=collection_name,
        id_fn=id_fn
    )

    retrieved_documents = retrieve_fn(llm, store, query)
    context = format_fn(retrieved_documents)

    answer = guard_answer(get_llm_response(llm, query, context), redact_pii=redact_pii)
    logger.info("AI: %s", answer)
    return (answer, retrieved_documents) if include_sources else answer


def rag_pipeline(query, include_sources=False):
    #Product titles/brands are frequently misdetected as PERSON entities by
    #DetectPII, and products carry no reviewer PII, so PII redaction is
    #skipped here and only applied to review answers.
    return _answer(
        query,
        lambda: document_loader(load_products()),
        "product_details",
        document_ids,
        retrieve_documents,
        format_product_docs,
        redact_pii=False,
        include_sources=include_sources
    )


def review_rag_pipeline(query, include_sources=False):
    return _answer(
        query,
        lambda: review_document_loader(load_reviews()),
        "customer_reviews",
        review_document_ids,
        retrieve_review_documents,
        format_review_docs,
        redact_pii=True,
        include_sources=include_sources
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    print("AI : ", rag_pipeline(input("Enter your query: ")))
