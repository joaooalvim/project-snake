"""
Formats and sends the daily digest email via Gmail SMTP.
Requires a Gmail App Password (not your regular password).
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import DIGEST_EMAIL, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD


def build_html(date: str, summary: dict) -> str:
    def ul(items):
        if not items:
            return "<p><em>No data</em></p>"
        return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

    articles_html = ""
    for a in summary.get("top_articles", []):
        articles_html += (
            f'<li><a href="{a.get("url", "#")}">{a.get("title", "")}</a>'
            f' — {a.get("why_it_matters", "")}</li>'
        )

    counts = summary.get("raw_counts", {})
    count_str = (
        f"{counts.get('chart_entries', '?')} chart entries · "
        f"{counts.get('articles', '?')} articles · "
        f"{counts.get('tweets', '?')} tweets"
    )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 680px; margin: 0 auto; color: #222; }}
  h1 {{ font-size: 22px; border-bottom: 2px solid #000; padding-bottom: 8px; }}
  h2 {{ font-size: 15px; text-transform: uppercase; letter-spacing: 0.05em; color: #555; margin-top: 28px; }}
  .headline {{ font-size: 18px; font-weight: 600; background: #f5f5f5; padding: 12px 16px; border-left: 4px solid #000; }}
  .meta {{ font-size: 12px; color: #999; margin-bottom: 24px; }}
  ul {{ padding-left: 20px; line-height: 1.7; }}
  a {{ color: #000; }}
</style>
</head>
<body>
  <h1>Project Snake — Daily Digest</h1>
  <p class="meta">{date} &nbsp;·&nbsp; {count_str} &nbsp;·&nbsp;
    <a href="http://localhost:8000">Open dashboard</a>
  </p>

  <div class="headline">{summary.get("headline", "No summary available.")}</div>

  <h2>Chart Highlights</h2>
  {ul(summary.get("chart_highlights", []))}

  <h2>Top Articles</h2>
  <ul>{articles_html or "<li><em>No articles today</em></li>"}</ul>

  <h2>Twitter Signals</h2>
  {ul(summary.get("twitter_signals", []))}

  <h2>Watch List</h2>
  {ul(summary.get("watch_list", []))}
</body>
</html>"""


def send_digest_email(date: str, summary: dict):
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[digest] SMTP credentials not set — skipping email")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Project Snake: {date} — {summary.get('headline', 'Daily digest')[:60]}"
    msg["From"] = SMTP_USER
    msg["To"] = DIGEST_EMAIL

    plain = summary.get("headline", "See HTML version.")
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(build_html(date, summary), "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, DIGEST_EMAIL, msg.as_string())
        print(f"[digest] email sent to {DIGEST_EMAIL}")
    except Exception as exc:
        print(f"[digest] email failed: {exc}")
