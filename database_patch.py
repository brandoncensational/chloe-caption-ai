# Run this once to add the ratings table to existing databases
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "captions.db")

def patch():
    if not os.path.exists(DB_PATH):
        print("No database found — will be created fresh when app runs.")
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS caption_ratings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id       INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                caption_text    TEXT    NOT NULL,
                hashtags        TEXT    DEFAULT '',
                platform        TEXT    DEFAULT '',
                batch_desc      TEXT    DEFAULT '',
                rating          INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                saved_as        TEXT,   -- 'good', 'bad', or NULL
                notes           TEXT,
                created_at      TEXT    DEFAULT CURRENT_TIMESTAMP
            );
        """)
    print("Database patched successfully.")

if __name__ == "__main__":
    patch()
