"""Тести виправлень, знайдених під час code review (етап 7)."""
import os
import stat

from app import create_app


def test_login_does_not_hash_oversized_password(client, monkeypatch):
    """Вхід з надто довгим паролем відхиляється до хешування (захист від навантаження на сервер)."""
    import app.auth as auth

    calls = []
    original = auth.check_password_hash
    monkeypatch.setattr(auth, "check_password_hash", lambda h, p: calls.append(1) or original(h, p))

    res = client.post("/api/login", json={"email": "a@example.com", "password": "x" * 100_000})
    assert res.status_code == 401
    assert calls == []


def test_login_with_normal_password_still_checks_hash(client, monkeypatch):
    import app.auth as auth

    calls = []
    original = auth.check_password_hash
    monkeypatch.setattr(auth, "check_password_hash", lambda h, p: calls.append(1) or original(h, p))

    client.post("/api/login", json={"email": "a@example.com", "password": "secret123"})
    assert calls == [1]


def test_foreign_key_columns_are_indexed(app):
    with app.app_context():
        from app.db import get_db

        db = get_db()
        indexed = {
            (table, row["name"])
            for table in ("subjects", "tasks")
            for idx in db.execute(f"PRAGMA index_list({table})").fetchall()
            for row in db.execute(f"PRAGMA index_info({idx['name']})").fetchall()
        }
    assert ("subjects", "user_id") in indexed
    assert ("tasks", "subject_id") in indexed


def test_secret_key_file_is_private(tmp_path):
    os.environ.pop("SECRET_KEY", None)
    create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db")}, instance_path=str(tmp_path / "inst"))
    mode = stat.S_IMODE(os.stat(tmp_path / "inst" / "secret_key").st_mode)
    assert mode == 0o600
