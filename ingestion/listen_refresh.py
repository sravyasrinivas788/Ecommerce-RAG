import os
import select
import time

import psycopg2
from dotenv import load_dotenv

from ingestion.embed import embed_source, check_collection, delete_point

load_dotenv()


def fetch_and_embed(source, pk):
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    if source == "products":
        cur.execute(
            "SELECT item_id, embedding_text, brand, product_type, category_primary "
            "FROM products WHERE item_id = %s",
            (pk,),
        )
        row = cur.fetchone()
        if row:
            item_id, text, brand, ptype, cat = row
            chunk = {
                "source": "abo",
                "doc_id": f"abo:{item_id}",
                "text": text,
                "metadata": {"item_id": item_id, "brand": brand, "product_type": ptype, "category": cat},
            }
            embed_source([chunk], "products")
            

    elif source == "reviews":
        cur.execute(
            "SELECT id, asin, matched_item_id, category, rating, title, review_text, verified_purchase "
            "FROM reviews WHERE id = %s",
            (int(pk),),
        )
        row = cur.fetchone()
        if row:
            id_, asin, matched_item_id, category, rating, title, review_text, verified = row
            chunk = {
                "source": "amazon_reviews",
                "doc_id": f"review:{id_}",
                "text": f"{title or ''}\n{review_text or ''}".strip(),
                "metadata": {
                    "id": id_, "asin": asin, "matched_item_id": matched_item_id,
                    "category": category, "rating": rating, "verified_purchase": verified,
                },
            }
            embed_source([chunk], "reviews")

    elif source == "policies":
        cur.execute("SELECT doc_id, title, section, body FROM policies WHERE doc_id = %s", (pk,))
        row = cur.fetchone()
        if row:
            doc_id, title, section, body = row
            chunk = {
                "source": "policy",
                "doc_id": doc_id,
                "text": f"{title} — {section}\n\n{body}",
                "metadata": {"title": title, "section": section},
            }
            embed_source([chunk], "policies")
            

    conn.commit()
    cur.close()
    conn.close()


def handle_change(source, op, pk):
    if op == "DELETE":
        if source == "products":
            doc_id = f"abo:{pk}"
        elif source == "reviews":
            doc_id = f"review:{pk}"
        else:  # policies — doc_id IS the pk already
            doc_id = pk
        delete_point(doc_id)
        print(f"Deleted {source}:{pk} from Qdrant")
    else:
        fetch_and_embed(source, pk)


def listen():
    while True:
        try:
            conn = psycopg2.connect(os.environ["DATABASE_URL"])
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("LISTEN content_changes;")
            check_collection()
            print("Listening for content changes...")

            while True:
                if select.select([conn], [], [], 5) == ([], [], []):
                    continue
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop(0)
                    source, op, pk = notify.payload.split(":", 2)
                    print(f"Change detected: {source} {op} -> {pk}")
                    try:
                        handle_change(source, op, pk)
                    except Exception as e:
                        print(f"Failed to handle {source}:{op}:{pk}: {e}")

        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"Lost connection to Postgres: {e}. Reconnecting in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    listen()