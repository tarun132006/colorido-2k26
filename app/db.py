import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "colorido.db"

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row   # rows behave like dicts
    c.execute("PRAGMA foreign_keys = ON")
    return c

def query(sql, args=()):
    c = conn()
    try:
        return [dict(r) for r in c.execute(sql, args)]
    finally:
        c.close()

def execute(sql, args=()):
    c = conn()
    try:
        cur = c.execute(sql, args)
        c.commit()
        return cur.lastrowid
    finally:
        c.close()

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    division    TEXT NOT NULL,          -- 'cultural' or 'sports'
    category    TEXT NOT NULL,          -- 'Dance', 'Fine Arts', 'Basketball', ...
    gender      TEXT NOT NULL DEFAULT 'Open',   -- 'Open', 'Boys', 'Girls'
    team_min    INTEGER NOT NULL DEFAULT 1,
    team_max    INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    rules       TEXT,                   -- JSON list stored as text
    eligibility TEXT,
    fee         INTEGER DEFAULT 0,
    prize       TEXT,
    day         INTEGER,                -- 1, 2 or 3
    start_time  TEXT,                   -- '10:30'
    venue       TEXT,
    coordinator TEXT,
    phone       TEXT,
    featured    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS registrations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_id     TEXT UNIQUE,             -- e.g. CLR26-DAN-0042
    event_id   INTEGER NOT NULL REFERENCES events(id),
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    phone      TEXT NOT NULL,
    college    TEXT NOT NULL,
    gender     TEXT NOT NULL,
    team_name  TEXT,
    members    TEXT,                    -- JSON list of extra member names
    status     TEXT DEFAULT 'Confirmed',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (event_id, email)            -- same email can't join the same event twice
);

CREATE TABLE IF NOT EXISTS announcements (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    body       TEXT NOT NULL,
    pinned     INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id   INTEGER NOT NULL REFERENCES events(id),
    position   INTEGER NOT NULL,        -- 1, 2, 3
    winner     TEXT NOT NULL,
    college    TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gallery (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    caption   TEXT NOT NULL,
    category  TEXT,
    year      INTEGER,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS sponsors (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tier TEXT NOT NULL,                 -- 'Title', 'Gold', 'Silver', 'Partner'
    url  TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    subject    TEXT,
    body       TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY,
    salt     TEXT NOT NULL,
    pw_hash  TEXT NOT NULL
);
"""

def init_db():
    c = conn()
    c.executescript(SCHEMA)
    c.commit()
    c.close()