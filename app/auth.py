import functools
import re

from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/api")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 6


def error(message, status):
    return jsonify({"error": message}), status


def login_required(view):
    """Пропускає тільки авторизованого користувача."""

    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return error("Потрібно увійти в систему", 401)
        return view(*args, **kwargs)

    return wrapped


@bp.before_app_request
def load_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT id, email, name FROM users WHERE id = ?", (user_id,)
        ).fetchone()


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    name = str(data.get("name", "")).strip()

    if not EMAIL_RE.match(email):
        return error("Некоректний e-mail", 400)
    if len(password) < MIN_PASSWORD_LEN:
        return error(f"Пароль має містити щонайменше {MIN_PASSWORD_LEN} символів", 400)
    if not name:
        return error("Вкажіть ім'я", 400)

    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        return error("Користувач з таким e-mail уже існує", 409)

    cur = db.execute(
        "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
        (email, generate_password_hash(password), name),
    )
    db.commit()
    session.clear()
    session["user_id"] = cur.lastrowid
    return jsonify({"id": cur.lastrowid, "email": email, "name": name}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    user = get_db().execute(
        "SELECT id, email, name, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()
    # Однакова відповідь для невідомого e-mail і неправильного пароля
    if user is None or not check_password_hash(user["password_hash"], password):
        return error("Неправильний e-mail або пароль", 401)

    session.clear()
    session["user_id"] = user["id"]
    return jsonify({"id": user["id"], "email": user["email"], "name": user["name"]})


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get("/me")
@login_required
def me():
    return jsonify({"id": g.user["id"], "email": g.user["email"], "name": g.user["name"]})
