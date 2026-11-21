"""Граничні випадки, знайдені під час перевірки якості (етап 6)."""
import pytest


def register(client, email="a@example.com", password="secret123", name="A"):
    client.post("/api/logout")
    return client.post("/api/register", json={"email": email, "password": password, "name": name})


@pytest.fixture
def sid(client):
    assert register(client).status_code == 201
    return client.post("/api/subjects", json={"title": "Предмет", "pass_score": 10}).get_json()["id"]


def add_task(client, sid, **kw):
    return client.post(f"/api/subjects/{sid}/tasks", json={"title": "Т", "max_score": 10, **kw})


# --- числа ---

def test_task_numbers_are_returned_without_trailing_zero(client, sid):
    task = add_task(client, sid).get_json()
    raw = client.get(f"/api/tasks/{task['id']}").get_data(as_text=True).replace(" ", "")
    assert '"max_score":10,' in raw


def test_error_message_shows_whole_number_without_dot_zero(client, sid):
    res = add_task(client, sid, score=11)
    assert res.status_code == 400
    assert "10.0" not in res.get_json()["error"]


def test_huge_scores_are_rejected_instead_of_crashing_progress(client, sid):
    """Регресія: два бали 1e308 давали суму inf, і /progress падав з OverflowError (500)."""
    for _ in range(2):
        res = add_task(client, sid, max_score=1e308)
        assert res.status_code == 400
    assert client.get(f"/api/subjects/{sid}/progress").status_code == 200


def test_many_tasks_with_maximum_allowed_score_do_not_overflow(client, sid):
    for _ in range(5):
        tid = add_task(client, sid, max_score=1_000_000, score=1_000_000).get_json()["id"]
        assert tid
    data = client.get(f"/api/subjects/{sid}/progress").get_json()
    assert data["earned_score"] == 5_000_000


def test_unreasonably_large_pass_score_rejected(client):
    register(client)
    res = client.post("/api/subjects", json={"title": "X", "pass_score": 1e308})
    assert res.status_code == 400


# --- довжини вхідних даних ---

def test_very_long_password_rejected(client):
    assert register(client, password="a" * 100_000).status_code == 400


def test_very_long_name_rejected(client):
    assert register(client, name="І" * 500).status_code == 400


def test_very_long_email_rejected(client):
    assert register(client, email="a" * 300 + "@example.com").status_code == 400


# --- безпека ---

def test_html_in_titles_is_stored_as_plain_text(client, sid):
    payload = "<img src=x onerror=alert(1)>"
    task = add_task(client, sid, title=payload).get_json()
    assert client.get(f"/api/tasks/{task['id']}").get_json()["title"] == payload  # зберігається як текст


def test_session_cookie_is_httponly_and_samesite(client):
    res = register(client)
    cookie = res.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_non_json_body_is_rejected_cleanly(client):
    res = client.post("/api/register", data="email=a@a.ua", content_type="text/plain")
    assert res.status_code == 400


def test_malformed_json_returns_400_not_500(client):
    res = client.post("/api/login", data="{bad json", content_type="application/json")
    assert res.status_code == 401 or res.status_code == 400


def test_secret_key_is_random_and_persistent(tmp_path):
    from app import create_app

    first = create_app({"DATABASE": str(tmp_path / "a.db")}, instance_path=str(tmp_path))
    second = create_app({"DATABASE": str(tmp_path / "b.db")}, instance_path=str(tmp_path))
    key = first.config["SECRET_KEY"]
    assert key != "dev-change-me" and len(key) >= 32
    assert second.config["SECRET_KEY"] == key
