import pytest

from app.services import clean_number, compute_progress


def task(status="new", score=None, max_score=10):
    return {"status": status, "score": score, "max_score": max_score}


def tasks_done(done, total):
    return [task("done") for _ in range(done)] + [task("new") for _ in range(total - done)]


def test_no_tasks_gives_zero_percent_without_error():
    result = compute_progress([], 60)
    assert result["percent"] == 0
    assert result["total_tasks"] == 0
    assert result["reachable"] is False  # з нуля набрати 60 неможливо


def test_all_tasks_done_is_100_percent():
    assert compute_progress(tasks_done(10, 10), 0)["percent"] == 100


def test_half_done_is_50_percent():
    assert compute_progress(tasks_done(5, 10), 0)["percent"] == 50


@pytest.mark.parametrize("done,total,expected", [
    (1, 3, 33), (2, 3, 67), (1, 8, 13), (3, 8, 38), (0, 5, 0), (1, 1, 100),
])
def test_percent_rounding(done, total, expected):
    assert compute_progress(tasks_done(done, total), 0)["percent"] == expected


def test_earned_score_counts_only_graded_tasks():
    result = compute_progress([task(score=8), task(score=None), task(score=5.5)], 20)
    assert result["earned_score"] == 13.5


def test_score_counts_even_if_task_not_marked_done():
    result = compute_progress([task("new", score=7)], 5)
    assert result["earned_score"] == 7
    assert result["done_tasks"] == 0


def test_passed_when_earned_equals_pass_score():
    result = compute_progress([task(score=60, max_score=100)], 60)
    assert result["passed"] is True
    assert result["remaining_to_pass"] == 0


def test_remaining_to_pass():
    result = compute_progress([task(score=30, max_score=50)], 80)
    assert result["passed"] is False
    assert result["remaining_to_pass"] == 50


def test_pass_score_zero_means_always_passed():
    assert compute_progress([], 0)["passed"] is True


def test_reachable_uses_max_of_not_graded_tasks():
    tasks = [task(score=10, max_score=10), task(score=None, max_score=20)]
    assert compute_progress(tasks, 30)["reachable"] is True
    assert compute_progress(tasks, 31)["reachable"] is False


def test_float_sum_is_cleaned():
    result = compute_progress([task(score=0.1), task(score=0.2)], 0)
    assert result["earned_score"] == 0.3


@pytest.mark.parametrize("value,expected", [(10.0, 10), (0.1 + 0.2, 0.3), (7.5, 7.5), (0, 0)])
def test_clean_number(value, expected):
    assert clean_number(value) == expected
