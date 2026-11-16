"""
Stream an Amazon Reviews 2023 category file (decompressed, via stdin) and
write a bounded, catalog-aware sample instead of dumping the whole file:

  - every review whose asin/parent_asin is an item_id in our own product
    catalog is kept (these are the reviews we can actually attach to a
    specific product we have)
  - a random reservoir sample of --sample-size reviews from the rest of the
    category is kept as general "customer sentiment for this product type"
    context (not tied to a specific SKU)

Usage (from the project root, Git Bash):
  curl -s "<review_category_url>" \
    | gunzip -c \
    | python scripts/sample_reviews.py \
        --catalog data/products_clean.jsonl \
        --sample-size 2000 \
        --out data/raw_reviews_cell_phones.jsonl
"""
import argparse
import json
import random
import sys


def load_catalog_ids(path):
    ids = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "\t" in line:
                line = line.split("\t", 1)[1]
            try:
                d = json.loads(line)
            except ValueError:
                continue
            item_id = d.get("item_id")
            if item_id:
                ids.add(item_id)
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True, help="path to products_clean.jsonl")
    ap.add_argument("--sample-size", type=int, default=2000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    catalog_ids = load_catalog_ids(args.catalog)
    sys.stderr.write(f"Loaded {len(catalog_ids)} catalog item ids.\n")

    rng = random.Random(args.seed)
    matched = []
    reservoir = []
    seen_unmatched = 0
    total = 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        total += 1
        try:
            d = json.loads(line)
        except ValueError:
            continue

        asin = d.get("asin") or d.get("parent_asin")
        if asin in catalog_ids:
            d["_matched_item_id"] = asin
            matched.append(d)
            continue

        seen_unmatched += 1
        if len(reservoir) < args.sample_size:
            reservoir.append(d)
        else:
            j = rng.randint(0, seen_unmatched - 1)
            if j < args.sample_size:
                reservoir[j] = d

        if total % 200000 == 0:
            sys.stderr.write(
                f"...scanned {total} rows, matched {len(matched)}, "
                f"reservoir full at {len(reservoir)}\n"
            )
            sys.stderr.flush()

    for d in reservoir:
        d["_matched_item_id"] = None

    with open(args.out, "w", encoding="utf-8") as f:
        for d in matched + reservoir:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    sys.stderr.write(
        f"Done. scanned={total} exact_matches={len(matched)} "
        f"sampled={len(reservoir)} -> wrote {args.out}\n"
    )


if __name__ == "__main__":
    main()
