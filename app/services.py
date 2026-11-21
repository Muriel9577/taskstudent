"""Бізнес-логіка: прогрес по предмету та порівняння балів із прохідним."""


def clean_number(value):
    """Прибирає зайвий «.0» і похибки дробових сум: 10.0 -> 10, 0.1 + 0.2 -> 0.3."""
    value = round(float(value), 2)
    return int(value) if value == int(value) else value


def compute_progress(tasks, pass_score):
    """Рахує прогрес по предмету.

    tasks - список словників із ключами status, score, max_score.
    Відсоток - це частка виконаних завдань, округлена до цілого (0,5 округлюється вгору).
    Бали рахуються по всіх завданнях з виставленим балом, незалежно від статусу.
    """
    total = len(tasks)
    done = sum(1 for t in tasks if t["status"] == "done")
    # Цілочисельна арифметика: (200 * done + total) // (2 * total) = округлення half-up
    percent = (200 * done + total) // (2 * total) if total else 0

    earned = sum(t["score"] for t in tasks if t["score"] is not None)
    not_graded_max = sum(t["max_score"] for t in tasks if t["score"] is None)
    max_possible = earned + not_graded_max

    return {
        "total_tasks": total,
        "done_tasks": done,
        "percent": percent,
        "earned_score": clean_number(earned),
        "pass_score": clean_number(pass_score),
        "remaining_to_pass": clean_number(max(0, pass_score - earned)),
        "passed": earned >= pass_score,
        "max_possible_score": clean_number(max_possible),
        "reachable": max_possible >= pass_score,
    }
