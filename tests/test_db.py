import sqlite3

import pytest

from app.db import get_db


def test_tables_created(app):
    with app.app_context():
        rows = get_db().execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        names = {r["name"] for r in rows}
    assert {"users", "subjects", "tasks"} <= names


def test_email_must_be_unique(app):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO users (email, password_hash, name) VALUES ('a@a.ua', 'h', 'A')")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO users (email, password_hash, name) VALUES ('a@a.ua', 'h', 'B')")


def test_deleting_subject_deletes_its_tasks(app):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO users (email, password_hash, name) VALUES ('a@a.ua', 'h', 'A')")
        db.execute("INSERT INTO subjects (user_id, title, pass_score) VALUES (1, 'Math', 60)")
        db.execute("INSERT INTO tasks (subject_id, title, max_score) VALUES (1, 'Lab 1', 10)")
        db.execute("DELETE FROM subjects WHERE id = 1")
        left = db.execute("SELECT COUNT(*) AS n FROM tasks").fetchone()["n"]
    assert left == 0


def test_score_cannot_exceed_max_score(app):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO users (email, password_hash, name) VALUES ('a@a.ua', 'h', 'A')")
        db.execute("INSERT INTO subjects (user_id, title) VALUES (1, 'Math')")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO tasks (subject_id, title, max_score, score) VALUES (1, 'Lab', 10, 11)")
