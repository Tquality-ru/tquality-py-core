"""Драйвер-независимое представление локатора элемента.

Локатор - пара `(strategy, value)`, где strategy - это стратегия поиска
(CSS-селектор, XPath, ID и т.д. - зависит от драйвера), а value - сам
локатор (`.button`, `//div`, `my-id`).

Тип strategy остается `str`, потому что разные драйверы используют разные
значения: Selenium - строки из `By.*` (`"css selector"`, `"xpath"`...),
Appium добавляет mobile-специфичные (`"accessibility id"`, `"android uiautomator"`).
"""
from __future__ import annotations

from typing import NamedTuple


class Locator(NamedTuple):
    """Пара (стратегия_поиска, локатор) для идентификации элемента."""

    by: str
    value: str

    def __str__(self) -> str:
        return f"{self.by}={self.value}"

    def __repr__(self) -> str:
        return f"Locator(by={self.by!r}, value={self.value!r})"
