import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

#database.py -> storage -> src -> project root
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "amazon_data.db"


@contextmanager
def get_connection():
    #sqlite3.Connection's own context manager only commits/rolls back the
    #transaction - it never closes the connection, so we own that here.
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                asin TEXT PRIMARY KEY,
                title TEXT,
                rating REAL,
                no_of_ratings INTEGER,
                price INTEGER,
                about TEXT,
                url TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                url TEXT PRIMARY KEY,
                asin TEXT REFERENCES products(asin),
                author TEXT,
                rating REAL,
                date TEXT,
                title TEXT,
                contents TEXT
            )
        """)


def _clean_numeric(series):
    without_commas = series.astype(str).str.replace(",", "", regex=False)
    first_number = without_commas.str.extract(r"(\d+\.?\d*)", expand=False)
    return pd.to_numeric(first_number, errors="coerce")


def save_products(product_df):
    if product_df is None or product_df.empty:
        return 0

    df = product_df.dropna(subset=["asin"]).copy()
    df = df.drop_duplicates(subset=["asin"], keep="last")

    df["rating"] = _clean_numeric(df["rating"])
    df["no_of_ratings"] = _clean_numeric(df["no_of_ratings"])
    df["price"] = _clean_numeric(df["price"])

    init_db()

    with get_connection() as conn:
        conn.executemany("""
            INSERT INTO products (asin, title, rating, no_of_ratings, price, about, url)
            VALUES (:asin, :title, :rating, :no_of_ratings, :price, :about, :url)
            ON CONFLICT(asin) DO UPDATE SET
                title = excluded.title,
                rating = excluded.rating,
                no_of_ratings = excluded.no_of_ratings,
                price = excluded.price,
                about = excluded.about,
                url = excluded.url
        """, df.to_dict("records"))

    logger.info("Saved %d product(s) to the database", len(df))
    return len(df)


def save_reviews(review_df):
    if review_df is None or review_df.empty:
        return 0

    df = review_df.rename(columns={"product_name": "asin"}).copy()
    df = df[["url", "asin", "author", "rating", "date", "title", "contents"]]
    df = df.dropna(subset=["url"]).drop_duplicates(subset=["url"], keep="last")
    df["date"] = df["date"].astype(str)

    init_db()

    with get_connection() as conn:
        conn.executemany("""
            INSERT INTO reviews (url, asin, author, rating, date, title, contents)
            VALUES (:url, :asin, :author, :rating, :date, :title, :contents)
            ON CONFLICT(url) DO UPDATE SET
                asin = excluded.asin,
                author = excluded.author,
                rating = excluded.rating,
                date = excluded.date,
                title = excluded.title,
                contents = excluded.contents
        """, df.to_dict("records"))

    logger.info("Saved %d review(s) to the database", len(df))
    return len(df)


def load_products():
    init_db()
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM products", conn)


def load_reviews():
    init_db()
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM reviews", conn)


def clear_all():
    """Deletes every row from products and reviews. Returns (products_cleared, reviews_cleared)."""
    init_db()
    with get_connection() as conn:
        products_cleared = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        reviews_cleared = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]

        #reviews.asin references products(asin) - delete reviews first.
        conn.execute("DELETE FROM reviews")
        conn.execute("DELETE FROM products")

    logger.warning("Cleared all data: %d product(s), %d review(s)", products_cleared, reviews_cleared)
    return products_cleared, reviews_cleared
