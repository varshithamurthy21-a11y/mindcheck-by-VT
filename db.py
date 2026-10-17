"""
SQLite storage. Everything is keyed by a nickname (no real names, no passwords).
Rows created by the demo-data generator carry demo=1 so they can be removed.
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.environ.get("MINDCHECK_DB", "mindcheck.db")

SCHEMA = {
    "puzzle_attempts": "pillar TEXT, skill TEXT, difficulty INTEGER, correct INTEGER, "
                       "ms INTEGER, mode TEXT, stress REAL, energy REAL",
    "battery_sessions": "speed REAL, memory REAL, reaction_ms REAL, readiness REAL, "
                        "details TEXT, stress REAL, sleep REAL",
    "journals": "text TEXT, emotions TEXT, sentiment REAL",
    "body_checkins": "energy INTEGER, sleep INTEGER, tension INTEGER, stress INTEGER, areas TEXT",
    "wheel_entries": "core TEXT, mid TEXT, specific TEXT",
    "wellbeing": "mood INTEGER, stress INTEGER, sensitivity INTEGER",
    "quick_mood": "value INTEGER",
}
JSON_FIELDS = {"details", "emotions", "areas"}


def now_str(dt=None):
    return (dt or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    for table, cols in SCHEMA.items():
        c.execute(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  f"nickname TEXT, ts TEXT, demo INTEGER DEFAULT 0, {cols})")
    return c


def _norm(nickname):
    return (nickname or "").strip().lower()


def insert(table, nickname, ts=None, demo=0, **fields):
    if table not in SCHEMA:
        raise ValueError(table)
    data = {k: (json.dumps(v) if k in JSON_FIELDS else v) for k, v in fields.items()}
    cols = ["nickname", "ts", "demo"] + list(data)
    vals = [_norm(nickname), ts or now_str(), demo] + list(data.values())
    with _conn() as c:
        c.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", vals)


def insert_many(table, rows):
    """rows: list of dicts with nickname, ts, demo and table fields."""
    for r in rows:
        r = dict(r)
        insert(table, r.pop("nickname"), r.pop("ts", None), r.pop("demo", 0), **r)


def fetch(table, nickname, days=None):
    q = f"SELECT * FROM {table} WHERE nickname=?"
    args = [_norm(nickname)]
    if days is not None:
        q += " AND ts >= ?"
        args.append(now_str(datetime.now() - timedelta(days=days)))
    q += " ORDER BY ts, id"
    with _conn() as c:
        rows = [dict(r) for r in c.execute(q, args).fetchall()]
    for r in rows:
        for k in JSON_FIELDS & r.keys():
            r[k] = json.loads(r[k]) if r[k] else None
    return rows


def latest(table, nickname, same_day=False):
    rows = fetch(table, nickname, days=1 if same_day else None)
    if same_day:
        today = datetime.now().strftime("%Y-%m-%d")
        rows = [r for r in rows if r["ts"].startswith(today)]
    return rows[-1] if rows else None


def has_demo(nickname):
    with _conn() as c:
        return any(c.execute(f"SELECT 1 FROM {t} WHERE nickname=? AND demo=1 LIMIT 1",
                             (_norm(nickname),)).fetchone() for t in SCHEMA)


def delete_demo(nickname):
    with _conn() as c:
        for t in SCHEMA:
            c.execute(f"DELETE FROM {t} WHERE nickname=? AND demo=1", (_norm(nickname),))


def delete_user(nickname):
    with _conn() as c:
        for t in SCHEMA:
            c.execute(f"DELETE FROM {t} WHERE nickname=?", (_norm(nickname),))
