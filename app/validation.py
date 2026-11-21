import math


class ValidationError(Exception):
    """Помилка перевірки вхідних даних (повертається клієнту як 400)."""


def parse_text(value, field, max_len=100, required=True):
    text = "" if value is None else str(value).strip()
    if required and not text:
        raise ValidationError(f"Поле «{field}» не може бути порожнім")
    if len(text) > max_len:
        raise ValidationError(f"Поле «{field}» не може бути довшим за {max_len} символів")
    return text


def parse_number(value, field, minimum=0, allow_zero=True):
    """Приймає тільки скінченне число (не рядок, не булеве значення)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"Поле «{field}» має бути числом")
    if not math.isfinite(value):
        raise ValidationError(f"Поле «{field}» має бути скінченним числом")
    if value < minimum or (not allow_zero and value == minimum):
        sign = "більшим за" if not allow_zero else "не меншим за"
        raise ValidationError(f"Поле «{field}» має бути {sign} {minimum}")
    return value
