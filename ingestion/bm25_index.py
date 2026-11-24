import pickle
import re
from rank_bm25 import BM25Okapi
from ingestion.normalize_data import normalize_products, normalize_reviews, normalize_policies


def tokenize(text):
    return re.findall(r"\w+", text.lower())

def build_bm25_index():
    chunks=list(normalize_products()) + list(normalize_reviews()) + list(normalize_policies())
    corpus = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(corpus)
    doc_ids=[c["doc_id"] for c in chunks]
    return bm25, doc_ids,chunks

if __name__=="__main__":
    bm25, doc_ids,chunks = build_bm25_index()
    with open("bm25_index.pkl", "wb") as f:
        pickle.dump((bm25, doc_ids,chunks), f)
    print(f"BM25 index built and saved to bm25_index.pkl with {len(doc_ids)} documents.")