"""Тесты для BaseElement (абстрактный интерфейс)."""
from __future__ import annotations

import pytest

from tquality_core import BaseElement


def test_cannot_instantiate_abstract() -> None:
    with pytest.raises(TypeError):
        BaseElement("id", "my-id", "Элемент")  # type: ignore[abstract]


def test_concrete_subclass_exposes_locator_fields() -> None:
    class _Impl(BaseElement):
        @property
        def text(self) -> str:
            return ""

        @property
        def is_displayed(self) -> bool:
            return False

        @property
        def is_present(self) -> bool:
            return False

        @property
        def is_enabled(self) -> bool:
            return False

        def get_attribute(self, attr: str) -> str | None:
            return None

        def click(self) -> None:
            pass

        def wait_for_displayed(self, timeout: float | None = None) -> BaseElement:
            return self

        def wait_until_visible(self, timeout: float | None = None) -> BaseElement:
            return self

        def wait_until_clickable(self, timeout: float | None = None) -> BaseElement:
            return self

        def wait_until_invisible(self, timeout: float | None = None) -> BaseElement:
            return self

        def wait_until_not_present(self, timeout: float | None = None) -> BaseElement:
            return self

    el = _Impl("id", "my-id", "Элемент")
    assert el.name == "Элемент"
    assert el.by == "id"
    assert el.locator == "my-id"
