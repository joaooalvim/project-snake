"""
Main pipeline: collect data from all sources, summarize with Claude, store results.
Run this daily (via scheduler.py or cron).
"""
from datetime import date
import anthropic

from config import ANTHROPIC_API_KEY
from collectors import appstore, techcrunch, twitter
from storage.db import (
    init_db, save_chart_entries, save_articles, save_tweets,
    get_day_data, save_digest,
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def collect(today: str):
    print(f"[pipeline] collecting data for {today}")

    # App Store charts
    charts = appstore.fetch_all()
    for country, categories in charts.items():
        for category, entries in categories.items():
            if entries:
                save_chart_entries(today, country, category, entries)
                print(f"  [appstore] {country}/{category}: {len(entries)} apps")

    # TechCrunch
    tc_articles = techcrunch.fetch()
    if tc_articles:
        save_articles(today, "techcrunch", tc_articles)
        print(f"  [techcrunch] {len(tc_articles)} articles")

    # Twitter
    tweets = twitter.fetch()
    if tweets:
        save_tweets(today, tweets)
        print(f"  [twitter] {len(tweets)} tweets")


def summarize(today: str) -> dict:
    data = get_day_data(today)

    # Build a compact text representation for Claude
    chart_lines = []
    for entry in data["charts"]:
        chart_lines.append(
            f"  [{entry['country'].upper()} {entry['category']}] #{entry['rank']} {entry['app_name']}"
            + (f" by {entry['developer']}" if entry.get("developer") else "")
        )

    article_lines = [f"  - {a['title']} ({a['source']})" for a in data["articles"]]
    tweet_lines = [f"  - @{t['author']}: {t['content'][:140]}" for t in data["tweets"][:20]]

    prompt = f"""You are an app ecosystem analyst. Below is raw surveillance data collected on {today}.

=== APP STORE CHARTS (top apps by country/category) ===
{chr(10).join(chart_lines[:60]) or "No data"}

=== TECHCRUNCH ARTICLES ===
{chr(10).join(article_lines) or "No data"}

=== TWITTER SIGNALS ===
{chr(10).join(tweet_lines) or "No data"}

Produce a concise daily digest in JSON with these exact keys:
{{
  "headline": "one-sentence summary of the most important trend today",
  "chart_highlights": ["3-5 bullet strings about notable chart movements or patterns"],
  "top_articles": [{{"title": str, "why_it_matters": str, "url": str}}],
  "twitter_signals": ["2-4 notable tweets or themes worth tracking"],
  "watch_list": ["apps or companies to keep an eye on based on today's data"],
  "raw_counts": {{"chart_entries": N, "articles": N, "tweets": N}}
}}

Be specific. Mention app names, developers, countries. Skip filler."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    import json, re
    text = message.content[0].text
    # extract JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            summary = json.loads(match.group())
            summary["raw_counts"] = {
                "chart_entries": len(data["charts"]),
                "articles": len(data["articles"]),
                "tweets": len(data["tweets"]),
            }
            return summary
        except json.JSONDecodeError:
            pass

    return {"headline": text[:200], "raw_counts": {
        "chart_entries": len(data["charts"]),
        "articles": len(data["articles"]),
        "tweets": len(data["tweets"]),
    }}


def run(send_email: bool = True):
    init_db()
    today = date.today().isoformat()
    collect(today)
    print("[pipeline] summarizing with Claude...")
    summary = summarize(today)
    save_digest(today, summary)
    print(f"[pipeline] digest saved: {summary.get('headline', '')}")

    if send_email:
        from digest import send_digest_email
        send_digest_email(today, summary)


if __name__ == "__main__":
    run()
