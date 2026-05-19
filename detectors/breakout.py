"""
Breakout detector: finds apps that newly entered or sharply rose in App Store charts.

new_entry  — app_id not seen in this (country, chart_type) in the past 7 days
rising     — app was ranked ≥50 and jumped ≥25 positions to reach top 100

Cross-country signal: the same app breaking out in multiple countries
simultaneously is a stronger signal — this is surfaced via country_count
in the breakouts table.
"""
from datetime import date, timedelta
from config import BREAKOUT_LOOKBACK_DAYS, RISING_MIN_JUMP, RISING_PREV_RANK_MIN
from storage.db import get_recent_app_ids, get_last_rank, save_breakouts


def detect(today: str, charts: dict) -> list:
    """
    charts: {country: {chart_slug: [entries]}}
    Returns list of breakout dicts, also saves them to DB.
    """
    since = (date.fromisoformat(today) - timedelta(days=BREAKOUT_LOOKBACK_DAYS)).isoformat()
    found = []

    for country, slugs in charts.items():
        for chart_slug, entries in slugs.items():
            if not entries:
                continue

            # App IDs seen in this chart in the lookback window (excluding today)
            historical_ids = get_recent_app_ids(country, chart_slug, since, today)

            for entry in entries:
                app_id    = entry["app_id"]
                rank_now  = entry["rank"]

                last = get_last_rank(app_id, country, chart_slug, today)

                if app_id not in historical_ids:
                    # Never seen in lookback window → new entry
                    found.append({
                        "date":          today,
                        "app_id":        app_id,
                        "app_name":      entry["app_name"],
                        "developer":     entry.get("developer"),
                        "icon_url":      entry.get("icon_url"),
                        "chart_type":    chart_slug,
                        "country":       country,
                        "rank_today":    rank_now,
                        "rank_prev":     last[1] if last else None,
                        "prev_date":     last[0] if last else None,
                        "breakout_type": "new_entry",
                    })
                elif last and last[1] >= RISING_PREV_RANK_MIN:
                    jump = last[1] - rank_now
                    if jump >= RISING_MIN_JUMP:
                        # Was deep in chart, now rising fast
                        found.append({
                            "date":          today,
                            "app_id":        app_id,
                            "app_name":      entry["app_name"],
                            "developer":     entry.get("developer"),
                            "icon_url":      entry.get("icon_url"),
                            "chart_type":    chart_slug,
                            "country":       country,
                            "rank_today":    rank_now,
                            "rank_prev":     last[1],
                            "prev_date":     last[0],
                            "breakout_type": "rising",
                        })

    save_breakouts(found)
    return found


def summarize(breakouts: list) -> dict:
    """
    Groups breakout list into a structured summary for digest/display.
    Apps breaking in multiple countries are ranked higher.
    """
    from collections import defaultdict

    # Group by app_id to count cross-country breakouts
    by_app = defaultdict(list)
    for b in breakouts:
        by_app[b["app_id"]].append(b)

    ranked = sorted(by_app.values(), key=lambda rows: (-len(rows), rows[0]["rank_today"]))

    new_entries = []
    rising = []

    for rows in ranked:
        countries = [r["country"].upper() for r in rows]
        first = rows[0]
        item = {
            "app_name":      first["app_name"],
            "developer":     first.get("developer", ""),
            "app_id":        first["app_id"],
            "icon_url":      first.get("icon_url", ""),
            "rank_today":    first["rank_today"],
            "rank_prev":     first.get("rank_prev"),
            "chart_type":    first["chart_type"],
            "countries":     countries,
            "country_count": len(countries),
            "breakout_type": first["breakout_type"],
            "appstore_url":  f"https://apps.apple.com/app/id{first['app_id']}",
        }
        if first["breakout_type"] == "new_entry":
            new_entries.append(item)
        else:
            rising.append(item)

    return {
        "new_entries": new_entries[:30],
        "rising":      rising[:20],
        "total":       len(breakouts),
        "unique_apps": len(by_app),
    }
