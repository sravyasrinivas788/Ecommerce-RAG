-- ABO product catalog
CREATE TABLE products (
    item_id TEXT PRIMARY KEY,
    name TEXT,
    brand TEXT,
    color TEXT,
    material TEXT,
    product_type TEXT,
    category_primary TEXT,
    embedding_text TEXT NOT NULL,
    raw JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    embedded_at TIMESTAMPTZ
);
CREATE INDEX idx_products_product_type ON products(product_type);

-- Amazon Reviews (matched + sampled)
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    asin TEXT NOT NULL,
    matched_item_id TEXT REFERENCES products(item_id),
    category TEXT NOT NULL,            
    rating NUMERIC,
    title TEXT,
    review_text TEXT,
    verified_purchase BOOLEAN,
    review_timestamp BIGINT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    embedded_at TIMESTAMPTZ
);
CREATE INDEX idx_reviews_matched_item_id ON reviews(matched_item_id);

CREATE TABLE olist_customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT
);

CREATE TABLE olist_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES olist_customers(customer_id),
    order_status TEXT,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);
CREATE INDEX idx_orders_customer_id ON olist_orders(customer_id);

CREATE TABLE olist_order_items (
    order_id TEXT REFERENCES olist_orders(order_id),
    order_item_id INT,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TIMESTAMP,
    price NUMERIC,
    freight_value NUMERIC,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE olist_order_payments (
    order_id TEXT REFERENCES olist_orders(order_id),
    payment_sequential INT,
    payment_type TEXT,
    payment_installments INT,
    payment_value NUMERIC,
    PRIMARY KEY (order_id, payment_sequential)
);

-- Custom policy documents
CREATE TABLE policies (
    doc_id TEXT PRIMARY KEY,           
    title TEXT NOT NULL,
    section TEXT,                     
    body TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    embedded_at TIMESTAMPTZ
);

CREATE TABLE policy_files (
    file_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    content BYTEA NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);