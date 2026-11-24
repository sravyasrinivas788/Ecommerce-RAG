import os
import psycopg2
import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance,PayloadSchemaType
from ingestion.normalize_data import normalize_products, normalize_reviews, normalize_policies
from dotenv import load_dotenv
load_dotenv()

MODEL_NAME="BAAI/bge-small-en-v1.5"
COLLECTION_NAME="ecommerce_rag"
VECTOR_SIZE=384

model=SentenceTransformer(MODEL_NAME)
qdrant=QdrantClient(url=os.getenv("QDRANT_URL"))

def check_collection():
    if not qdrant.collection_exists(COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),)
        qdrant.create_payload_index(COLLECTION_NAME,field_name="source",field_schema=PayloadSchemaType.KEYWORD)
        qdrant.create_payload_index(COLLECTION_NAME,field_name="category",field_schema=PayloadSchemaType.KEYWORD)
        qdrant.create_payload_index(COLLECTION_NAME,field_name="matched_item_id",field_schema=PayloadSchemaType.KEYWORD)

def doc_id_to_point_id(doc_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))

def embed_source(chunks,source_name,batch_size=256):
    chunks=list(chunks)
    if not chunks:
        return 0
    vectors = model.encode([c["text"] for c in chunks], normalize_embeddings=True,show_progress_bar=True,batch_size=batch_size)
    points = [
        PointStruct(id=doc_id_to_point_id(c["doc_id"]), vector=v.tolist(),
                     payload={"doc_id": c["doc_id"], "source": source_name, **c["metadata"]})
        for c, v in zip(chunks, vectors)
    ]
    for i in range(0,len(points),batch_size):
        batch_points=points[i:i+batch_size]
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=batch_points
        )
        print(f"{{source_name}}: embedded {i+len(batch_points)}/{len(points)} chunks")

if __name__=="__main__":
    check_collection()
    print(f"Embedding products...{embed_source(normalize_products(), 'products')} products embedded.")
    print(f"Embedding reviews...{embed_source(normalize_reviews(), 'reviews')} reviews embedded.")
    print(f"Embedding policies...{embed_source(normalize_policies(), 'policies')} policies embedded.")
    print("Embedding complete.")