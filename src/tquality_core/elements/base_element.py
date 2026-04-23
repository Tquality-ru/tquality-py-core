"""Abstract base for all element implementations (Selenium, Appium, WinAppDriver).

Driver-specific packages extend `BaseElement` to provide find/wait logic.
The core defines the interface that page objects rely on.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseElement(ABC):
    """Interface for a single UI element identified by a locator.

    Subclasses must implement `_find_element()` and `_find_all_elements()` to
    return driver-specific element handles, and the wait methods via their
    driver's wait primitives.
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
        """Return the element's visible text."""

    @property
    @abstractmethod
    def is_displayed(self) -> bool:
        """Return True if the element exists AND is visible."""

    @property
    @abstractmethod
    def is_present(self) -> bool:
        """Return True if the element exists in the DOM (may not be visible)."""

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Return True if the element is enabled/interactable."""

    @abstractmethod
    def get_attribute(self, attr: str) -> str | None:
        """Return the value of a DOM attribute, or None."""

    @abstractmethod
    def click(self) -> None:
        """Click the element (waits for clickability first)."""

    @abstractmethod
    def wait_for_displayed(self, timeout: float | None = None) -> "BaseElement":
        """Block until the element is displayed. Returns self for chaining."""

    @abstractmethod
    def wait_until_visible(self, timeout: float | None = None) -> "BaseElement":
        ...

    @abstractmethod
    def wait_until_clickable(self, timeout: float | None = None) -> "BaseElement":
        ...

    @abstractmethod
    def wait_until_invisible(self, timeout: float | None = None) -> "BaseElement":
        ...

    @abstractmethod
    def wait_until_not_present(self, timeout: float | None = None) -> "BaseElement":
        ...

    def __repr__(self) -> str:
        return self._name
