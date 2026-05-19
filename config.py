import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DIGEST_EMAIL = os.getenv("DIGEST_EMAIL", "joaoalfig@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "joaoalfig@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# 11 countries to monitor
APPSTORE_COUNTRIES = ["us", "ca", "gb", "de", "fr", "es", "br", "ro", "au", "nz", "za"]

# Category charts to track — (slug, genre_id or None for overall)
# genre_id=None = overall Top Free chart
APPSTORE_CATEGORIES = {
    "free":              None,
    "free_games":        6014,
    "free_social":       6005,
    "free_entertainment":6016,
    "free_photo":        6008,
    "free_productivity": 6007,
    "free_finance":      6015,
}

APPSTORE_CHART_SIZE = 100  # track full top 100

DB_PATH = os.getenv("DB_PATH", "snake.db")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))

# Breakout detection thresholds
BREAKOUT_LOOKBACK_DAYS = 7    # days of history to check against
RISING_MIN_JUMP = 25          # rank must improve by at least this many positions
RISING_PREV_RANK_MIN = 50     # previous rank must have been worse than this

# Daily run time (24h UTC)
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "8"))
DIGEST_MINUTE = int(os.getenv("DIGEST_MINUTE", "0"))
