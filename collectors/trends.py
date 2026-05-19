"""
Google Trends daily trending searches via public RSS feed.
No API key required. Returns topic, search volume, image, and related news.
"""
import httpx
import json
import xml.etree.ElementTree as ET

RSS_URL = "https://trends.google.com/trending/rss?geo={geo}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
HT = "https://trends.google.com/trending/rss"
NS = {"ht": HT}

COUNTRIES = {
    "US": "🇺🇸", "GB": "🇬🇧", "CA": "🇨🇦", "AU": "🇦🇺",
    "BR": "🇧🇷", "DE": "🇩🇪", "FR": "🇫🇷", "ES": "🇪🇸",
}


def _fetch_country(geo: str) -> list:
    try:
        r = httpx.get(RSS_URL.format(geo=geo), timeout=15, headers=HEADERS)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        channel = root.find("channel")
        items = []
        for rank, item in enumerate(channel.findall("item"), 1):
            title     = item.findtext("title", "").strip()
            traffic   = item.findtext(f"{{{HT}}}approx_traffic", "").strip()
            picture   = item.findtext(f"{{{HT}}}picture", "").strip()
            pic_src   = item.findtext(f"{{{HT}}}picture_source", "").strip()
            news = []
            for ni in item.findall(f"{{{HT}}}news_item"):
                ni_title = ni.findtext(f"{{{HT}}}news_item_title", "").strip()
                ni_url   = ni.findtext(f"{{{HT}}}news_item_url", "").strip()
                ni_src   = ni.findtext(f"{{{HT}}}news_item_source", "").strip()
                ni_pic   = ni.findtext(f"{{{HT}}}news_item_picture", "").strip()
                if ni_title and ni_url:
                    news.append({"title": ni_title, "url": ni_url, "source": ni_src, "picture": ni_pic})
            items.append({
                "rank":        rank,
                "topic":       title,
                "traffic":     traffic,
                "picture_url": picture,
                "pic_source":  pic_src,
                "news":        news,
            })
        return items
    except Exception as exc:
        print(f"  [trends] {geo} failed: {exc}")
        return []


def fetch() -> dict:
    """Returns {geo: [trend items]}"""
    results = {}
    for geo in COUNTRIES:
        items = _fetch_country(geo)
        results[geo] = items
        if items:
            print(f"  [trends] {geo}: {len(items)} trending topics")
    return results
