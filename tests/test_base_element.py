"""Тесты для BaseElement (абстрактный интерфейс) и Locator."""
from __future__ import annotations

import pytest

from tquality_core import BaseElement, Locator


def test_cannot_instantiate_abstract() -> None:
    with pytest.raises(TypeError):
        BaseElement(Locator("id", "my-id"), "Элемент")  # type: ignore[abstract]


def test_locator_str_format() -> None:
    loc = Locator("css", ".button")
    assert str(loc) == "css=.button"


def test_locator_repr_format() -> None:
    loc = Locator("xpath", "//div[@id='x']")
    assert repr(loc) == "Locator(by='xpath', value=\"//div[@id='x']\")"


def test_locator_is_tuple_like() -> None:
    loc = Locator("id", "my-id")
    by, value = loc
    assert by == "id"
    assert value == "my-id"
    assert loc.by == "id"
    assert loc.value == "my-id"


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

    el = _Impl(Locator("id", "my-id"), "Элемент")
    assert el.name == "Элемент"
    assert el.locator == Locator("id", "my-id")
    assert el.locator.by == "id"
    assert el.locator.value == "my-id"


def test_default_name_includes_locator() -> None:
    class _Impl(BaseElement):
        @property
        def text(self) -> str: return ""
        @property
        def is_displayed(self) -> bool: return False
        @property
        def is_present(self) -> bool: return False
        @property
        def is_enabled(self) -> bool: return False
        def get_attribute(self, attr: str) -> str | None: return None
        def click(self) -> None: pass
        def wait_for_displayed(self, timeout: float | None = None) -> BaseElement: return self
        def wait_until_visible(self, timeout: float | None = None) -> BaseElement: return self
        def wait_until_clickable(self, timeout: float | None = None) -> BaseElement: return self
        def wait_until_invisible(self, timeout: float | None = None) -> BaseElement: return self
        def wait_until_not_present(self, timeout: float | None = None) -> BaseElement: return self

    el = _Impl(Locator("css", ".foo"))
    assert el.name == "_Impl(css=.foo)"
