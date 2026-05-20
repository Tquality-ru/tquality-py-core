"""Тесты для XPathUtils."""
from __future__ import annotations

import pytest

from tquality_core.utils.xpath_utils import XPathUtils


@pytest.mark.parametrize(
    "value, expected",
    [
        (".", ""),
        ("./foo", "/foo"),
        (".//foo", "//foo"),
        ("foo", "/foo"),
        ("/foo", "/foo"),
        ("//foo", "//foo"),
    ],
)
def test_normalize(value: str, expected: str) -> None:
    assert XPathUtils.normalize(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("hello", "'hello'"),
        ("it's", '"it\'s"'),
        ('say "hi"', "'say \"hi\"'"),
        ("a'b\"c", "concat('a', \"'\", 'b\"c')"),
    ],
)
def test_literal(value: str, expected: str) -> None:
    assert XPathUtils.literal(value) == expected
