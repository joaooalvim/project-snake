import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DIGEST_EMAIL = os.getenv("DIGEST_EMAIL", "joaoalfig@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Gmail App Password

APPSTORE_COUNTRIES = ["us", "gb", "br", "de", "jp"]
APPSTORE_CHART_SIZE = 10  # top N apps per chart per country

DB_PATH = os.getenv("DB_PATH", "snake.db")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))

# Daily run time (24h format, local timezone)
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "8"))
DIGEST_MINUTE = int(os.getenv("DIGEST_MINUTE", "0"))
