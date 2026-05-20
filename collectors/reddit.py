"""
Reddit hot posts via public JSON API. No auth required.
"""
import httpx
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.reddit.com/",
}

SUBREDDITS = {
    # Painpoints & revolts
    "rant":             "Painpoints",
    "offmychest":       "Painpoints",
    "AmItheAsshole":    "Painpoints",
    "unpopularopinion": "Painpoints",
    # Culture & what's happening
    "OutOfTheLoop":     "Culture",
    "TrueOffMyChest":   "Culture",
    "AskReddit":        "Culture",
    # Generational
    "GenZ":             "Generational",
    "Millennials":      "Generational",
    "antiwork":         "Generational",
}

LIMIT = 25


def fetch_subreddit(subreddit: str) -> list:
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={LIMIT}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        r.raise_for_status()
        posts = r.json()["data"]["children"]
        return [
            {
                "post_id":      p["data"]["id"],
                "subreddit":    subreddit,
                "title":        p["data"]["title"],
                "score":        p["data"]["score"],
                "num_comments": p["data"]["num_comments"],
                "permalink":    "https://reddit.com" + p["data"]["permalink"],
                "url":          p["data"].get("url", ""),
                "is_self":      p["data"]["is_self"],
            }
            for p in posts
            if not p["data"].get("stickied")
        ]
    except Exception as exc:
        print(f"  [reddit] r/{subreddit} failed: {exc}")
        return []


def fetch() -> list:
    all_posts = []
    for subreddit, category in SUBREDDITS.items():
        posts = fetch_subreddit(subreddit)
        for p in posts:
            p["category"] = category
        all_posts.extend(posts)
        print(f"  [reddit] r/{subreddit}: {len(posts)} posts")
        time.sleep(1)  # be polite, avoid rate limiting
    return all_posts
