import os

from flask import Flask

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev-change-me",
        DATABASE=os.path.join(app.instance_path, "taskstudent.db"),
    )
    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    # Створюємо таблиці при першому запуску
    with app.app_context():
        if not os.path.exists(app.config["DATABASE"]):
            db.init_db()

    return app
