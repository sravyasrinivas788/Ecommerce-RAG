import csv
import json
import os
import re

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()


def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


# ---------- 1. Products ----------

def load_products(conn, path="data/amazon/products_clean.jsonl"):
    cur = conn.cursor()
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "\t" in line:
                line = line.split("\t", 1)[1]
            d = json.loads(line)
            rows.append((
                d["item_id"], d.get("name"), d.get("brand"), d.get("color"),
                d.get("material"), d.get("product_type"), d.get("category_primary"),
                d["embedding_text"], json.dumps(d),
            ))
    execute_values(cur, """
        INSERT INTO products (item_id, name, brand, color, material, product_type, category_primary, embedding_text, raw)
        VALUES %s
        ON CONFLICT (item_id) DO UPDATE SET
            name = EXCLUDED.name, brand = EXCLUDED.brand, color = EXCLUDED.color,
            material = EXCLUDED.material, product_type = EXCLUDED.product_type,
            category_primary = EXCLUDED.category_primary, embedding_text = EXCLUDED.embedding_text,
            raw = EXCLUDED.raw, updated_at = now()
    """, rows)
    conn.commit()
    print(f"products: loaded {len(rows)} rows")


# ---------- 2. Reviews ----------

REVIEW_FILES = {
    "cell_phones": "data/amazon/raw_reviews_cell_phones.jsonl",
    "shoes_jewelry": "data/amazon/raw_reviews_shoes_jewelry.jsonl",
    "home_kitchen": "data/amazon/raw_reviews_home_kitchen.jsonl",
}

def load_reviews(conn):
    cur = conn.cursor()
    total = 0
    for category, path in REVIEW_FILES.items():
        if not os.path.exists(path):
            print(f"reviews: skipping missing {path}")
            continue
        rows = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                rows.append((
                    d.get("asin") or d.get("parent_asin"),
                    d.get("_matched_item_id"),
                    category,
                    d.get("rating"),
                    d.get("title"),
                    d.get("text"),
                    d.get("verified_purchase"),
                    d.get("timestamp"),
                ))
        execute_values(cur, """
            INSERT INTO reviews (asin, matched_item_id, category, rating, title, review_text, verified_purchase, review_timestamp)
            VALUES %s
        """, rows)
        total += len(rows)
        print(f"reviews: loaded {len(rows)} rows from {category}")
    conn.commit()
    print(f"reviews: {total} total")


# ---------- 3. Olist ----------

def _none_if_blank(v):
    return v if v else None

def load_olist(conn):
    cur = conn.cursor()

    with open("data/olist/olist_customers_dataset.csv", encoding="utf-8") as f:
        rows = [(r["customer_id"], r["customer_unique_id"], r["customer_zip_code_prefix"],
                  r["customer_city"], r["customer_state"]) for r in csv.DictReader(f)]
    execute_values(cur, """
        INSERT INTO olist_customers (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)
        VALUES %s ON CONFLICT (customer_id) DO NOTHING
    """, rows)
    print(f"olist_customers: loaded {len(rows)} rows")

    with open("data/olist/olist_orders_dataset.csv", encoding="utf-8") as f:
        rows = [(r["order_id"], r["customer_id"], r["order_status"],
                  _none_if_blank(r["order_purchase_timestamp"]), _none_if_blank(r["order_approved_at"]),
                  _none_if_blank(r["order_delivered_carrier_date"]), _none_if_blank(r["order_delivered_customer_date"]),
                  _none_if_blank(r["order_estimated_delivery_date"])) for r in csv.DictReader(f)]
    execute_values(cur, """
        INSERT INTO olist_orders (order_id, customer_id, order_status, order_purchase_timestamp,
                                   order_approved_at, order_delivered_carrier_date,
                                   order_delivered_customer_date, order_estimated_delivery_date)
        VALUES %s ON CONFLICT (order_id) DO NOTHING
    """, rows)
    print(f"olist_orders: loaded {len(rows)} rows")

    with open("data/olist/olist_order_items_dataset.csv", encoding="utf-8") as f:
        rows = [(r["order_id"], int(r["order_item_id"]), r["product_id"], r["seller_id"],
                  _none_if_blank(r["shipping_limit_date"]), float(r["price"]), float(r["freight_value"]))
                 for r in csv.DictReader(f)]
    execute_values(cur, """
        INSERT INTO olist_order_items (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value)
        VALUES %s ON CONFLICT (order_id, order_item_id) DO NOTHING
    """, rows)
    print(f"olist_order_items: loaded {len(rows)} rows")

    with open("data/olist/olist_order_payments_dataset.csv", encoding="utf-8") as f:
        rows = [(r["order_id"], int(r["payment_sequential"]), r["payment_type"],
                  int(r["payment_installments"]), float(r["payment_value"])) for r in csv.DictReader(f)]
    execute_values(cur, """
        INSERT INTO olist_order_payments (order_id, payment_sequential, payment_type, payment_installments, payment_value)
        VALUES %s ON CONFLICT (order_id, payment_sequential) DO NOTHING
    """, rows)
    print(f"olist_order_payments: loaded {len(rows)} rows")

    conn.commit()


# ---------- 4. Policies ----------


def load_policy_file(conn, path):
    cur = conn.cursor()
    fname = os.path.basename(path)
    with open(path, "rb") as f:
        data = f.read()
    cur.execute("""
        INSERT INTO policy_files (file_id, filename, content)
        VALUES (%s, %s, %s)
        ON CONFLICT (file_id) DO UPDATE SET content = EXCLUDED.content, uploaded_at = now()
    """, (fname, fname, psycopg2.Binary(data)))
    conn.commit()
    print(f"Stored {fname} ({len(data)} bytes) in policy_files")


# ---------- run everything ----------

if __name__ == "__main__":
    conn = get_conn()
    load_products(conn)
    load_reviews(conn)
    load_olist(conn)
    load_policy_file(conn, "data/policies/policies.pdf")
    conn.close()
    print("Done.")