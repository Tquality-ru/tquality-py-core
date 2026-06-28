"""Тесты для BaseElement (абстрактный интерфейс) и BaseBy."""
from __future__ import annotations

from typing import Any, override

import pytest

from tquality_core import BaseBy, BaseElement


def test_cannot_instantiate_abstract() -> None:
    with pytest.raises(TypeError):
        BaseElement()  # type: ignore[abstract]


def test_baseby_str_format() -> None:
    assert str(BaseBy.css_selector(".button")) == "css selector=.button"


def test_baseby_unpacks_to_strategy_value() -> None:
    by, value = BaseBy.xpath("//a")
    assert by == "xpath"
    assert value == "//a"


def test_baseby_common_strategies() -> None:
    assert BaseBy.id("x") == BaseBy("id", "x")
    assert BaseBy.name("x") == BaseBy("name", "x")
    assert BaseBy.class_name("x") == BaseBy("class name", "x")
    assert BaseBy.tag_name("a") == BaseBy("tag name", "a")
    assert BaseBy.link_text("go") == BaseBy("link text", "go")
    assert BaseBy.partial_link_text("go") == BaseBy("partial link text", "go")


def test_baseby_replace_keeps_strategy() -> None:
    assert BaseBy.xpath("//a")._replace(value="//b") == BaseBy.xpath("//b")


def test_baseby_is_frozen() -> None:
    with pytest.raises(Exception):
        setattr(BaseBy.id("x"), "value", "y")


class _Impl(BaseElement):
    def __init__(self, by: BaseBy, name: str = "") -> None:
        self._by = by
        self._name = name or f"{self.__class__.__name__}({by})"

    @property
    @override
    def name(self) -> str:
        return self._name

    @property
    @override
    def by(self) -> BaseBy:
        return self._by

    @property
    @override
    def text(self) -> str:
        return ""

    @property
    @override
    def is_displayed(self) -> bool:
        return False

    @property
    @override
    def is_present(self) -> bool:
        return False

    @property
    @override
    def is_enabled(self) -> bool:
        return False

    @property
    @override
    def wait(self) -> Any:
        return None

    @override
    def get_attribute(self, attr: str) -> str | None:
        return None

    @override
    def click(self) -> None:
        pass


def test_concrete_subclass_exposes_fields() -> None:
    el = _Impl(BaseBy.id("my-id"), "Элемент")
    assert el.name == "Элемент"
    assert el.by == BaseBy("id", "my-id")
    assert el.by.value == "my-id"


def test_default_name_includes_locator() -> None:
    assert _Impl(BaseBy.css_selector(".foo")).name == "_Impl(css selector=.foo)"
