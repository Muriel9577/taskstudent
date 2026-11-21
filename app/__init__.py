import os
import secrets

from flask import Flask, jsonify

from . import auth, db, progress, subjects, tasks
from .validation import ValidationError


def load_secret_key(instance_path):
    """Секретний ключ: змінна середовища SECRET_KEY або випадковий ключ у файлі instance/secret_key."""
    from_env = os.environ.get("SECRET_KEY")
    if from_env:
        return from_env
    path = os.path.join(instance_path, "secret_key")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(path, "w", encoding="utf-8") as f:
        f.write(key)
    return key


def create_app(test_config=None, instance_path=None):
    app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.from_mapping(
        SECRET_KEY=load_secret_key(app.instance_path),
        DATABASE=os.path.join(app.instance_path, "taskstudent.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=1024 * 1024,  # запити більші за 1 МБ відхиляються
    )
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(subjects.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(progress.bp)

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc):
        return jsonify({"error": str(exc)}), 400

    # Створюємо таблиці при першому запуску
    with app.app_context():
        if not os.path.exists(app.config["DATABASE"]):
            db.init_db()

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/subject/<int:subject_id>")
    def subject_page(subject_id):
        return app.send_static_file("subject.html")

    return app
