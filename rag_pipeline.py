#product details and customer reviews
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_classic.chains.query_constructor.schema import AttributeInfo
from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import pandas as pd
import chromadb

from database import load_products, load_reviews


def load_environment():
    load_dotenv()
    llm = ChatOpenAI(model="gpt-5")
    embedding_model = OpenAIEmbeddings()
    return llm, embedding_model


#Document Loading
def document_loader(data):

    document = []
    seen = set()
    for row in range(data.shape[0]):
        asin = str(data['asin'].iloc[row])
        title = str(data['title'].iloc[row])
        about = str(data['about'].iloc[row])

        if asin in seen:
            continue
        seen.add(asin)

        doc = f"""hair oil product title : {title},
        product details = {about}"""

        document.append(Document(page_content=doc, metadata={
            "asin": asin,
            "title": title,
            "rating": float(data['rating'].iloc[row]),
            "no_of_ratings": int(data['no_of_ratings'].iloc[row]),
            "price": int(data['price'].iloc[row])
        }))

    return document


def document_ids(documents):
    return [doc.metadata["asin"] for doc in documents]


#Document Loading - customer reviews
def review_document_loader(data):

    document = []
    seen = set()
    for row in range(data.shape[0]):
        url = str(data['url'].iloc[row])

        if url in seen:
            continue
        seen.add(url)

        asin = str(data['asin'].iloc[row])
        title = str(data['title'].iloc[row])
        contents = str(data['contents'].iloc[row])
        author = str(data['author'].iloc[row])
        date = str(data['date'].iloc[row])
        rating = data['rating'].iloc[row]

        doc = f"""review title : {title},
        review contents = {contents}"""

        document.append(Document(page_content=doc, metadata={
            "url": url,
            "asin": asin,
            "author": author,
            "date": date,
            "rating": float(rating) if pd.notna(rating) else 0.0
        }))

    return document


def review_document_ids(documents):
    return [doc.metadata["url"] for doc in documents]


#Vector Store
def vector_store(embedding_model, document_loader_fn, collection_name="product_details", id_fn=document_ids):
    client = chromadb.PersistentClient(path="./RAG")

    existing_collections = [c.name for c in client.list_collections()]

    if collection_name in existing_collections:
        print(f"Loading existing collection: {collection_name}")

        store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory="./RAG"
        )

    else:
        print(f"Creating new collection: {collection_name}")

        documents = document_loader_fn()

        if not documents:
            raise ValueError("No data found. Scrape it first.")

        store = Chroma.from_documents(
            documents=documents,
            ids=id_fn(documents),
            collection_name=collection_name,
            embedding=embedding_model,
            persist_directory="./RAG"
        )

    return store


#Reindex products into the existing (or new) collection, keyed by asin
#so re-running it updates existing products instead of duplicating them.
def reindex_products(embedding_model):
    data = load_products()

    if data.empty:
        raise ValueError("No product data found. Scrape product details first.")

    documents = document_loader(data)

    store = Chroma(
        collection_name="product_details",
        embedding_function=embedding_model,
        persist_directory="./RAG"
    )

    store.add_documents(documents=documents, ids=document_ids(documents))

    return len(documents)


#Reindex reviews into the existing (or new) collection, keyed by review url
#so re-running it updates existing reviews instead of duplicating them.
def reindex_reviews(embedding_model):
    data = load_reviews()

    if data.empty:
        raise ValueError("No review data found. Scrape customer reviews first.")

    documents = review_document_loader(data)

    store = Chroma(
        collection_name="customer_reviews",
        embedding_function=embedding_model,
        persist_directory="./RAG"
    )

    store.add_documents(documents=documents, ids=review_document_ids(documents))

    return len(documents)


#Self Query Retriever - products
def retrieve_documents(llm, store, query):

    metadata_info_field = [
        AttributeInfo(name="title", description="title/product name", type="string"),
        AttributeInfo(name="rating", description="product rating", type="float"),
        AttributeInfo(name="no_of_ratings", description="number of product ratings", type="integer"),
        AttributeInfo(name="price", description="product price", type="integer")
    ]

    retriever = SelfQueryRetriever.from_llm(
        llm=llm,
        vectorstore=store,
        metadata_field_info=metadata_info_field,
        document_contents="Amazon product title and description containing benefits, ingredients, features and usage information.",
        search_kwargs={"k": 3}
    )

    return retriever.invoke(query)


#Self Query Retriever - customer reviews
def retrieve_review_documents(llm, store, query):

    metadata_info_field = [
        AttributeInfo(name="asin", description="product identifier the review belongs to", type="string"),
        AttributeInfo(name="author", description="name of the reviewer", type="string"),
        AttributeInfo(name="rating", description="star rating given by the reviewer", type="float"),
        AttributeInfo(name="date", description="date the review was posted", type="string")
    ]

    retriever = SelfQueryRetriever.from_llm(
        llm=llm,
        vectorstore=store,
        metadata_field_info=metadata_info_field,
        document_contents="Amazon customer review title and content describing product experience, complaints, praise and usage feedback.",
        search_kwargs={"k": 3}
    )

    return retriever.invoke(query)


def format_product_docs(docs):
    output = []
    for doc in docs:
        output.append(f"""
        Rating: {doc.metadata.get('rating')}
        Number of Ratings: {doc.metadata.get('no_of_ratings')}
        Price: ₹{doc.metadata.get('price')}
        Description:
        {doc.page_content}
        """)

    return "\n\n".join(output)


def format_review_docs(docs):
    output = []
    for doc in docs:
        output.append(f"""
        Author: {doc.metadata.get('author')}
        Rating: {doc.metadata.get('rating')}
        Date: {doc.metadata.get('date')}
        Review:
        {doc.page_content}
        """)

    return "\n\n".join(output)


def get_llm_response(llm, query, context):
    prompt = PromptTemplate(
        template="Answer the following query based only on the context provided below. If answer is not present in the context, say i don't know.\nQuery:{query}\nContext : {context}",
        input_variables=["query", "context"]
    )

    chain = prompt | llm
    response = chain.invoke({"query": query, "context": context})
    return response.content


def rag_pipeline(query):
    llm, embedding_model = load_environment()

    store = vector_store(
        embedding_model,
        lambda: document_loader(load_products())
    )

    retrieved_documents = retrieve_documents(llm, store, query)
    context = format_product_docs(retrieved_documents)

    answer = get_llm_response(llm, query, context)
    print("AI : ", answer)
    return answer


def review_rag_pipeline(query):
    llm, embedding_model = load_environment()

    store = vector_store(
        embedding_model,
        lambda: review_document_loader(load_reviews()),
        collection_name="customer_reviews",
        id_fn=review_document_ids
    )

    retrieved_documents = retrieve_review_documents(llm, store, query)
    context = format_review_docs(retrieved_documents)

    answer = get_llm_response(llm, query, context)
    print("AI : ", answer)
    return answer


if __name__ == "__main__":
    rag_pipeline(input("Enter your query: "))
