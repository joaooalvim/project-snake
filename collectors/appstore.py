"""
App Store top 100 charts via Apple's public iTunes RSS feeds.
Tracks overall + category-specific free charts across 11 countries.
No API key required.
"""
import httpx
from config import APPSTORE_COUNTRIES, APPSTORE_CATEGORIES, APPSTORE_CHART_SIZE

BASE_URL = "https://itunes.apple.com/{country}/rss/topfreeapplications/limit={n}{genre}/json"


def _chart_url(country: str, genre_id: int = None) -> str:
    genre_part = f"/genre={genre_id}" if genre_id else ""
    return BASE_URL.format(country=country, n=APPSTORE_CHART_SIZE, genre=genre_part)


def fetch_chart(country: str, chart_slug: str, genre_id: int = None) -> list[dict]:
    url = _chart_url(country, genre_id)
    try:
        r = httpx.get(url, timeout=15, headers={"User-Agent": "project-snake/1.0"})
        r.raise_for_status()
        data = r.json()
        entries = data.get("feed", {}).get("entry", [])
        if not entries:
            return []
        return [
            {
                "rank":      i + 1,
                "app_id":    e["id"]["attributes"]["im:id"],
                "app_name":  e["im:name"]["label"],
                "developer": e.get("im:artist", {}).get("label", ""),
                "genre":     e.get("category", {}).get("attributes", {}).get("label", ""),
                "icon_url":  e.get("im:image", [{}])[-1].get("label", ""),
            }
            for i, e in enumerate(entries)
        ]
    except Exception as exc:
        print(f"  [appstore] {country}/{chart_slug} failed: {exc}")
        return []


def fetch_all() -> dict:
    """Returns {country: {chart_slug: [entries]}}"""
    results = {}
    for country in APPSTORE_COUNTRIES:
        results[country] = {}
        for slug, genre_id in APPSTORE_CATEGORIES.items():
            entries = fetch_chart(country, slug, genre_id)
            results[country][slug] = entries
            if entries:
                print(f"  [appstore] {country}/{slug}: {len(entries)} apps")
    return results
