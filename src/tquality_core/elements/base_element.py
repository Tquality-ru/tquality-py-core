"""Абстрактная база для всех реализаций элементов (Selenium, Appium, WinAppDriver).

Пакеты, специфичные для драйвера, наследуют `BaseElement` для реализации
логики поиска и ожидания. Ядро определяет интерфейс, на который опираются
page object классы.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseElement(ABC):
    """Интерфейс единичного UI-элемента, идентифицируемого локатором.

    Подклассы должны реализовать методы поиска и ожидания через примитивы
    своего драйвера.
    """

    def __init__(self, by: object, locator: str, name: str = "") -> None:
        self._by = by
        self._locator = locator
        self._name = name or f"{self.__class__.__name__}({by}={locator!r})"

    @property
    def name(self) -> str:
        return self._name

    @property
    def by(self) -> object:
        return self._by

    @property
    def locator(self) -> str:
        return self._locator

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
        """Вернуть True, если элемент есть в DOM (может быть невидим)."""

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Вернуть True, если элемент активен и интерактивен."""

    @abstractmethod
    def get_attribute(self, attr: str) -> str | None:
        """Вернуть значение DOM-атрибута или None."""

    @abstractmethod
    def click(self) -> None:
        """Кликнуть по элементу (сначала дождется кликабельности)."""

    @abstractmethod
    def wait_for_displayed(self, timeout: float | None = None) -> BaseElement:
        """Ждать, пока элемент станет отображаемым. Возвращает self для чейнинга."""

    @abstractmethod
    def wait_until_visible(self, timeout: float | None = None) -> BaseElement:
        """Ждать, пока элемент станет видимым."""

    @abstractmethod
    def wait_until_clickable(self, timeout: float | None = None) -> BaseElement:
        """Ждать, пока элемент станет кликабельным."""

    @abstractmethod
    def wait_until_invisible(self, timeout: float | None = None) -> BaseElement:
        """Ждать, пока элемент станет невидимым."""

    @abstractmethod
    def wait_until_not_present(self, timeout: float | None = None) -> BaseElement:
        """Ждать, пока элемент исчезнет из DOM."""

    def __repr__(self) -> str:
        return self._name
