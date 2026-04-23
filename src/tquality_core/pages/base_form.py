"""Base form / page object.

A Page is a specific case of a Form (full-context form). Extend `BaseForm` for
any addressable UI surface: main page, modal, header, sidebar, popup, etc.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tquality_core.elements.base_element import BaseElement


class BaseForm:
    """Driver-agnostic base for page objects and forms.

    Subclasses create elements in `__init__` and pass the `unique_element`
    (truly unique to this form) to `super().__init__()`. Tests never touch
    elements directly — they call form methods that describe business logic.
    """

    def __init__(self, unique_element: BaseElement, name: str = "") -> None:
        self._unique_element = unique_element
        self._name = name or self.__class__.__name__

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_element(self) -> BaseElement:
        return self._unique_element

    @property
    def is_displayed(self) -> bool:
        return self._unique_element.is_displayed

    def wait_for_displayed(self, timeout: float | None = None) -> "BaseForm":
        self._unique_element.wait_for_displayed(timeout)
        return self
