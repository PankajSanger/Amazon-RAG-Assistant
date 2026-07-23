import logging
from io import BytesIO

import streamlit as st
import pandas as pd

from src.scrapers.login import get_driver, auto_login, AutoLoginError
from src.scrapers.product_page import scrape_products
from src.scrapers.keyword_search import search_scrape
from src.scrapers.reviews import scrape_reviews
from src.storage.database import save_products, save_reviews, load_products, load_reviews
from src.rag.pipeline import (
    load_environment,
    vector_store,
    document_loader,
    retrieve_documents,
    format_product_docs,
    get_llm_response,
    reindex_products,
    review_document_loader,
    review_document_ids,
    retrieve_review_documents,
    format_review_docs,
    reindex_reviews
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Amazon Product & Review Scraper",
    layout="wide"
)

st.title("Amazon Product & Review Scraper")

mode = st.sidebar.radio(
    "Mode",
    ["Scrape Data", "Ask About Products", "Ask About Reviews"]
)

# ==================================================
# ASK ABOUT PRODUCTS (RAG)
# ==================================================

if mode == "Ask About Products":

    st.subheader("Ask About Products")

    @st.cache_resource
    def get_rag_components():
        llm, embedding_model = load_environment()
        store = vector_store(
            embedding_model,
            lambda: document_loader(load_products())
        )
        return llm, store

    if st.button("Rebuild Index"):

        try:
            _, embedding_model = load_environment()

            with st.spinner("Rebuilding index..."):
                indexed_count = reindex_products(embedding_model)

            get_rag_components.clear()
            st.success(f"Indexed {indexed_count} product(s).")

        except ValueError as exc:
            st.error(str(exc))

    query = st.text_input("Ask a question about the scraped products")

    if st.button("Ask") and query:

        try:
            llm, store = get_rag_components()

            with st.spinner("Thinking..."):
                docs = retrieve_documents(llm, store, query)
                context = format_product_docs(docs)
                answer = get_llm_response(llm, query, context)

            st.markdown(answer)

            if docs:
                with st.expander(f"Sources ({len(docs)})"):
                    for doc in docs:
                        st.write(doc.metadata.get("title"))

        except ValueError as exc:
            st.error(str(exc))

    st.stop()

# ==================================================
# ASK ABOUT REVIEWS (RAG)
# ==================================================

if mode == "Ask About Reviews":

    st.subheader("Ask About Reviews")

    @st.cache_resource
    def get_review_rag_components():
        llm, embedding_model = load_environment()
        store = vector_store(
            embedding_model,
            lambda: review_document_loader(load_reviews()),
            collection_name="customer_reviews",
            id_fn=review_document_ids
        )
        return llm, store

    if st.button("Rebuild Index", key="rebuild_review_index"):

        try:
            _, embedding_model = load_environment()

            with st.spinner("Rebuilding index..."):
                indexed_count = reindex_reviews(embedding_model)

            get_review_rag_components.clear()
            st.success(f"Indexed {indexed_count} review(s).")

        except ValueError as exc:
            st.error(str(exc))

    query = st.text_input("Ask a question about the scraped reviews")

    if st.button("Ask", key="ask_reviews") and query:

        try:
            llm, store = get_review_rag_components()

            with st.spinner("Thinking..."):
                docs = retrieve_review_documents(llm, store, query)
                context = format_review_docs(docs)
                answer = get_llm_response(llm, query, context)

            st.markdown(answer)

            if docs:
                with st.expander(f"Sources ({len(docs)})"):
                    for doc in docs:
                        st.write(f"{doc.metadata.get('author')} — {doc.metadata.get('asin')}")

        except ValueError as exc:
            st.error(str(exc))

    st.stop()

# ==================================================
# INPUT TYPE
# ==================================================

input_type = st.radio(
    "Select Input Type",
    [
        "Single URL",
        "Upload File",
        "Keyword Search"
    ]
)

# ==================================================
# SCRAPE OPTIONS
# ==================================================

st.subheader("Select Data to Scrape")

col1, col2 = st.columns(2)

with col1:
    scrape_product_details = st.checkbox(
        "Product Details",
        value=True
    )

with col2:
    scrape_customer_reviews = st.checkbox(
        "Customer Reviews"
    )

# ==================================================
# INPUT VARIABLES
# ==================================================

urls = []
keyword = None
pages = 1

# ==================================================
# SINGLE URL
# ==================================================

if input_type == "Single URL":

    url = st.text_input(
        "Enter Amazon Product URL"
    )

    if url:
        urls = [url]

# ==================================================
# FILE UPLOAD
# ==================================================

elif input_type == "Upload File":

    uploaded_file = st.file_uploader(
        "Upload Excel File (column name: url)",
        type=["xlsx"]
    )

    if uploaded_file:

        df_urls = pd.read_excel(uploaded_file)

        if "url" not in df_urls.columns:
            st.error(
                "Excel file must contain a column named 'url'"
            )
            st.stop()

        urls = df_urls["url"].dropna().tolist()

        st.success(
            f"{len(urls)} URLs loaded"
        )

        with st.expander("Preview"):
            st.dataframe(df_urls.head())

# ==================================================
# KEYWORD SEARCH
# ==================================================

elif input_type == "Keyword Search":

    keyword = st.text_input(
        "Enter Keyword"
    )

    pages = st.number_input(
        "Search Pages to Scrape",
        min_value=1,
        max_value=50,
        value=1
    )

# ==================================================
# SCRAPE BUTTON
# ==================================================

if st.button("Start Scraping"):

    if not scrape_product_details and not scrape_customer_reviews:

        st.error(
            "Please select at least one scraping option."
        )
        st.stop()

    if input_type == "Keyword Search":

        if not keyword:

            st.error(
                "Please enter a keyword."
            )
            st.stop()

    else:

        if not urls:

            st.error(
                "Please provide URL(s)."
            )
            st.stop()

    progress_bar = st.progress(0)
    status = st.empty()

    driver = get_driver()

    try:

        status.info("Logging into Amazon...")
        progress_bar.progress(10)

        auto_login(driver)

        # ==========================================
        # KEYWORD SEARCH
        # ==========================================

        if input_type == "Keyword Search":

            status.info(
                f"Searching keyword '{keyword}'..."
            )

            progress_bar.progress(25)

            search_results = search_scrape(
                driver=driver,
                keyword=keyword,
                pages=pages
            )

            search_df = pd.DataFrame(search_results)

            urls = search_df["URL"].dropna().tolist()

            status.success(
                f"{len(urls)} products found"
            )

            progress_bar.progress(40)

        product_df = None
        review_df = None

        # ==========================================
        # PRODUCT DETAILS
        # ==========================================

        if scrape_product_details:

            status.info(
                f"Scraping product details for {len(urls)} products..."
            )

            progress_bar.progress(55)

            product_data = scrape_products(
                driver=driver,
                urls=urls
            )

            product_df = pd.DataFrame(product_data)

            st.subheader("Product Details")

            st.dataframe(
                product_df,
                width='stretch'
            )

            saved_count = save_products(product_df)

            st.caption(
                f"Saved {saved_count} product(s) to the database "
                "— use Rebuild Index in Ask About Products to update the RAG index."
            )

        # ==========================================
        # CUSTOMER REVIEWS
        # ==========================================

        if scrape_customer_reviews:

            status.info(
                f"Scraping customer reviews for {len(urls)} products..."
            )

            progress_bar.progress(80)

            review_df = scrape_reviews(
                driver=driver,
                product_urls=urls
            )

            st.subheader("Customer Reviews")

            st.dataframe(
                review_df.head(100),
                use_container_width=True
            )

            saved_review_count = save_reviews(review_df)

            st.success(
                f"Collected {len(review_df):,} reviews "
                f"({saved_review_count} saved to the database)"
            )

        # ==========================================
        # EXCEL EXPORT
        # ==========================================

        status.info("Preparing Excel file...")

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            if product_df is not None:
                product_df.to_excel(
                    writer,
                    sheet_name="Products",
                    index=False
                )

            if review_df is not None:
                review_df.to_excel(
                    writer,
                    sheet_name="Reviews",
                    index=False
                )

        progress_bar.progress(100)

        status.success(
            "Scraping completed successfully!"
        )

        st.download_button(
            label="Download Excel",
            data=output.getvalue(),
            file_name="amazon_scraper_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except FileNotFoundError as exc:

        logger.warning("Missing cookie file: %s", exc)
        st.error(str(exc))
        st.info(
            "This app needs the Amazon cookie file to run scraping workflows. "
            "Make sure amazon_cookies.pkl is present in the deployment environment."
        )

    except AutoLoginError as exc:

        logger.warning("Amazon auto-login failed: %s", exc)
        st.error(str(exc))

    except Exception as e:

        logger.exception("Scraping run failed")
        st.error(
            f"Error: {str(e)}"
        )

    finally:

        driver.quit()