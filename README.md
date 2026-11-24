Commands to make Postgres and Qdrant up: docker compose up -d
Commads to load the  tables into database: Get-Content db/schema.sql | docker exec -i ecommerce-rag-postgres-1 psql -U Sravya -d Ecommerce
Command to load raw sources (products, reviews, olist, policy PDF bytes) into Postgres: python scripts/load_all.py
Command to chunk the policy PDF into sections (populates the policies table): python ingestion/chunk_policy.py
Command to embed products, reviews, and policies into Qdrant: python -m ingestion.embed

