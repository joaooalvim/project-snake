"""
FastAPI dashboard — browse digests and raw collected data.
Run: uvicorn dashboard.app:app --reload --port 8000
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from storage.db import init_db, list_digests, get_digest, get_day_data

app = FastAPI(title="Project Snake")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    digests = list_digests(30)
    latest_date = digests[0]["date"] if digests else date.today().isoformat()
    digest = get_digest(latest_date)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "digests": digests,
        "digest": digest,
        "selected_date": latest_date,
    })


@app.get("/digest/{date_str}", response_class=HTMLResponse)
async def digest_page(request: Request, date_str: str):
    digests = list_digests(30)
    digest = get_digest(date_str)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "digests": digests,
        "digest": digest,
        "selected_date": date_str,
    })


@app.get("/api/digest/{date_str}")
async def api_digest(date_str: str):
    return get_digest(date_str) or {}


@app.get("/api/raw/{date_str}")
async def api_raw(date_str: str):
    return get_day_data(date_str)
