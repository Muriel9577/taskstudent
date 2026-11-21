from flask import Blueprint, g, jsonify, request

from .auth import error, login_required
from .db import get_db
from .services import clean_number
from .validation import ValidationError, parse_number, parse_text

bp = Blueprint("subjects", __name__, url_prefix="/api/subjects")


def subject_to_dict(row):
    return {"id": row["id"], "title": row["title"], "pass_score": clean_number(row["pass_score"])}


def get_own_subject(subject_id):
    """Предмет поточного користувача або None (чужий предмет не розкриваємо)."""
    return get_db().execute(
        "SELECT id, title, pass_score FROM subjects WHERE id = ? AND user_id = ?",
        (subject_id, g.user["id"]),
    ).fetchone()


@bp.get("")
@login_required
def list_subjects():
    rows = get_db().execute(
        "SELECT id, title, pass_score FROM subjects WHERE user_id = ? ORDER BY title",
        (g.user["id"],),
    ).fetchall()
    return jsonify([subject_to_dict(r) for r in rows])


@bp.post("")
@login_required
def create_subject():
    data = request.get_json(silent=True) or {}
    title = parse_text(data.get("title"), "Назва")
    pass_score = parse_number(data.get("pass_score", 0), "Прохідний бал")

    db = get_db()
    cur = db.execute(
        "INSERT INTO subjects (user_id, title, pass_score) VALUES (?, ?, ?)",
        (g.user["id"], title, pass_score),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "title": title, "pass_score": clean_number(pass_score)}), 201


@bp.get("/<int:subject_id>")
@login_required
def get_subject(subject_id):
    row = get_own_subject(subject_id)
    if row is None:
        return error("Предмет не знайдено", 404)
    return jsonify(subject_to_dict(row))


@bp.put("/<int:subject_id>")
@login_required
def update_subject(subject_id):
    row = get_own_subject(subject_id)
    if row is None:
        return error("Предмет не знайдено", 404)

    data = request.get_json(silent=True) or {}
    title = parse_text(data["title"], "Назва") if "title" in data else row["title"]
    pass_score = (
        parse_number(data["pass_score"], "Прохідний бал")
        if "pass_score" in data
        else row["pass_score"]
    )

    db = get_db()
    db.execute(
        "UPDATE subjects SET title = ?, pass_score = ? WHERE id = ?",
        (title, pass_score, subject_id),
    )
    db.commit()
    return jsonify({"id": subject_id, "title": title, "pass_score": clean_number(pass_score)})


@bp.delete("/<int:subject_id>")
@login_required
def delete_subject(subject_id):
    if get_own_subject(subject_id) is None:
        return error("Предмет не знайдено", 404)
    db = get_db()
    db.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    db.commit()
    return jsonify({"ok": True})
