import sqlite3, json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/history.db")

def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_key TEXT NOT NULL,
            source_url TEXT NOT NULL,
            started_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            sources     TEXT DEFAULT '[]',
            latency     REAL DEFAULT 0,
            chunks_used INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL
        );
        """)

def create_session(domain_key, source_url):
    init_db()
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO sessions (domain_key,source_url,started_at) VALUES (?,?,?)",
            (domain_key, source_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        return cur.lastrowid

def add_message(session_id, role, content, sources=None, latency=0, chunks_used=0):
    init_db()
    with _conn() as con:
        con.execute(
            "INSERT INTO messages (session_id,role,content,sources,latency,chunks_used,created_at) VALUES (?,?,?,?,?,?,?)",
            (session_id, role, content, json.dumps(sources or []), latency, chunks_used,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

def get_session_messages(session_id):
    init_db()
    with _conn() as con:
        rows = con.execute("SELECT * FROM messages WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
    return [dict(r) for r in rows]

def get_recent_messages(session_id, n=4):
    msgs = get_session_messages(session_id)
    return msgs[-(n * 2):]

def get_all_sessions():
    init_db()
    with _conn() as con:
        rows = con.execute("""
            SELECT s.*, COUNT(m.id) as message_count
            FROM sessions s LEFT JOIN messages m ON m.session_id=s.id
            GROUP BY s.id ORDER BY s.id DESC
        """).fetchall()
    return [dict(r) for r in rows]

def search_history(query):
    init_db()
    with _conn() as con:
        rows = con.execute("""
            SELECT m.*, s.source_url, s.domain_key, s.started_at as session_started
            FROM messages m JOIN sessions s ON s.id=m.session_id
            WHERE m.role='user' AND m.content LIKE ?
            ORDER BY m.id DESC LIMIT 50
        """, (f"%{query}%",)).fetchall()
    return [dict(r) for r in rows]

def delete_session(session_id):
    init_db()
    with _conn() as con:
        con.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        con.execute("DELETE FROM sessions WHERE id=?", (session_id,))

def delete_all_history():
    init_db()
    with _conn() as con:
        con.execute("DELETE FROM messages")
        con.execute("DELETE FROM sessions")

def get_stats():
    init_db()
    with _conn() as con:
        sessions  = con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        questions = con.execute("SELECT COUNT(*) FROM messages WHERE role='user'").fetchone()[0]
        sites     = con.execute("SELECT COUNT(DISTINCT domain_key) FROM sessions").fetchone()[0]
    return {"total_sessions": sessions, "total_questions": questions, "total_sites": sites}