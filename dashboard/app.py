import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from storage.db import (
    init_db, get_breakouts, get_breakout_dates,
    get_articles, get_article_dates,
    get_trends, get_trend_dates, get_us_trends_24h,
    get_reddit_posts, get_reddit_dates,
)

app = FastAPI(title="Project Snake")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

init_db()

COUNTRY_FLAG = {
    "us": "🇺🇸", "ca": "🇨🇦", "gb": "🇬🇧", "de": "🇩🇪", "fr": "🇫🇷",
    "es": "🇪🇸", "br": "🇧🇷", "ro": "🇷🇴", "au": "🇦🇺", "nz": "🇳🇿", "za": "🇿🇦",
}
CHART_LABEL = {
    "free":               "Overall",
    "free_games":         "Games",
    "free_business":      "Business",
    "free_education":     "Education",
    "free_entertainment": "Entertainment",
    "free_finance":       "Finance",
    "free_food":          "Food & Drink",
    "free_health":        "Health & Fitness",
    "free_lifestyle":     "Lifestyle",
    "free_medical":       "Medical",
    "free_music":         "Music",
    "free_navigation":    "Navigation",
    "free_news":          "News",
    "free_photo":         "Photo & Video",
    "free_productivity":  "Productivity",
    "free_reference":     "Reference",
    "free_shopping":      "Shopping",
    "free_social":        "Social",
    "free_sports":        "Sports",
    "free_travel":        "Travel",
    "free_utilities":     "Utilities",
    "free_weather":       "Weather",
}
TREND_COUNTRIES = {
    "US": "🇺🇸", "GB": "🇬🇧", "CA": "🇨🇦", "AU": "🇦🇺",
    "BR": "🇧🇷", "DE": "🇩🇪", "FR": "🇫🇷", "ES": "🇪🇸",
}

# Pass shared dicts as context rather than env.globals (breaks on Python 3.12 + Jinja2 3.1.4+)
SHARED = {"COUNTRY_FLAG": COUNTRY_FLAG, "CHART_LABEL": CHART_LABEL, "TREND_COUNTRIES": TREND_COUNTRIES}


def _get_dates():
    b = {d["date"] for d in get_breakout_dates(60)}
    a = {d["date"] for d in get_article_dates(60)}
    t = {d["date"] for d in get_trend_dates(60)}
    r = {d["date"] for d in get_reddit_dates(60)}
    return sorted(b | a | t | r, reverse=True)


def _group_breakouts(rows: list) -> list:
    from collections import defaultdict
    by_app = defaultdict(list)
    for r in rows:
        by_app[r["app_id"]].append(r)
    grouped = []
    for app_id, app_rows in by_app.items():
        first = app_rows[0]
        grouped.append({
            **first,
            "countries":     [r["country"] for r in app_rows],
            "charts":        list({r["chart_type"] for r in app_rows}),
            "country_count": len(app_rows),
            "appstore_url":  f"https://apps.apple.com/app/id{app_id}",
        })
    return sorted(grouped, key=lambda x: (-x["country_count"], x["rank_today"]))


@app.get("/", response_class=RedirectResponse)
async def index():
    dates = _get_dates()
    latest = dates[0] if dates else date.today().isoformat()
    return RedirectResponse(f"/{latest}/breakouts")


@app.get("/{date_str}", response_class=RedirectResponse)
async def date_redirect(date_str: str):
    return RedirectResponse(f"/{date_str}/breakouts")


@app.get("/{date_str}/breakouts", response_class=HTMLResponse)
async def breakouts_page(request: Request, date_str: str):
    dates = _get_dates()
    grouped = _group_breakouts(get_breakouts(date_str))
    return templates.TemplateResponse("breakouts.html", {
        "request": request, "dates": dates,
        "selected_date": date_str, "breakouts": grouped,
        **SHARED,
    })


@app.get("/{date_str}/news", response_class=HTMLResponse)
async def news_page(request: Request, date_str: str):
    dates = _get_dates()
    return templates.TemplateResponse("news.html", {
        "request": request, "dates": dates,
        "selected_date": date_str, "articles": get_articles(date_str),
        **SHARED,
    })


@app.get("/{date_str}/trends", response_class=HTMLResponse)
async def trends_page(request: Request, date_str: str):
    dates = _get_dates()
    return templates.TemplateResponse("trends.html", {
        "request": request, "dates": dates,
        "selected_date": date_str, "trends": get_us_trends_24h(date_str),
        **SHARED,
    })


@app.get("/{date_str}/reddit", response_class=HTMLResponse)
async def reddit_page(request: Request, date_str: str):
    dates = _get_dates()
    posts = get_reddit_posts(date_str)
    from collections import defaultdict
    by_category = defaultdict(list)
    for p in posts:
        by_category[p["category"]].append(p)
    return templates.TemplateResponse("reddit.html", {
        "request": request, "dates": dates,
        "selected_date": date_str, "by_category": dict(by_category),
        "total": len(posts), **SHARED,
    })


@app.get("/api/breakouts/{date_str}")
async def api_breakouts(date_str: str):
    return _group_breakouts(get_breakouts(date_str))


@app.get("/api/news/{date_str}")
async def api_news(date_str: str):
    return get_articles(date_str)
