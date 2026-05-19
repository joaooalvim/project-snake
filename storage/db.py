import sqlite3
import json
from datetime import datetime
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS app_charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            country TEXT NOT NULL,
            category TEXT NOT NULL,
            rank INTEGER NOT NULL,
            app_id TEXT NOT NULL,
            app_name TEXT NOT NULL,
            developer TEXT,
            genre TEXT,
            fetched_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            summary TEXT,
            fetched_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            tweet_id TEXT UNIQUE,
            author TEXT,
            content TEXT NOT NULL,
            url TEXT,
            likes INTEGER DEFAULT 0,
            fetched_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            summary_json TEXT NOT NULL,
            email_sent INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def save_chart_entries(date: str, country: str, category: str, entries: list[dict]):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    conn.executemany(
        """INSERT OR IGNORE INTO app_charts
           (date, country, category, rank, app_id, app_name, developer, genre, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (date, country, category, e["rank"], e["app_id"], e["app_name"],
             e.get("developer"), e.get("genre"), now)
            for e in entries
        ],
    )
    conn.commit()
    conn.close()


def save_articles(date: str, source: str, articles: list[dict]):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    for a in articles:
        conn.execute(
            """INSERT OR IGNORE INTO articles (date, source, title, url, summary, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (date, source, a["title"], a["url"], a.get("summary"), now),
        )
    conn.commit()
    conn.close()


def save_tweets(date: str, tweets: list[dict]):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    for t in tweets:
        conn.execute(
            """INSERT OR IGNORE INTO tweets (date, tweet_id, author, content, url, likes, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (date, t.get("tweet_id"), t.get("author"), t["content"],
             t.get("url"), t.get("likes", 0), now),
        )
    conn.commit()
    conn.close()


def get_day_data(date: str) -> dict:
    conn = get_conn()
    charts = conn.execute(
        "SELECT * FROM app_charts WHERE date = ? ORDER BY country, category, rank", (date,)
    ).fetchall()
    articles = conn.execute(
        "SELECT * FROM articles WHERE date = ? ORDER BY source, id", (date,)
    ).fetchall()
    tweets = conn.execute(
        "SELECT * FROM tweets WHERE date = ? ORDER BY likes DESC", (date,)
    ).fetchall()
    conn.close()
    return {
        "charts": [dict(r) for r in charts],
        "articles": [dict(r) for r in articles],
        "tweets": [dict(r) for r in tweets],
    }


def save_digest(date: str, summary: dict, email_sent: bool = False):
    conn = get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO digests (date, summary_json, email_sent, created_at)
           VALUES (?, ?, ?, ?)""",
        (date, json.dumps(summary), int(email_sent), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_digest(date: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM digests WHERE date = ?", (date,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["summary"] = json.loads(d["summary_json"])
    return d


def list_digests(limit: int = 30) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT date, email_sent, created_at FROM digests ORDER BY date DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
