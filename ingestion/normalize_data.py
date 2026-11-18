import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

def normalize_products():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SELECT item_id, embedding_text, brand, product_type, category_primary FROM products")
    for item_id, embedding_text, brand, product_type, category_primary in cur.fetchall():
        yield {
            "source": "abo",
            "doc_id": f"abo:{item_id}",
            "text": embedding_text,
            "metadata": {
                "item_id": item_id,
                "brand": brand,
                "product_type": product_type,
                "category": category_primary,
            },
        }
    cur.close()
    conn.close()

def normalize_reviews():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("""
        SELECT id, asin, matched_item_id, category, rating, title, review_text, verified_purchase
        FROM reviews
    """)
    for id_, asin, matched_item_id, category, rating, title, review_text, verified_purchase in cur.fetchall():
        text = f"{title or ''}\n{review_text or ''}".strip()
        yield {
            "source": "amazon_reviews",
            "doc_id": f"review:{id_}",
            "text": text,
            "metadata": {
                "asin": asin,
                "matched_item_id": matched_item_id,   # null for general sampled reviews
                "category": category,
                "rating": rating,
                "verified_purchase": verified_purchase,
            },
        }
    cur.close()
    conn.close()


def normalize_policies():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SELECT doc_id, title, section, body FROM policies")
    for doc_id, title, section, body in cur.fetchall():
        yield {
            "source": "policy",
            "doc_id": doc_id,
            "text": f"{title} — {section}\n\n{body}",
            "metadata": {"title": title, "section": section},
        }
    cur.close()
    conn.close()