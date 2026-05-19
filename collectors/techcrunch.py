"""
TechCrunch articles via public RSS feed.
Fetches og:image from each article page for thumbnails.
"""
import httpx
import xml.etree.ElementTree as ET
import re

RSS_URL = "https://techcrunch.com/feed/"
MAX_ARTICLES = 50
HEADERS = {"User-Agent": "project-snake/1.0"}


def _og_image(url: str) -> str:
    try:
        r = httpx.get(url, timeout=10, headers=HEADERS, follow_redirects=True)
        match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)["\']', r.text)
        if not match:
            match = re.search(r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+property=["\']og:image["\']', r.text)
        return match.group(1) if match else ""
    except Exception:
        return ""


def fetch() -> list:
    try:
        r = httpx.get(RSS_URL, timeout=15, headers=HEADERS)
        r.raise_for_status()
    except Exception as exc:
        print(f"[techcrunch] RSS fetch failed: {exc}")
        return []

    root = ET.fromstring(r.text)
    channel = root.find("channel")
    articles = []

    for item in (channel.findall("item") if channel is not None else [])[:MAX_ARTICLES]:
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        articles.append({"title": title, "url": url, "summary": description[:300]})

    print(f"  [techcrunch] fetching images for {len(articles)} articles...")
    for a in articles:
        a["image_url"] = _og_image(a["url"])

    return articles
