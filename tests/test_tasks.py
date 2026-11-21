import pytest


def make_user(client, email="a@example.com"):
    client.post("/api/logout")
    res = client.post("/api/register", json={"email": email, "password": "secret123", "name": "A"})
    assert res.status_code == 201


def login(client, email):
    client.post("/api/logout")
    assert client.post("/api/login", json={"email": email, "password": "secret123"}).status_code == 200


def make_subject(client, title="Математика"):
    return client.post("/api/subjects", json={"title": title, "pass_score": 60}).get_json()["id"]


def make_task(client, sid, **overrides):
    payload = {"title": "Лаба 1", "max_score": 10, **overrides}
    return client.post(f"/api/subjects/{sid}/tasks", json=payload)


@pytest.fixture
def sid(client):
    make_user(client)
    return make_subject(client)


def test_requires_login(client):
    assert client.get("/api/subjects/1/tasks").status_code == 401
    assert client.get("/api/tasks/1").status_code == 401


def test_create_task_defaults(client, sid):
    res = make_task(client, sid)
    assert res.status_code == 201
    task = res.get_json()
    assert task["status"] == "new"
    assert task["score"] is None
    assert task["description"] == ""
    assert task["deadline"] is None


def test_create_full_task(client, sid):
    res = make_task(client, sid, description="Звіт", deadline="2026-12-01", score=8, status="done")
    task = res.get_json()
    assert (task["deadline"], task["score"], task["status"]) == ("2026-12-01", 8, "done")


@pytest.mark.parametrize("overrides", [
    {"title": ""},
    {"max_score": 0},
    {"max_score": -5},
    {"max_score": "10"},
    {"max_score": None},
    {"score": 11},
    {"score": -1},
    {"score": "5"},
    {"deadline": "01.12.2026"},
    {"deadline": "2026-13-45"},
    {"status": "maybe"},
])
def test_invalid_task_rejected(client, sid, overrides):
    assert make_task(client, sid, **overrides).status_code == 400


def test_score_equal_to_max_is_allowed(client, sid):
    assert make_task(client, sid, score=10).status_code == 201


def test_list_sorted_by_deadline_with_empty_last(client, sid):
    make_task(client, sid, title="Без дати")
    make_task(client, sid, title="Пізно", deadline="2026-12-20")
    make_task(client, sid, title="Рано", deadline="2026-12-01")
    titles = [t["title"] for t in client.get(f"/api/subjects/{sid}/tasks").get_json()]
    assert titles == ["Рано", "Пізно", "Без дати"]


def test_change_status(client, sid):
    tid = make_task(client, sid).get_json()["id"]
    res = client.put(f"/api/tasks/{tid}", json={"status": "done"})
    assert res.get_json()["status"] == "done"
    assert client.put(f"/api/tasks/{tid}", json={"status": "bad"}).status_code == 400


def test_partial_update_keeps_other_fields(client, sid):
    tid = make_task(client, sid, deadline="2026-12-01", score=7).get_json()["id"]
    task = client.put(f"/api/tasks/{tid}", json={"title": "Нова назва"}).get_json()
    assert (task["title"], task["deadline"], task["score"]) == ("Нова назва", "2026-12-01", 7)


def test_set_and_clear_score(client, sid):
    tid = make_task(client, sid).get_json()["id"]
    assert client.put(f"/api/tasks/{tid}", json={"score": 9}).get_json()["score"] == 9
    assert client.put(f"/api/tasks/{tid}", json={"score": None}).get_json()["score"] is None


def test_score_above_max_rejected_on_update(client, sid):
    tid = make_task(client, sid).get_json()["id"]
    assert client.put(f"/api/tasks/{tid}", json={"score": 11}).status_code == 400
    assert client.get(f"/api/tasks/{tid}").get_json()["score"] is None


def test_lowering_max_score_below_existing_score_rejected(client, sid):
    tid = make_task(client, sid, score=8).get_json()["id"]
    res = client.put(f"/api/tasks/{tid}", json={"max_score": 5})
    assert res.status_code == 400
    assert client.get(f"/api/tasks/{tid}").get_json()["max_score"] == 10


def test_lowering_max_score_together_with_score_is_allowed(client, sid):
    tid = make_task(client, sid, score=8).get_json()["id"]
    res = client.put(f"/api/tasks/{tid}", json={"max_score": 5, "score": 4})
    assert res.status_code == 200


def test_delete_task(client, sid):
    tid = make_task(client, sid).get_json()["id"]
    assert client.delete(f"/api/tasks/{tid}").status_code == 200
    assert client.get(f"/api/tasks/{tid}").status_code == 404


def test_other_user_cannot_touch_tasks(client, sid):
    tid = make_task(client, sid).get_json()["id"]
    make_user(client, "b@example.com")
    assert client.get(f"/api/subjects/{sid}/tasks").status_code == 404
    assert make_task(client, sid).status_code == 404
    assert client.get(f"/api/tasks/{tid}").status_code == 404
    assert client.put(f"/api/tasks/{tid}", json={"title": "X"}).status_code == 404
    assert client.delete(f"/api/tasks/{tid}").status_code == 404
    login(client, "a@example.com")
    assert client.get(f"/api/tasks/{tid}").get_json()["title"] == "Лаба 1"


def test_unknown_subject_or_task_returns_404(client, sid):
    assert client.get("/api/subjects/9999/tasks").status_code == 404
    assert client.get("/api/tasks/9999").status_code == 404
