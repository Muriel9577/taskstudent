def make_user(client, email="a@example.com"):
    client.post("/api/logout")
    assert client.post("/api/register", json={"email": email, "password": "secret123", "name": "A"}).status_code == 201


def setup_subject(client, pass_score=60):
    return client.post("/api/subjects", json={"title": "Математика", "pass_score": pass_score}).get_json()["id"]


def add_task(client, sid, **kw):
    return client.post(f"/api/subjects/{sid}/tasks", json={"title": "Т", "max_score": 10, **kw}).get_json()["id"]


def test_requires_login(client):
    assert client.get("/api/subjects/1/progress").status_code == 401


def test_empty_subject_progress(client):
    make_user(client)
    sid = setup_subject(client)
    data = client.get(f"/api/subjects/{sid}/progress").get_json()
    assert data["percent"] == 0 and data["total_tasks"] == 0


def test_progress_after_changes(client):
    make_user(client)
    sid = setup_subject(client, pass_score=15)
    t1 = add_task(client, sid)
    add_task(client, sid)
    client.put(f"/api/tasks/{t1}", json={"status": "done", "score": 9})
    data = client.get(f"/api/subjects/{sid}/progress").get_json()
    assert (data["done_tasks"], data["total_tasks"], data["percent"]) == (1, 2, 50)
    assert data["earned_score"] == 9
    assert data["remaining_to_pass"] == 6
    assert data["max_possible_score"] == 19
    assert data["reachable"] is True


def test_numbers_are_integers_when_whole(client):
    make_user(client)
    sid = setup_subject(client, pass_score=60)
    t = add_task(client, sid)
    client.put(f"/api/tasks/{t}", json={"score": 8})
    raw = client.get(f"/api/subjects/{sid}/progress").get_data(as_text=True)
    assert '"earned_score":8,' in raw.replace(" ", "").replace("\n", "")


def test_other_user_gets_404(client):
    make_user(client, "a@example.com")
    sid = setup_subject(client)
    make_user(client, "b@example.com")
    assert client.get(f"/api/subjects/{sid}/progress").status_code == 404
