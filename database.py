"""
database.py — SQLite backend for Censational Social Media Manager
Tables: users, clients, caption_examples, generation_history, client_keywords, keyword_usage_log, caption_ratings
"""

import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "captions.db")


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                email           TEXT    NOT NULL UNIQUE,
                password_hash   TEXT    NOT NULL,
                name            TEXT    NOT NULL,
                role            TEXT    NOT NULL DEFAULT 'user' CHECK(role IN ('master','user')),
                business_name   TEXT    DEFAULT '',
                website_url     TEXT    DEFAULT '',
                created_at      TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS clients (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL UNIQUE,
                industry    TEXT,
                brand_voice TEXT,
                target_audience TEXT,
                platforms   TEXT,
                notes       TEXT,
                owner_id    INTEGER DEFAULT NULL REFERENCES users(id),
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS caption_examples (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id   INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                caption     TEXT    NOT NULL,
                label       TEXT    NOT NULL CHECK(label IN ('good','bad','used')),
                context     TEXT,
                platform    TEXT,
                engagement  TEXT,
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS generation_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id    INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                batch_desc   TEXT    NOT NULL,
                platform     TEXT,
                num_captions INTEGER,
                captions_json TEXT,
                created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS client_keywords (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id   INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                keyword     TEXT    NOT NULL,
                category    TEXT    DEFAULT 'general',
                priority    TEXT    DEFAULT 'normal' CHECK(priority IN ('high','normal','low')),
                use_count   INTEGER DEFAULT 0,
                last_used   TEXT,
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, keyword)
            );

            CREATE TABLE IF NOT EXISTS keyword_usage_log (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id     INTEGER NOT NULL,
                keyword_id    INTEGER NOT NULL REFERENCES client_keywords(id) ON DELETE CASCADE,
                generation_id INTEGER,
                used_at       TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS caption_ratings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id       INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                caption_text    TEXT    NOT NULL,
                hashtags        TEXT    DEFAULT '',
                platform        TEXT    DEFAULT '',
                batch_desc      TEXT    DEFAULT '',
                rating          INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                saved_as        TEXT,
                notes           TEXT,
                created_at      TEXT    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Safe migration: add owner_id column to existing clients table if missing
        try:
            conn.execute("SELECT owner_id FROM clients LIMIT 1")
        except Exception:
            try:
                conn.execute("ALTER TABLE clients ADD COLUMN owner_id INTEGER DEFAULT NULL REFERENCES users(id)")
            except Exception:
                pass


# ── Password Hashing ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a salt."""
    salt = "censational_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


# ── User Operations ──────────────────────────────────────────────────────────

def create_user(email: str, password: str, name: str, role: str = "user",
                business_name: str = "", website_url: str = ""):
    """Create a new user account. Returns the user dict or raises on duplicate."""
    pw_hash = hash_password(password)
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO users (email, password_hash, name, role, business_name, website_url)
               VALUES (?,?,?,?,?,?)""",
            (email.lower().strip(), pw_hash, name.strip(), role, business_name, website_url)
        )
        row = conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
        return dict(row) if row else None


def authenticate_user(email: str, password: str):
    """Check email/password against the users table. Returns user dict or None."""
    pw_hash = hash_password(password)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email=? AND password_hash=?",
            (email.lower().strip(), pw_hash)
        ).fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str):
    """Look up a user by email."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int):
    """Look up a user by ID."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_all_users():
    """Return all users (master-only function)."""
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM users ORDER BY created_at DESC")]


# ── Client Operations ─────────────────────────────────────────────────────────

def add_client(name, industry="", brand_voice="", target_audience="", platforms="", notes="", owner_id=None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO clients (name, industry, brand_voice, target_audience, platforms, notes, owner_id) VALUES (?,?,?,?,?,?,?)",
            (name, industry, brand_voice, target_audience, platforms, notes, owner_id)
        )


def get_clients(owner_id=None):
    """Get clients. If owner_id is None, returns ALL clients (master mode).
    If owner_id is set, returns only that user's clients."""
    with get_conn() as conn:
        if owner_id is not None:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM clients WHERE owner_id=? ORDER BY name", (owner_id,)
            )]
        return [dict(r) for r in conn.execute("SELECT * FROM clients ORDER BY name")]


def get_client(client_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        return dict(row) if row else None


def update_client(client_id, **kwargs):
    allowed = {"name","industry","brand_voice","target_audience","platforms","notes"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [client_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE clients SET {set_clause} WHERE id=?", values)


def delete_client(client_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM clients WHERE id=?", (client_id,))


# ── Caption Example Operations ───────────────────────────────────────────────

def add_example(client_id, caption, label, context="", platform="", engagement=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO caption_examples (client_id, caption, label, context, platform, engagement) VALUES (?,?,?,?,?,?)",
            (client_id, caption, label, context, platform, engagement)
        )


def get_examples(client_id, label=None):
    with get_conn() as conn:
        if label:
            rows = conn.execute(
                "SELECT * FROM caption_examples WHERE client_id=? AND label=? ORDER BY created_at DESC",
                (client_id, label)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM caption_examples WHERE client_id=? ORDER BY label, created_at DESC",
                (client_id,)
            ).fetchall()
        return [dict(r) for r in rows]


def delete_example(example_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM caption_examples WHERE id=?", (example_id,))


def get_example_counts(client_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT label, COUNT(*) as cnt FROM caption_examples WHERE client_id=? GROUP BY label",
            (client_id,)
        ).fetchall()
        return {r["label"]: r["cnt"] for r in rows}


# ── Generation History ───────────────────────────────────────────────────────

def save_generation(client_id, batch_desc, platform, num_captions, captions_json):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO generation_history (client_id, batch_desc, platform, num_captions, captions_json) VALUES (?,?,?,?,?)",
            (client_id, batch_desc, platform, num_captions, captions_json)
        )


def get_history(client_id, limit=20):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM generation_history WHERE client_id=? ORDER BY created_at DESC LIMIT ?",
            (client_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def get_stats(owner_id=None):
    """Get dashboard stats. If owner_id is set, scoped to that user's clients only."""
    with get_conn() as conn:
        stats = {}
        if owner_id is not None:
            stats["total_clients"] = conn.execute(
                "SELECT COUNT(*) FROM clients WHERE owner_id=?", (owner_id,)
            ).fetchone()[0]
            stats["total_examples"] = conn.execute(
                "SELECT COUNT(*) FROM caption_examples WHERE client_id IN (SELECT id FROM clients WHERE owner_id=?)",
                (owner_id,)
            ).fetchone()[0]
            stats["total_generated"] = conn.execute(
                "SELECT COALESCE(SUM(num_captions),0) FROM generation_history WHERE client_id IN (SELECT id FROM clients WHERE owner_id=?)",
                (owner_id,)
            ).fetchone()[0]
            stats["recent_generations"] = conn.execute(
                """SELECT g.*, c.name as client_name FROM generation_history g
                   JOIN clients c ON g.client_id=c.id
                   WHERE c.owner_id=?
                   ORDER BY g.created_at DESC LIMIT 5""",
                (owner_id,)
            ).fetchall()
        else:
            stats["total_clients"] = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
            stats["total_examples"] = conn.execute("SELECT COUNT(*) FROM caption_examples").fetchone()[0]
            stats["total_generated"] = conn.execute("SELECT COALESCE(SUM(num_captions),0) FROM generation_history").fetchone()[0]
            stats["recent_generations"] = conn.execute(
                "SELECT g.*, c.name as client_name FROM generation_history g JOIN clients c ON g.client_id=c.id ORDER BY g.created_at DESC LIMIT 5"
            ).fetchall()
        return stats

# ── Keyword Operations ────────────────────────────────────────────────────────

def add_keyword(client_id, keyword, category="general", priority="normal"):
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO client_keywords (client_id, keyword, category, priority) VALUES (?,?,?,?)",
                (client_id, keyword.strip(), category, priority)
            )
            return True
        except sqlite3.IntegrityError:
            return False


def add_keywords_bulk(client_id, keywords: list, category="general", priority="normal"):
    added, skipped = 0, 0
    for kw in keywords:
        if kw.strip():
            success = add_keyword(client_id, kw.strip(), category, priority)
            if success:
                added += 1
            else:
                skipped += 1
    return added, skipped


def get_keywords(client_id, category=None):
    with get_conn() as conn:
        if category:
            rows = conn.execute(
                "SELECT * FROM client_keywords WHERE client_id=? AND category=? ORDER BY priority DESC, keyword",
                (client_id, category)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM client_keywords WHERE client_id=? ORDER BY category, priority DESC, keyword",
                (client_id,)
            ).fetchall()
        return [dict(r) for r in rows]


def get_keywords_for_generation(client_id, num_captions=5):
    """Smart keyword selection — rotates by least recently used to minimize repetition."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM client_keywords
            WHERE client_id=?
            ORDER BY
                CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END,
                COALESCE(last_used, '1970-01-01') ASC,
                use_count ASC
        """, (client_id,)).fetchall()

    keywords = [dict(r) for r in rows]
    result = {"always": [], "rotate": [], "occasional": [], "all": keywords}
    for kw in keywords:
        if kw["priority"] == "high":
            result["always"].append(kw["keyword"])
        elif kw["priority"] == "normal":
            result["rotate"].append(kw["keyword"])
        else:
            result["occasional"].append(kw["keyword"])
    return result


def record_keyword_usage(client_id, keyword, generation_id=None):
    with get_conn() as conn:
        conn.execute("""
            UPDATE client_keywords
            SET use_count = use_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE client_id=? AND keyword=?
        """, (client_id, keyword))
        row = conn.execute(
            "SELECT id FROM client_keywords WHERE client_id=? AND keyword=?",
            (client_id, keyword)
        ).fetchone()
        if row:
            conn.execute(
                "INSERT INTO keyword_usage_log (client_id, keyword_id, generation_id) VALUES (?,?,?)",
                (client_id, row["id"], generation_id)
            )


def update_keyword(keyword_id, **kwargs):
    allowed = {"keyword", "category", "priority"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [keyword_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE client_keywords SET {set_clause} WHERE id=?", values)


def delete_keyword(keyword_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM client_keywords WHERE id=?", (keyword_id,))


def get_keyword_stats(client_id):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT k.keyword, k.category, k.priority, k.use_count, k.last_used,
                   COUNT(l.id) as recent_uses
            FROM client_keywords k
            LEFT JOIN keyword_usage_log l ON l.keyword_id = k.id
                AND l.used_at >= datetime('now', '-30 days')
            WHERE k.client_id=?
            GROUP BY k.id
            ORDER BY k.use_count DESC
        """, (client_id,)).fetchall()
        return [dict(r) for r in rows]

# ── Caption Rating Operations ─────────────────────────────────────────────────

def save_rating(client_id, caption_text, rating, hashtags="", platform="",
                batch_desc="", notes="", saved_as=None):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO caption_ratings
                (client_id, caption_text, hashtags, platform, batch_desc, rating, notes, saved_as)
            VALUES (?,?,?,?,?,?,?,?)
        """, (client_id, caption_text, hashtags, platform, batch_desc, rating, notes, saved_as))


def update_rating_saved_as(client_id, caption_text, saved_as):
    with get_conn() as conn:
        conn.execute("""
            UPDATE caption_ratings SET saved_as=?
            WHERE client_id=? AND caption_text=?
        """, (saved_as, client_id, caption_text))


def get_ratings(client_id, limit=50):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM caption_ratings
            WHERE client_id=?
            ORDER BY created_at DESC
            LIMIT ?
        """, (client_id, limit)).fetchall()
        return [dict(r) for r in rows]


def get_rating_stats(client_id):
    with get_conn() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*)                            as total,
                ROUND(AVG(rating), 2)               as avg_rating,
                SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as high_rated,
                SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) as low_rated,
                SUM(CASE WHEN saved_as='good' THEN 1 ELSE 0 END) as saved_good,
                SUM(CASE WHEN saved_as='bad'  THEN 1 ELSE 0 END) as saved_bad
            FROM caption_ratings WHERE client_id=?
        """, (client_id,)).fetchone()
        return dict(row) if row else {}

# ── Posting Schedule Operations ───────────────────────────────────────────────

def save_posting_schedule(client_id, schedule_json):
    with get_conn() as conn:
        try:
            conn.execute("ALTER TABLE clients ADD COLUMN posting_schedule TEXT")
        except Exception:
            pass
        conn.execute(
            "UPDATE clients SET posting_schedule=? WHERE id=?",
            (schedule_json, client_id)
        )


def get_posting_schedule(client_id):
    import json
    with get_conn() as conn:
        try:
            row = conn.execute(
                "SELECT posting_schedule FROM clients WHERE id=?", (client_id,)
            ).fetchone()
            if row and row[0]:
                return json.loads(row[0])
        except Exception:
            pass
    return {"post_types": [], "total_monthly": 0, "notes": "", "proposal": ""}


def relabel_example(example_id, new_label):
    with get_conn() as conn:
        conn.execute(
            "UPDATE caption_examples SET label=? WHERE id=?",
            (new_label, example_id)
        )
