from app.db import get_db

USER = {"email": "student@example.com", "password": "secret123", "name": "Іван"}


def register(client, **overrides):
    return client.post("/api/register", json={**USER, **overrides})


def test_register_success(client):
    res = register(client)
    assert res.status_code == 201
    assert res.get_json()["email"] == USER["email"]


def test_password_is_stored_as_hash(app, client):
    register(client)
    with app.app_context():
        row = get_db().execute("SELECT password_hash FROM users").fetchone()
    assert row["password_hash"] != USER["password"]
    assert USER["password"] not in row["password_hash"]


def test_duplicate_email_rejected_case_insensitive(client):
    register(client)
    res = register(client, email="STUDENT@example.com")
    assert res.status_code == 409


def test_invalid_email_rejected(client):
    assert register(client, email="not-an-email").status_code == 400


def test_short_password_rejected(client):
    assert register(client, password="123").status_code == 400


def test_empty_name_rejected(client):
    assert register(client, name="   ").status_code == 400


def test_login_success(client):
    register(client)
    client.post("/api/logout")
    res = client.post("/api/login", json={"email": USER["email"], "password": USER["password"]})
    assert res.status_code == 200
    assert client.get("/api/me").status_code == 200


def test_login_wrong_password(client):
    register(client)
    client.post("/api/logout")
    res = client.post("/api/login", json={"email": USER["email"], "password": "wrong-pass"})
    assert res.status_code == 401
    assert client.get("/api/me").status_code == 401


def test_login_unknown_email_has_same_error(client):
    res = client.post("/api/login", json={"email": "no@no.ua", "password": "whatever1"})
    assert res.status_code == 401
    assert res.get_json()["error"] == "Неправильний e-mail або пароль"


def test_me_requires_login(client):
    assert client.get("/api/me").status_code == 401


def test_logout_ends_session(client):
    register(client)
    assert client.get("/api/me").status_code == 200
    client.post("/api/logout")
    assert client.get("/api/me").status_code == 401


def test_index_page_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "TaskStudent" in res.get_data(as_text=True)
