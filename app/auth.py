import functools
import re

from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .validation import ValidationError, parse_password, parse_text

bp = Blueprint("auth", __name__, url_prefix="/api")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_EMAIL_LEN = 254

# Хеш неіснуючого пароля: перевіряємо його для невідомого e-mail, щоб відповідь
# займала стільки ж часу, і за часом не можна було дізнатися, які адреси зареєстровані.
DUMMY_HASH = generate_password_hash("not-a-real-password")


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


def parse_email(value):
    email = parse_text(value, "E-mail", max_len=MAX_EMAIL_LEN).lower()
    if not EMAIL_RE.match(email):
        raise ValidationError("Некоректний e-mail")
    return email


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = parse_email(data.get("email"))
    password = parse_password(data.get("password"))
    name = parse_text(data.get("name"), "Ім'я")

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
    password_hash = user["password_hash"] if user else DUMMY_HASH
    password_ok = check_password_hash(password_hash, password)
    # Однакова відповідь для невідомого e-mail і неправильного пароля
    if user is None or not password_ok:
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
