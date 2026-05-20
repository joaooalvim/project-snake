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
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            country     TEXT NOT NULL,
            category    TEXT NOT NULL,
            rank        INTEGER NOT NULL,
            app_id      TEXT NOT NULL,
            app_name    TEXT NOT NULL,
            developer   TEXT,
            genre       TEXT,
            icon_url    TEXT,
            fetched_at  TEXT NOT NULL,
            UNIQUE(date, country, category, app_id)
        );

        CREATE INDEX IF NOT EXISTS idx_charts_lookup
            ON app_charts(country, category, date, app_id);

        CREATE TABLE IF NOT EXISTS breakouts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT NOT NULL,
            app_id          TEXT NOT NULL,
            app_name        TEXT NOT NULL,
            developer       TEXT,
            icon_url        TEXT,
            chart_type      TEXT NOT NULL,
            country         TEXT NOT NULL,
            rank_today      INTEGER NOT NULL,
            rank_prev       INTEGER,
            prev_date       TEXT,
            breakout_type   TEXT NOT NULL,
            detected_at     TEXT NOT NULL,
            UNIQUE(date, app_id, chart_type, country)
        );

        CREATE INDEX IF NOT EXISTS idx_breakouts_date
            ON breakouts(date DESC);

        CREATE TABLE IF NOT EXISTS reddit_posts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT NOT NULL,
            post_id      TEXT NOT NULL UNIQUE,
            subreddit    TEXT NOT NULL,
            category     TEXT NOT NULL,
            title        TEXT NOT NULL,
            score        INTEGER DEFAULT 0,
            num_comments INTEGER DEFAULT 0,
            permalink    TEXT,
            fetched_at   TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_reddit_date ON reddit_posts(date DESC);

        CREATE TABLE IF NOT EXISTS trends (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            country     TEXT NOT NULL,
            rank        INTEGER NOT NULL,
            topic       TEXT NOT NULL,
            traffic     TEXT,
            picture_url TEXT,
            pic_source  TEXT,
            news_json   TEXT,
            fetched_at  TEXT NOT NULL,
            UNIQUE(date, country, topic)
        );

        CREATE INDEX IF NOT EXISTS idx_trends_date ON trends(date DESC);

        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            source      TEXT NOT NULL,
            title       TEXT NOT NULL,
            url         TEXT NOT NULL UNIQUE,
            summary     TEXT,
            image_url   TEXT,
            fetched_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tweets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            tweet_id    TEXT UNIQUE,
            author      TEXT,
            content     TEXT NOT NULL,
            url         TEXT,
            likes       INTEGER DEFAULT 0,
            fetched_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS digests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL UNIQUE,
            summary_json TEXT NOT NULL,
            email_sent  INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def save_chart_entries(date: str, country: str, category: str, entries: list):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    conn.executemany(
        """INSERT OR IGNORE INTO app_charts
           (date, country, category, rank, app_id, app_name, developer, genre, icon_url, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (date, country, category, e["rank"], e["app_id"], e["app_name"],
             e.get("developer"), e.get("genre"), e.get("icon_url"), now)
            for e in entries
        ],
    )
    conn.commit()
    conn.close()


def get_recent_app_ids(country: str, category: str, since_date: str, before_date: str) -> set:
    """Return set of app_ids that appeared in this chart between since_date and before_date."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT DISTINCT app_id FROM app_charts
           WHERE country = ? AND category = ? AND date >= ? AND date < ?""",
        (country, category, since_date, before_date),
    ).fetchall()
    conn.close()
    return {r["app_id"] for r in rows}


def get_last_rank(app_id: str, country: str, category: str, before_date: str):
    """Return (date, rank) of the most recent chart appearance before today, or None."""
    conn = get_conn()
    row = conn.execute(
        """SELECT date, rank FROM app_charts
           WHERE app_id = ? AND country = ? AND category = ? AND date < ?
           ORDER BY date DESC LIMIT 1""",
        (app_id, country, category, before_date),
    ).fetchone()
    conn.close()
    return (row["date"], row["rank"]) if row else None


def save_breakouts(breakouts: list):
    if not breakouts:
        return
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    conn.executemany(
        """INSERT OR IGNORE INTO breakouts
           (date, app_id, app_name, developer, icon_url, chart_type, country,
            rank_today, rank_prev, prev_date, breakout_type, detected_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (b["date"], b["app_id"], b["app_name"], b.get("developer"),
             b.get("icon_url"), b["chart_type"], b["country"],
             b["rank_today"], b.get("rank_prev"), b.get("prev_date"),
             b["breakout_type"], now)
            for b in breakouts
        ],
    )
    conn.commit()
    conn.close()


def get_breakouts(date: str) -> list:
    conn = get_conn()
    rows = conn.execute(
        """SELECT *, COUNT(*) OVER (PARTITION BY date, app_id) as country_count
           FROM breakouts WHERE date = ?
           ORDER BY country_count DESC, rank_today ASC""",
        (date,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_breakout_dates(limit: int = 30) -> list:
    conn = get_conn()
    rows = conn.execute(
        """SELECT date, COUNT(*) as count FROM breakouts
           GROUP BY date ORDER BY date DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_reddit_posts(date: str, posts: list):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    conn.executemany(
        """INSERT OR IGNORE INTO reddit_posts
           (date, post_id, subreddit, category, title, score, num_comments, permalink, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(date, p["post_id"], p["subreddit"], p["category"],
          p["title"], p["score"], p["num_comments"], p["permalink"], now)
         for p in posts],
    )
    conn.commit()
    conn.close()


def get_reddit_posts(date: str) -> list:
    conn = get_conn()
    rows = conn.execute(
        """SELECT * FROM reddit_posts WHERE date = ?
           ORDER BY category, score DESC""",
        (date,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_reddit_dates(limit: int = 60) -> list:
    conn = get_conn()
    rows = conn.execute(
        """SELECT date, COUNT(*) as count FROM reddit_posts
           GROUP BY date ORDER BY date DESC LIMIT ?""", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_trends(date: str, country: str, items: list):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    conn.executemany(
        """INSERT OR IGNORE INTO trends
           (date, country, rank, topic, traffic, picture_url, pic_source, news_json, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(date, country, t["rank"], t["topic"], t.get("traffic"),
          t.get("picture_url"), t.get("pic_source"), json.dumps(t.get("news", [])), now)
         for t in items],
    )
    conn.commit()
    conn.close()


def get_trends(date: str) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM trends WHERE date = ? ORDER BY country, rank", (date,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["news"] = json.loads(d["news_json"] or "[]")
        result.append(d)
    return result


def get_us_trends_24h(today: str) -> list:
    """US trends for today only."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM trends WHERE country = 'US' AND date = ? ORDER BY rank ASC",
        (today,),
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["news"] = json.loads(d["news_json"] or "[]")
        result.append(d)
    return result


def get_trend_dates(limit: int = 60) -> list:
    conn = get_conn()
    rows = conn.execute(
        """SELECT date, COUNT(DISTINCT topic) as count FROM trends
           GROUP BY date ORDER BY date DESC LIMIT ?""", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_articles(date: str) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM articles WHERE date = ? ORDER BY id", (date,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_article_dates(limit: int = 60) -> list:
    conn = get_conn()
    rows = conn.execute(
        """SELECT date, COUNT(*) as count FROM articles
           GROUP BY date ORDER BY date DESC LIMIT ?""", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_articles(date: str, source: str, articles: list):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    for a in articles:
        conn.execute(
            """INSERT OR IGNORE INTO articles (date, source, title, url, summary, image_url, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (date, source, a["title"], a["url"], a.get("summary"), a.get("image_url"), now),
        )
    conn.commit()
    conn.close()


def save_tweets(date: str, tweets: list):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    for t in tweets:
        conn.execute(
            """INSERT OR IGNORE INTO tweets
               (date, tweet_id, author, content, url, likes, fetched_at)
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


def get_digest(date: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM digests WHERE date = ?", (date,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["summary"] = json.loads(d["summary_json"])
    return d


def list_digests(limit: int = 30) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT date, email_sent, created_at FROM digests ORDER BY date DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
