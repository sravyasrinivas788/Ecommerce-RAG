Commands to make Postgres and Qdrant up: docker compose up -d
Commads to load the  tables into database: Get-Content db/schema.sql | docker exec -i ecommerce-rag-postgres-1 psql -U Sravya -d Ecommerce
Command to load raw sources (products, reviews, olist, policy PDF bytes) into Postgres: python scripts/load_all.py
Command to chunk the policy PDF into sections (populates the policies table): python ingestion/chunk_policy.py
Command to embed products, reviews, and policies into Qdrant: python -m ingestion.embed
Command to add the CDC notify triggers (one-time): Get-Content db/migrations/001_cdc_triggers.sql | docker exec -i ecommerce-rag-postgres-1 psql -U Sravya -d Ecommerce
Command to build and start the always-on refresh listener (reacts to Postgres changes automatically, re-embeds into Qdrant): docker compose up -d --build refresh_listener
Command to watch the refresh listener's logs: docker compose logs -f refresh_listener

