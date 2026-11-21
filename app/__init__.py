import os

from flask import Flask

from . import auth, db, progress, subjects, tasks


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
    app.register_blueprint(auth.bp)
    app.register_blueprint(subjects.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(progress.bp)

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
