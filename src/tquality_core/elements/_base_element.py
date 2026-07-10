"""Абстрактный интерфейс единичного UI-элемента.

Драйвер-специфичные пакеты (Selenium, Appium, WinAppDriver) реализуют этот
интерфейс конкретными классами (обычно `Element(BaseElement)`). Ядро задаёт
лишь контракт, на который опираются page object'ы.

Ожидания вынесены в композицию: элемент отдаёт `wait` (привязанный к нему
`ElementWaiter`), а не несёт десяток `wait_until_*` методов на себе -
`element.wait.until_visible()`, `element.wait.until_clickable()` и т.д.
Тип `wait` платформенный, поэтому в ядре он типизирован как `Any`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from tquality_core.elements._base_by import BaseBy


class BaseElement(ABC):
    """Контракт UI-элемента, идентифицируемого локатором `BaseBy`."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Человекочитаемое имя элемента (для логов/отчётов)."""

    @property
    @abstractmethod
    def by(self) -> BaseBy:
        """Локатор элемента."""

    @property
    @abstractmethod
    def text(self) -> str:
        """Вернуть видимый текст элемента."""

    @property
    @abstractmethod
    def is_displayed(self) -> bool:
        """Вернуть True, если элемент существует И видим."""

    @property
    @abstractmethod
    def is_present(self) -> bool:
        """Вернуть True, если элемент есть в дереве (может быть невидим)."""

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Вернуть True, если элемент активен и интерактивен."""

    @property
    @abstractmethod
    def wait(self) -> Any:
        """Привязанный к элементу `ElementWaiter` (платформенный тип).
        Точка композиции для ожиданий: `element.wait.until_visible()` ..."""

    @abstractmethod
    def get_attribute(self, attr: str) -> str | None:
        """Вернуть значение атрибута или None."""

    @abstractmethod
    def click(self) -> None:
        """Кликнуть по элементу (с учётом предусловия-состояния)."""


__all__ = ["BaseElement"]
