import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from storage.db import init_db, get_breakouts, get_breakout_dates, get_articles, get_article_dates

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

templates.env.globals["COUNTRY_FLAG"] = COUNTRY_FLAG
templates.env.globals["CHART_LABEL"] = CHART_LABEL


def _group_breakouts(rows: list) -> list:
    """Group by app_id, aggregate countries."""
    from collections import defaultdict
    by_app = defaultdict(list)
    for r in rows:
        by_app[r["app_id"]].append(r)
    grouped = []
    for app_id, app_rows in by_app.items():
        first = app_rows[0]
        grouped.append({
            **first,
            "countries": [r["country"] for r in app_rows],
            "charts":    list({r["chart_type"] for r in app_rows}),
            "country_count": len(app_rows),
            "appstore_url": f"https://apps.apple.com/app/id{app_id}",
        })
    return sorted(grouped, key=lambda x: (-x["country_count"], x["rank_today"]))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    dates = get_breakout_dates(60)
    if dates:
        latest = dates[0]["date"]
        rows = get_breakouts(latest)
        grouped = _group_breakouts(rows)
    else:
        latest = date.today().isoformat()
        grouped = []
    return templates.TemplateResponse("breakouts.html", {
        "request":       request,
        "dates":         dates,
        "selected_date": latest,
        "breakouts":     grouped,
    })


@app.get("/breakouts/{date_str}", response_class=HTMLResponse)
async def breakouts_page(request: Request, date_str: str):
    dates = get_breakout_dates(60)
    rows = get_breakouts(date_str)
    grouped = _group_breakouts(rows)
    return templates.TemplateResponse("breakouts.html", {
        "request":       request,
        "dates":         dates,
        "selected_date": date_str,
        "breakouts":     grouped,
    })


@app.get("/api/breakouts/{date_str}")
async def api_breakouts(date_str: str):
    rows = get_breakouts(date_str)
    return _group_breakouts(rows)


@app.get("/news", response_class=HTMLResponse)
async def news_index(request: Request):
    dates = get_article_dates(60)
    latest = dates[0]["date"] if dates else date.today().isoformat()
    articles = get_articles(latest)
    return templates.TemplateResponse("news.html", {
        "request": request, "dates": dates,
        "selected_date": latest, "articles": articles,
    })


@app.get("/news/{date_str}", response_class=HTMLResponse)
async def news_page(request: Request, date_str: str):
    dates = get_article_dates(60)
    articles = get_articles(date_str)
    return templates.TemplateResponse("news.html", {
        "request": request, "dates": dates,
        "selected_date": date_str, "articles": articles,
    })
