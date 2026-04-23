"""Тесты для StringUtils."""
from __future__ import annotations

from tquality_core import StringUtils


def test_get_digits_strips_non_digits() -> None:
    assert StringUtils.get_digits("5 000 ₽") == "5000"
    assert StringUtils.get_digits("abc") == ""
    assert StringUtils.get_digits("") == ""


def test_parse_int_returns_default_when_no_digits() -> None:
    assert StringUtils.parse_int("abc") == 0
    assert StringUtils.parse_int("abc", default=-1) == -1


def test_parse_int_parses_digits() -> None:
    assert StringUtils.parse_int("5 000 ₽") == 5000
    assert StringUtils.parse_int("price: 123.45") == 12345


def test_extract_first_number() -> None:
    assert StringUtils.extract_first_number("Chrome 146.0.1") == 146
    assert StringUtils.extract_first_number("no numbers here") is None
    assert StringUtils.extract_first_number("") is None
