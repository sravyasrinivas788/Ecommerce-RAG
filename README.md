Commands to make Postgres and Qdrant up: docker compose up -d
Commads to load the  tables into database: Get-Content db/schema.sql | docker exec -i ecommerce-rag-postgres-1 psql -U Sravya -d Ecommerce

