from flask import Blueprint, g, jsonify, request

from .auth import error, login_required
from .db import get_db
from .subjects import get_own_subject
from .validation import ValidationError, parse_choice, parse_date, parse_number, parse_text

bp = Blueprint("tasks", __name__, url_prefix="/api")

STATUSES = ("new", "done")
TASK_COLUMNS = "t.id, t.subject_id, t.title, t.description, t.deadline, t.max_score, t.status, t.score"


def task_to_dict(row):
    return {key: row[key] for key in
            ("id", "subject_id", "title", "description", "deadline", "max_score", "status", "score")}


def get_own_task(task_id):
    """Завдання поточного користувача або None."""
    return get_db().execute(
        f"SELECT {TASK_COLUMNS} FROM tasks t JOIN subjects s ON s.id = t.subject_id "
        "WHERE t.id = ? AND s.user_id = ?",
        (task_id, g.user["id"]),
    ).fetchone()


def check_score(score, max_score):
    """Бал: не від'ємний і не більший за максимальний (або None - бал не виставлено)."""
    if score is None:
        return None
    score = parse_number(score, "Бал")
    if score > max_score:
        raise ValidationError(f"Бал не може бути більшим за максимальний ({max_score})")
    return score


@bp.errorhandler(ValidationError)
def handle_validation_error(exc):
    return error(str(exc), 400)


@bp.get("/subjects/<int:subject_id>/tasks")
@login_required
def list_tasks(subject_id):
    if get_own_subject(subject_id) is None:
        return error("Предмет не знайдено", 404)
    rows = get_db().execute(
        f"SELECT {TASK_COLUMNS} FROM tasks t WHERE t.subject_id = ? "
        "ORDER BY t.deadline IS NULL, t.deadline, t.id",
        (subject_id,),
    ).fetchall()
    return jsonify([task_to_dict(r) for r in rows])


@bp.post("/subjects/<int:subject_id>/tasks")
@login_required
def create_task(subject_id):
    if get_own_subject(subject_id) is None:
        return error("Предмет не знайдено", 404)

    data = request.get_json(silent=True) or {}
    title = parse_text(data.get("title"), "Назва")
    description = parse_text(data.get("description"), "Опис", max_len=1000, required=False)
    deadline = parse_date(data.get("deadline"), "Дедлайн")
    max_score = parse_number(data.get("max_score"), "Максимальний бал", allow_zero=False)
    status = parse_choice(data.get("status", "new"), "Статус", STATUSES)
    score = check_score(data.get("score"), max_score)

    db = get_db()
    cur = db.execute(
        "INSERT INTO tasks (subject_id, title, description, deadline, max_score, status, score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (subject_id, title, description, deadline, max_score, status, score),
    )
    db.commit()
    row = get_own_task(cur.lastrowid)
    return jsonify(task_to_dict(row)), 201


@bp.get("/tasks/<int:task_id>")
@login_required
def get_task(task_id):
    row = get_own_task(task_id)
    if row is None:
        return error("Завдання не знайдено", 404)
    return jsonify(task_to_dict(row))


@bp.put("/tasks/<int:task_id>")
@login_required
def update_task(task_id):
    row = get_own_task(task_id)
    if row is None:
        return error("Завдання не знайдено", 404)

    data = request.get_json(silent=True) or {}
    title = parse_text(data["title"], "Назва") if "title" in data else row["title"]
    description = (parse_text(data["description"], "Опис", max_len=1000, required=False)
                   if "description" in data else row["description"])
    deadline = parse_date(data["deadline"], "Дедлайн") if "deadline" in data else row["deadline"]
    max_score = (parse_number(data["max_score"], "Максимальний бал", allow_zero=False)
                 if "max_score" in data else row["max_score"])
    status = parse_choice(data["status"], "Статус", STATUSES) if "status" in data else row["status"]
    # Бал перевіряємо щодо підсумкового max_score, навіть якщо змінився тільки max_score
    score = check_score(data["score"] if "score" in data else row["score"], max_score)

    db = get_db()
    db.execute(
        "UPDATE tasks SET title = ?, description = ?, deadline = ?, max_score = ?, "
        "status = ?, score = ? WHERE id = ?",
        (title, description, deadline, max_score, status, score, task_id),
    )
    db.commit()
    return jsonify(task_to_dict(get_own_task(task_id)))


@bp.delete("/tasks/<int:task_id>")
@login_required
def delete_task(task_id):
    if get_own_task(task_id) is None:
        return error("Завдання не знайдено", 404)
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return jsonify({"ok": True})
