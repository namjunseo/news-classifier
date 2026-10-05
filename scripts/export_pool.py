"""Build the labeling pool from the stock-briefing DB.

Takes Korean headlines (hankyung feeds), drops duplicate titles,
shuffles with a fixed seed, and writes data/pool.jsonl.

Usage:
    python scripts/export_pool.py path/to/stock_briefing.db
"""
import json
import os
import random
import sqlite3
import sys

SEED = 42
OUT_PATH = os.path.join("data", "pool.jsonl")


def load_headlines(db_path: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, title, collected_at FROM articles "
        "WHERE market = 'KR' AND source LIKE 'hankyung%' ORDER BY id"
    ).fetchall()
    conn.close()

    seen: set[str] = set()
    out = []
    for r in rows:
        title = r["title"].strip()
        if not title or title in seen:
            continue  # same headline can appear in multiple feeds
        seen.add(title)
        out.append({"id": r["id"], "title": title, "date": (r["collected_at"] or "")[:10]})
    return out


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/export_pool.py path/to/stock_briefing.db")
    if os.path.exists(OUT_PATH):
        # Re-exporting would reshuffle the order labels were made in.
        raise SystemExit(f"{OUT_PATH} already exists. Delete it first if you really want to rebuild.")

    headlines = load_headlines(sys.argv[1])
    random.Random(SEED).shuffle(headlines)

    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for h in headlines:
            f.write(json.dumps(h, ensure_ascii=False) + "\n")
    print(f"wrote {len(headlines)} unique headlines to {OUT_PATH}")


if __name__ == "__main__":
    main()
