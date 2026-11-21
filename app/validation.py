import math
from datetime import date


MAX_NUMBER = 1_000_000  # верхня межа для балів: захист від переповнення сум
MIN_PASSWORD_LEN = 6
MAX_PASSWORD_LEN = 128  # довгі паролі уповільнюють хешування і дозволяють перевантажити сервер


class ValidationError(Exception):
    """Помилка перевірки вхідних даних (повертається клієнту як 400)."""


def parse_text(value, field, max_len=100, required=True):
    text = "" if value is None else str(value).strip()
    if required and not text:
        raise ValidationError(f"Поле «{field}» не може бути порожнім")
    if len(text) > max_len:
        raise ValidationError(f"Поле «{field}» не може бути довшим за {max_len} символів")
    return text


def parse_number(value, field, minimum=0, allow_zero=True, maximum=MAX_NUMBER):
    """Приймає тільки скінченне число в межах [minimum, maximum] (не рядок, не булеве значення)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"Поле «{field}» має бути числом")
    if not math.isfinite(value):
        raise ValidationError(f"Поле «{field}» має бути скінченним числом")
    if value < minimum or (not allow_zero and value == minimum):
        sign = "більшим за" if not allow_zero else "не меншим за"
        raise ValidationError(f"Поле «{field}» має бути {sign} {minimum}")
    if value > maximum:
        raise ValidationError(f"Поле «{field}» не може бути більшим за {maximum}")
    return value


def parse_date(value, field):
    """Дата у форматі РРРР-ММ-ДД або None, якщо дату не вказано."""
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ValidationError(f"Поле «{field}» має бути датою у форматі РРРР-ММ-ДД")


def parse_choice(value, field, allowed):
    if value not in allowed:
        raise ValidationError(f"Поле «{field}» має бути одним зі значень: {', '.join(allowed)}")
    return value


def parse_password(value):
    password = "" if value is None else str(value)
    if not MIN_PASSWORD_LEN <= len(password) <= MAX_PASSWORD_LEN:
        raise ValidationError(
            f"Пароль має містити від {MIN_PASSWORD_LEN} до {MAX_PASSWORD_LEN} символів"
        )
    return password
