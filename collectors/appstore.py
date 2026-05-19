"""
App Store top charts via Apple's public iTunes RSS feeds.
No API key required.
"""
import httpx
from config import APPSTORE_COUNTRIES, APPSTORE_CHART_SIZE

CATEGORIES = {
    "free": "https://itunes.apple.com/{country}/rss/topfreeapplications/limit={n}/json",
    "paid": "https://itunes.apple.com/{country}/rss/toppaidapplications/limit={n}/json",
    "grossing": "https://itunes.apple.com/{country}/rss/topgrossingapplications/limit={n}/json",
}


def fetch_chart(country: str, category: str) -> list[dict]:
    url = CATEGORIES[category].format(country=country, n=APPSTORE_CHART_SIZE)
    try:
        r = httpx.get(url, timeout=15)
        r.raise_for_status()
        entries = r.json()["feed"]["entry"]
        return [
            {
                "rank": i + 1,
                "app_id": e["id"]["attributes"]["im:id"],
                "app_name": e["im:name"]["label"],
                "developer": e.get("im:artist", {}).get("label"),
                "genre": e.get("category", {}).get("attributes", {}).get("label"),
            }
            for i, e in enumerate(entries)
        ]
    except Exception as exc:
        print(f"[appstore] {country}/{category} failed: {exc}")
        return []


def fetch_all() -> dict:
    results = {}
    for country in APPSTORE_COUNTRIES:
        results[country] = {}
        for category in CATEGORIES:
            results[country][category] = fetch_chart(country, category)
    return results
