"""
Reddit r/soccer Scraper (No API Key Required)
----------------------------------------------
Uses Reddit's old.reddit.com JSON endpoint with browser-like headers.

Setup:
    pip install requests

Usage:
    python scrape_soccer.py
    python scrape_soccer.py --sort new --limit 200 --output soccer_posts.csv
"""

import argparse
import csv
import time
import random
from datetime import datetime, timezone
from pathlib import Path

import requests

FIELDNAMES = [
    "post_id",
    "title",
    "author",
    "score",
    "upvote_ratio",
    "num_comments",
    "url",
    "permalink",
    "flair",
    "is_video",
    "created_utc",
    "created_local",
    "selftext_preview",
]

# Mimic a real browser to avoid 403s
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://old.reddit.com/",
    "DNT": "1",
}


def fetch_posts(sort: str, limit: int) -> list[dict]:
    """
    Fetch posts using old.reddit.com JSON endpoint with browser-like headers.
    Paginates automatically using the 'after' cursor.
    """
    rows = []
    after = None
    # old.reddit.com tends to be less aggressive with blocking
    base_url = f"https://old.reddit.com/r/soccer/{sort}.json"

    session = requests.Session()
    session.headers.update(HEADERS)

    # Warm up the session with a regular page visit first
    print("Warming up session...")
    try:
        session.get("https://old.reddit.com/r/soccer/", timeout=15)
        time.sleep(random.uniform(1.5, 2.5))
    except Exception:
        pass

    print(f"Fetching up to {limit} posts from r/soccer [{sort}] ...")

    while len(rows) < limit:
        batch_size = min(100, limit - len(rows))
        params = {"limit": batch_size, "raw_json": 1}
        if after:
            params["after"] = after

        try:
            response = session.get(base_url, params=params, timeout=15)
        except requests.RequestException as e:
            print(f"  Request failed: {e}")
            break

        if response.status_code == 429:
            wait = random.randint(15, 30)
            print(f"  Rate limited — waiting {wait}s...")
            time.sleep(wait)
            continue
        elif response.status_code == 403:
            print(f"  403 Forbidden — Reddit is blocking this request.")
            print("  Try running again in a few minutes, or use a VPN.")
            break
        elif response.status_code != 200:
            print(f"  Error {response.status_code}: {response.text[:300]}")
            break

        try:
            data = response.json()
        except Exception as e:
            print(f"  Failed to parse JSON: {e}")
            break

        children = data["data"]["children"]
        after = data["data"].get("after")

        if not children:
            print("  No more posts available.")
            break

        for child in children:
            post = child["data"]
            created_dt = datetime.fromtimestamp(post["created_utc"], tz=timezone.utc)
            rows.append({
                "post_id":          post["id"],
                "title":            post["title"],
                "author":           post.get("author", "[deleted]"),
                "score":            post["score"],
                "upvote_ratio":     post.get("upvote_ratio", ""),
                "num_comments":     post["num_comments"],
                "url":              post["url"],
                "permalink":        f"https://reddit.com{post['permalink']}",
                "flair":            post.get("link_flair_text") or "",
                "is_video":         post.get("is_video", False),
                "created_utc":      created_dt.isoformat(),
                "created_local":    created_dt.astimezone().isoformat(),
                "selftext_preview": (post.get("selftext") or "")[:200].replace("\n", " "),
            })

        print(f"  Collected {len(rows)} posts so far...")

        if not after:
            print("  Reached end of available posts.")
            break

        # Random delay to look more human
        time.sleep(random.uniform(1.5, 3.0))

    return rows[:limit]


def append_to_csv(rows: list[dict], output_path: Path) -> None:
    file_exists = output_path.exists() and output_path.stat().st_size > 0

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
            print(f"  Created new file: {output_path}")
        else:
            print(f"  Appending to existing file: {output_path}")
        writer.writerows(rows)

    total = sum(1 for _ in open(output_path, encoding="utf-8")) - 1
    print(f"  {len(rows)} rows written. Total rows in file: {total}")


def main():
    parser = argparse.ArgumentParser(description="Scrape r/soccer posts (no API key needed).")
    parser.add_argument("--sort",   default="hot", choices=["hot", "new", "top", "rising"])
    parser.add_argument("--limit",  default=200, type=int)
    parser.add_argument("--output", default="soccer_posts.csv")
    args = parser.parse_args()

    rows = fetch_posts(sort=args.sort, limit=args.limit)
    if rows:
        append_to_csv(rows, Path(args.output))
    else:
        print("\nNo posts collected — nothing written to CSV.")
    print("\nDone!")


if __name__ == "__main__":
    main()
