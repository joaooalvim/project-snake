"""
Main pipeline: collect App Store charts, detect breakouts, summarize, store.
Run this daily (via scheduler.py or directly: python pipeline.py).
"""
from datetime import date

from collectors import appstore, techcrunch, twitter, trends as trends_collector
from detectors import breakout as breakout_detector
from storage.db import (
    init_db, save_chart_entries, save_articles, save_tweets, save_trends,
    get_day_data, save_digest, get_breakouts,
)


def collect(today: str) -> dict:
    print(f"[pipeline] collecting charts for {today}")
    charts = appstore.fetch_all()
    for country, slugs in charts.items():
        for slug, entries in slugs.items():
            if entries:
                save_chart_entries(today, country, slug, entries)

    print("[pipeline] collecting articles + tweets")
    tc_articles = techcrunch.fetch()
    if tc_articles:
        save_articles(today, "techcrunch", tc_articles)
        print(f"  [techcrunch] {len(tc_articles)} articles")

    tweets = twitter.fetch()
    if tweets:
        save_tweets(today, tweets)
        print(f"  [twitter] {len(tweets)} tweets")

    print("[pipeline] collecting Google Trends")
    all_trends = trends_collector.fetch()
    for country, items in all_trends.items():
        if items:
            save_trends(today, country, items)

    return charts


def detect_breakouts(today: str, charts: dict):
    print("[pipeline] detecting breakouts...")
    found = breakout_detector.detect(today, charts)
    summary = breakout_detector.summarize(found)
    print(
        f"  {summary['unique_apps']} breakout apps "
        f"({len(summary['new_entries'])} new entries, {len(summary['rising'])} rising)"
    )
    return summary


def run(send_email: bool = True):
    init_db()
    today = date.today().isoformat()

    charts = collect(today)
    breakout_summary = detect_breakouts(today, charts)

    digest_data = {
        "breakouts": breakout_summary,
        "date": today,
    }
    save_digest(today, digest_data)

    if send_email:
        from digest import send_breakout_email
        breakouts_full = get_breakouts(today)
        send_breakout_email(today, breakout_summary, breakouts_full)

    print(f"[pipeline] done. {breakout_summary['unique_apps']} breakout apps detected.")


if __name__ == "__main__":
    run()
