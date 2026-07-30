import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "study_assistant.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT NOT NULL,
        topic TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        summary TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT NOT NULL,
        topic TEXT NOT NULL,
        review_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        difficulty TEXT DEFAULT 'medium'
    );

    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT NOT NULL,
        topic TEXT NOT NULL,
        questions_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        score REAL,
        weak_topics_json TEXT,
        attempted_at TEXT NOT NULL,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
    );
    """)
    conn.commit()
    conn.close()


def save_note(course, topic, raw_text, summary=None):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO notes (course, topic, raw_text, summary, created_at) VALUES (?, ?, ?, ?, ?)",
        (course, topic, raw_text, summary, datetime.now().isoformat()),
    )
    conn.commit()
    note_id = cur.lastrowid
    conn.close()
    return note_id


def update_summary(note_id, summary):
    conn = get_conn()
    conn.execute("UPDATE notes SET summary = ? WHERE id = ?", (summary, note_id))
    conn.commit()
    conn.close()


def get_notes(course=None, topic=None):
    conn = get_conn()
    q = "SELECT * FROM notes WHERE 1=1"
    params = []

    if course:
        q += " AND course = ?"
        params.append(course)

    if topic:
        q += " AND topic = ?"
        params.append(topic)

    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_schedule_entry(course, topic, review_date, difficulty="medium"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO schedule (course, topic, review_date, difficulty) VALUES (?, ?, ?, ?)",
        (course, topic, review_date, difficulty),
    )
    conn.commit()
    conn.close()


def get_upcoming_schedule(course=None):
    conn = get_conn()
    q = "SELECT * FROM schedule WHERE status = 'pending'"
    params = []

    if course:
        q += " AND course = ?"
        params.append(course)

    q += " ORDER BY review_date ASC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_schedule_status(entry_id, status):
    conn = get_conn()
    conn.execute("UPDATE schedule SET status = ? WHERE id = ?", (status, entry_id))
    conn.commit()
    conn.close()


def save_quiz(course, topic, questions):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO quizzes (course, topic, questions_json, created_at) VALUES (?, ?, ?, ?)",
        (course, topic, json.dumps(questions), datetime.now().isoformat()),
    )
    conn.commit()
    quiz_id = cur.lastrowid
    conn.close()
    return quiz_id


def save_quiz_attempt(quiz_id, score, weak_topics):
    conn = get_conn()
    conn.execute(
        "INSERT INTO quiz_attempts (quiz_id, score, weak_topics_json, attempted_at) VALUES (?, ?, ?, ?)",
        (quiz_id, score, json.dumps(weak_topics), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_weak_topics(course=None):
    conn = get_conn()
    q = """
    SELECT q.topic, qa.score
    FROM quiz_attempts qa
    JOIN quizzes q ON qa.quiz_id = q.id
    WHERE 1=1
    """
    params = []

    if course:
        q += " AND q.course = ?"
        params.append(course)

    rows = conn.execute(q, params).fetchall()
    conn.close()

    scores = {}
    for r in rows:
        scores.setdefault(r["topic"], []).append(r["score"])

    weak = [topic for topic, vals in scores.items() if sum(vals) / len(vals) < 0.7]
    return weak