from flask import Blueprint, jsonify

from .auth import error, login_required
from .db import get_db
from .services import compute_progress
from .subjects import get_own_subject

bp = Blueprint("progress", __name__, url_prefix="/api/subjects")


@bp.get("/<int:subject_id>/progress")
@login_required
def subject_progress(subject_id):
    subject = get_own_subject(subject_id)
    if subject is None:
        return error("Предмет не знайдено", 404)
    tasks = get_db().execute(
        "SELECT status, score, max_score FROM tasks WHERE subject_id = ?", (subject_id,)
    ).fetchall()
    return jsonify(compute_progress(tasks, subject["pass_score"]))
