"""
reformat_csv.py
---------------
Reformats soccer_posts.csv into the labeled ML format:
  - text  : post title + selftext preview (combined)
  - label : cleaned flair (e.g. "Goal Clip", "News", "Stats")
  - notes : flags for difficult/noisy cases

Run from the project folder:
    python reformat_csv.py

Input:  soccer_posts.csv  (in the same directory)
Output: soccer_labeled.csv (in the same directory)
"""

import csv
import re
from collections import Counter
from pathlib import Path

INPUT  = Path("soccer_posts.csv")
OUTPUT = Path("soccer_labeled.csv")


def clean_label(flair: str) -> str:
    """Strip the :n_tag: prefix from Reddit flair, e.g. ':n_goal: Goal Clip' -> 'Goal Clip'."""
    if not flair:
        return "Uncategorized"
    cleaned = re.sub(r"^:[^:]+:\s*", "", flair).strip()
    return cleaned or "Uncategorized"


def build_text(row: dict) -> str:
    """Combine title and selftext preview into a single text field."""
    title   = (row.get("title") or "").strip()
    preview = (row.get("selftext_preview") or "").strip()
    return f"{title} | {preview}" if preview else title


def flag_notes(row: dict) -> str:
    """Return a note string for cases that may be noisy or difficult to label."""
    notes = []
    try:
        ratio = float(row.get("upvote_ratio") or 1.0)
        score = int(row.get("score") or 0)
        if ratio < 0.75:
            notes.append("low upvote ratio — potentially controversial")
        if score < 30:
            notes.append("low score — low visibility")
        if not (row.get("flair") or "").strip():
            notes.append("no flair — label is inferred")
    except (ValueError, TypeError):
        pass
    return "; ".join(notes)


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Could not find '{INPUT}'. Run this script from the folder containing soccer_posts.csv.")

    rows_out = []
    with open(INPUT, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows_out.append({
                "text":  build_text(row),
                "label": clean_label(row.get("flair", "")),
                "notes": flag_notes(row),
            })

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
        writer.writeheader()
        writer.writerows(rows_out)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"✓ Wrote {len(rows_out)} rows → {OUTPUT}\n")
    counts = Counter(r["label"] for r in rows_out)
    print(f"{'Label':<30} {'Count':>5}")
    print("-" * 37)
    for label, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{label:<30} {count:>5}")


if __name__ == "__main__":
    main()