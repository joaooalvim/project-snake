"""
Twitter/X collection via Nitter RSS (no API key required).
Falls back gracefully if Nitter instances are down.
"""
import httpx
import xml.etree.ElementTree as ET

# Public Nitter instances — try in order
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]

# Searches and accounts to monitor
SEARCH_QUERIES = [
    "app store charts",
    "mobile app launch",
    "app ecosystem",
    "top apps",
    "consumer app funding",
]

ACCOUNTS = [
    "benedictevans",
    "mobiledevmemo",
    "eric_seufert",
    "andrewchen",
]


def _fetch_nitter_rss(path: str) -> list[dict]:
    for base in NITTER_INSTANCES:
        try:
            r = httpx.get(f"{base}{path}", timeout=10,
                          headers={"User-Agent": "project-snake/1.0"})
            if r.status_code == 200:
                return _parse_rss(r.text)
        except Exception:
            continue
    return []


def _parse_rss(xml_text: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        items = []
        for item in (channel.findall("item") if channel is not None else [])[:5]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            creator = item.findtext("{http://purl.org/dc/elements/1.1/}creator") or ""
            items.append({
                "content": title,
                "url": link,
                "author": creator.lstrip("@"),
                "tweet_id": link.split("/")[-1] if link else None,
                "likes": 0,
            })
        return items
    except Exception:
        return []


def fetch() -> list[dict]:
    results = []

    for query in SEARCH_QUERIES:
        encoded = query.replace(" ", "+")
        results.extend(_fetch_nitter_rss(f"/search/rss?q={encoded}&f=tweets"))

    for account in ACCOUNTS:
        results.extend(_fetch_nitter_rss(f"/{account}/rss"))

    # deduplicate by tweet_id / url
    seen = set()
    unique = []
    for t in results:
        key = t.get("tweet_id") or t.get("url") or t["content"]
        if key not in seen:
            seen.add(key)
            unique.append(t)

    return unique
