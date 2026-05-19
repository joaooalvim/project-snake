"""
TechCrunch articles via public RSS feed.
Filters for mobile/app ecosystem topics.
"""
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

RSS_URL = "https://techcrunch.com/feed/"
APP_KEYWORDS = {
    "app store", "google play", "mobile app", "ios", "android", "app ecosystem",
    "startup", "funding", "series a", "series b", "acqui", "ipo", "download",
    "developer", "sdk", "saas", "consumer app",
}
MAX_ARTICLES = 50


def fetch() -> list[dict]:
    try:
        r = httpx.get(RSS_URL, timeout=15, headers={"User-Agent": "project-snake/1.0"})
        r.raise_for_status()
    except Exception as exc:
        print(f"[techcrunch] RSS fetch failed: {exc}")
        return []

    root = ET.fromstring(r.text)
    channel = root.find("channel")
    articles = []

    for item in (channel.findall("item") if channel is not None else [])[:50]:
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()

        articles.append({"title": title, "url": url, "summary": description[:300]})
        if len(articles) >= MAX_ARTICLES:
            break

    return articles
