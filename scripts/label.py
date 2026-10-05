"""Terminal labeling tool for news headlines.

Keys:
    1-8  assign label        s  skip (excluded from dataset)
    u    undo last           g  show category list
    q    quit (progress is saved after every answer)

Usage:
    python scripts/label.py
"""
import json
import os
from collections import Counter
from datetime import datetime, timezone

POOL_PATH = os.path.join("data", "pool.jsonl")
LABELS_PATH = os.path.join("data", "labels.jsonl")
TARGET = 1500

CATEGORIES = {
    1: "실적",
    2: "리포트",
    3: "시황·수급",
    4: "해외·거시",
    5: "기업 이벤트",
    6: "정책·규제",
    7: "상품·투자전략",
    8: "기타",
}


def read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def show_categories() -> None:
    print("  " + "  ".join(f"{k}.{v}" for k, v in CATEGORIES.items()) + "  s.건너뛰기")


def show_stats(labels: list[dict]) -> None:
    done = [r for r in labels if r["label"] != "skip"]
    counts = Counter(r["label"] for r in done)
    dist = "  ".join(f"{CATEGORIES[k]} {counts.get(k, 0)}" for k in CATEGORIES)
    print(f"\n[진행 {len(done)}/{TARGET}, 건너뜀 {len(labels) - len(done)}]  {dist}")


def main() -> None:
    pool = read_jsonl(POOL_PATH)
    if not pool:
        raise SystemExit(f"{POOL_PATH} 이 없습니다. scripts/export_pool.py 를 먼저 실행하세요.")
    labels = read_jsonl(LABELS_PATH)

    show_stats(labels)
    show_categories()

    while True:
        labeled_ids = {r["id"] for r in labels}
        nxt = next((h for h in pool if h["id"] not in labeled_ids), None)
        if nxt is None:
            print("풀의 모든 헤드라인을 처리했습니다.")
            break

        print(f"\n> {nxt['title']}")
        key = input("라벨: ").strip().lower()

        if key == "q":
            break
        if key == "g":
            show_categories()
            continue
        if key == "u":
            if labels:
                removed = labels.pop()
                write_jsonl(LABELS_PATH, labels)
                print(f"  취소함: {removed['title'][:40]}")
            else:
                print("  취소할 라벨이 없습니다.")
            continue

        if key == "s":
            value = "skip"
        elif key.isdigit() and int(key) in CATEGORIES:
            value = int(key)
        else:
            print("  1-8, s, u, g, q 중에서 입력하세요.")
            continue

        labels.append({
            "id": nxt["id"],
            "title": nxt["title"],
            "label": value,
            "labeled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        write_jsonl(LABELS_PATH, labels)

        n_done = sum(1 for r in labels if r["label"] != "skip")
        if n_done % 50 == 0 and value != "skip":
            show_stats(labels)

    show_stats(labels)


if __name__ == "__main__":
    main()
