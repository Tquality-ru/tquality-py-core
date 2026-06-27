"""Юнит-тесты ContentType."""
from __future__ import annotations

from enum import StrEnum

from tquality_core.http_client import ContentType


class TestContentType:
    def test_is_str_enum_so_members_are_usable_as_header_values(self) -> None:
        # Поведение, на которое опирается клиент: вариант можно отдать как значение
        # заголовка/Accept напрямую, без `.value`. Сломается, если станет обычным Enum.
        assert issubclass(ContentType, StrEnum)
        assert all(isinstance(member, str) for member in ContentType)
