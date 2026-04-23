from __future__ import annotations

import re


class StringUtils:
    _DIGITS_PATTERN = re.compile(r"\d+")
    _NON_DIGIT_PATTERN = re.compile(r"[^\d]")

    @staticmethod
    def get_digits(value: str) -> str:
        return re.sub(StringUtils._NON_DIGIT_PATTERN, "", value)

    @staticmethod
    def parse_int(value: str, default: int = 0) -> int:
        digits = StringUtils.get_digits(value)
        return int(digits) if digits else default

    @staticmethod
    def extract_first_number(value: str) -> int | None:
        match = StringUtils._DIGITS_PATTERN.search(value)
        return int(match.group()) if match else None
