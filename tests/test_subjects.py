import pytest

from app.db import get_db


def make_user(client, email="a@example.com", name="A"):
    client.post("/api/logout")
    res = client.post("/api/register", json={"email": email, "password": "secret123", "name": name})
    assert res.status_code == 201


def login(client, email):
    client.post("/api/logout")
    res = client.post("/api/login", json={"email": email, "password": "secret123"})
    assert res.status_code == 200


def create(client, title="Математика", pass_score=60):
    return client.post("/api/subjects", json={"title": title, "pass_score": pass_score})


def test_requires_login(client):
    assert client.get("/api/subjects").status_code == 401
    assert create(client).status_code == 401


def test_create_and_list(client):
    make_user(client)
    res = create(client)
    assert res.status_code == 201
    assert res.get_json()["pass_score"] == 60
    items = client.get("/api/subjects").get_json()
    assert [i["title"] for i in items] == ["Математика"]


def test_pass_score_defaults_to_zero(client):
    make_user(client)
    res = client.post("/api/subjects", json={"title": "Фізика"})
    assert res.status_code == 201
    assert res.get_json()["pass_score"] == 0


@pytest.mark.parametrize("payload", [
    {"title": "", "pass_score": 10},
    {"title": "   ", "pass_score": 10},
    {"title": "Х" * 101, "pass_score": 10},
    {"title": "Ok", "pass_score": -1},
    {"title": "Ok", "pass_score": "60"},
    {"title": "Ok", "pass_score": True},
    {"title": "Ok", "pass_score": None},
])
def test_invalid_subject_rejected(client, payload):
    make_user(client)
    assert client.post("/api/subjects", json=payload).status_code == 400


def test_list_shows_only_own_subjects(client):
    make_user(client, "a@example.com")
    create(client, "Предмет A")
    make_user(client, "b@example.com")
    create(client, "Предмет B")
    titles = [i["title"] for i in client.get("/api/subjects").get_json()]
    assert titles == ["Предмет B"]


def test_other_user_cannot_access_subject(client):
    make_user(client, "a@example.com")
    sid = create(client).get_json()["id"]
    make_user(client, "b@example.com")
    assert client.get(f"/api/subjects/{sid}").status_code == 404
    assert client.put(f"/api/subjects/{sid}", json={"title": "Зламано"}).status_code == 404
    assert client.delete(f"/api/subjects/{sid}").status_code == 404
    # власник бачить свій предмет без змін
    login(client, "a@example.com")
    assert client.get(f"/api/subjects/{sid}").get_json()["title"] == "Математика"


def test_update_title_keeps_pass_score(client):
    make_user(client)
    sid = create(client, "Математика", 60).get_json()["id"]
    res = client.put(f"/api/subjects/{sid}", json={"title": "Вища математика"})
    assert res.status_code == 200
    assert res.get_json() == {"id": sid, "title": "Вища математика", "pass_score": 60}


def test_update_pass_score(client):
    make_user(client)
    sid = create(client).get_json()["id"]
    res = client.put(f"/api/subjects/{sid}", json={"pass_score": 75.5})
    assert res.get_json()["pass_score"] == 75.5


def test_update_with_invalid_value_rejected(client):
    make_user(client)
    sid = create(client).get_json()["id"]
    assert client.put(f"/api/subjects/{sid}", json={"pass_score": -5}).status_code == 400
    assert client.put(f"/api/subjects/{sid}", json={"title": ""}).status_code == 400
    assert client.get(f"/api/subjects/{sid}").get_json()["pass_score"] == 60


def test_delete_subject_also_deletes_its_tasks(app, client):
    make_user(client)
    sid = create(client).get_json()["id"]
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO tasks (subject_id, title, max_score) VALUES (?, 'Лаба', 10)", (sid,))
        db.commit()
    assert client.delete(f"/api/subjects/{sid}").status_code == 200
    assert client.get(f"/api/subjects/{sid}").status_code == 404
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) AS n FROM tasks").fetchone()["n"] == 0


def test_unknown_subject_returns_404(client):
    make_user(client)
    assert client.get("/api/subjects/9999").status_code == 404
