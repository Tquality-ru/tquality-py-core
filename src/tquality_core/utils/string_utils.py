"""Утилиты работы со строками."""
from __future__ import annotations

import re


class StringUtils:
    """Часто используемые операции парсинга строк."""

    _DIGITS_PATTERN = re.compile(r"\d+")
    _NON_DIGIT_PATTERN = re.compile(r"[^\d]")

    @staticmethod
    def get_digits(value: str) -> str:
        """Вернуть только цифры из строки. Пример: '5 000 ₽' -> '5000'."""
        return re.sub(StringUtils._NON_DIGIT_PATTERN, "", value)

    @staticmethod
    def parse_int(value: str, default: int = 0) -> int:
        """Распарсить число из строки, возвращая default если цифр нет."""
        digits = StringUtils.get_digits(value)
        return int(digits) if digits else default

    @staticmethod
    def extract_first_number(value: str) -> int | None:
        """Извлечь первое число из строки. Пример: 'Chrome 146.0.1' -> 146."""
        match = StringUtils._DIGITS_PATTERN.search(value)
        return int(match.group()) if match else None
