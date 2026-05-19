"""
Sends the daily breakout digest email via Gmail SMTP.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import DIGEST_EMAIL, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

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


def _flags(countries):
    return " ".join(COUNTRY_FLAG.get(c.lower(), c.upper()) for c in countries)


def _app_row(app: dict, show_prev: bool = False) -> str:
    countries = _flags(app["countries"])
    chart = CHART_LABEL.get(app["chart_type"], app["chart_type"])
    rank_info = f"#{app['rank_today']}"
    if show_prev and app.get("rank_prev"):
        rank_info += f" (was #{app['rank_prev']})"
    multi = f" <span style='color:#888;font-size:11px'>{app['country_count']} countries</span>" if app["country_count"] > 1 else ""
    return (
        f"<li style='padding:10px 0;border-bottom:1px solid #1e1e1e'>"
        f"<a href='{app['appstore_url']}' style='color:#fff;font-weight:600;text-decoration:none'>{app['app_name']}</a>{multi}<br>"
        f"<span style='color:#888;font-size:12px'>{app.get('developer','')} &nbsp;·&nbsp; {chart} &nbsp;·&nbsp; {rank_info} &nbsp;·&nbsp; {countries}</span>"
        f"</li>"
    )


def build_html(date: str, summary: dict) -> str:
    new_entries = summary.get("new_entries", [])
    rising = summary.get("rising", [])

    new_html = "".join(_app_row(a) for a in new_entries[:25]) or "<li style='color:#555'>No new entries today (need more historical data)</li>"
    rising_html = "".join(_app_row(a, show_prev=True) for a in rising[:15]) or "<li style='color:#555'>No rising apps today</li>"

    return f"""<!DOCTYPE html>
<html>
<head><meta charset='utf-8'>
<style>
  body {{font-family:-apple-system,sans-serif;background:#0a0a0a;color:#e8e8e8;max-width:680px;margin:0 auto;padding:24px}}
  h1 {{font-size:20px;border-bottom:1px solid #222;padding-bottom:12px;margin-bottom:4px}}
  h2 {{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:#555;margin:28px 0 10px}}
  ul {{list-style:none;padding:0;margin:0}}
  .meta {{font-size:12px;color:#444;margin-bottom:24px}}
  a {{color:#fff}}
</style>
</head>
<body>
  <h1>Project Snake — Breakout Apps</h1>
  <p class='meta'>{date} &nbsp;·&nbsp; {summary.get('unique_apps',0)} breakout apps across 11 countries &nbsp;·&nbsp;
    <a href='http://localhost:8000/breakouts/{date}' style='color:#888'>Open dashboard</a>
  </p>

  <h2>New Entries — appeared in top 100 for the first time in 7 days</h2>
  <ul>{new_html}</ul>

  <h2>Rising — jumped 25+ positions</h2>
  <ul>{rising_html}</ul>
</body>
</html>"""


def send_breakout_email(date: str, summary: dict, breakouts_full: list = None):
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[digest] SMTP credentials not set — skipping email")
        return

    unique = summary.get("unique_apps", 0)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Snake {date}: {unique} breakout apps detected"
    msg["From"] = SMTP_USER
    msg["To"] = DIGEST_EMAIL

    msg.attach(MIMEText(f"{unique} breakout apps detected on {date}.", "plain"))
    msg.attach(MIMEText(build_html(date, summary), "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, DIGEST_EMAIL, msg.as_string())
        print(f"[digest] email sent to {DIGEST_EMAIL}")
    except Exception as exc:
        print(f"[digest] email failed: {exc}")
