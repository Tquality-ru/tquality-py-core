"""Тесты для FormattableElement (шаблонный элемент с параметризуемым локатором)."""
from __future__ import annotations

from typing import Any, Self

from tquality_core import BaseBy, BaseElement, FormattableElement


class _By(BaseBy):
    """Стенд-ин для платформенного `By` - подкласс `BaseBy` со своей стратегией."""

    @classmethod
    def accessibility_id(cls, value: str) -> Self:
        return cls("accessibility id", value)


class _Impl(BaseElement):
    def __init__(self, by: BaseBy, name: str = "") -> None:
        self._by = by
        self._name = name or f"{self.__class__.__name__}({by})"

    @property
    def name(self) -> str: return self._name
    @property
    def by(self) -> BaseBy: return self._by
    @property
    def text(self) -> str: return ""
    @property
    def is_displayed(self) -> bool: return False
    @property
    def is_present(self) -> bool: return False
    @property
    def is_enabled(self) -> bool: return False
    @property
    def wait(self) -> Any: return None
    def get_attribute(self, attr: str) -> str | None: return None
    def click(self) -> None: pass


def _template(value: str) -> FormattableElement[_Impl]:
    return FormattableElement(BaseBy.xpath(value), _Impl)


def test_format_returns_concrete_element() -> None:
    el = _template("//tr[td={!r}]").format("Иванов")
    assert isinstance(el, _Impl)


def test_format_positional_placeholder() -> None:
    el = _template("//tr[td[normalize-space()={!r}]]").format("Иванов")
    assert el.by == BaseBy.xpath("//tr[td[normalize-space()='Иванов']]")


def test_format_named_placeholders() -> None:
    el = _template("//tr[@data-id={row}]/td[{col}]").format(row=42, col=3)
    assert el.by == BaseBy.xpath("//tr[@data-id=42]/td[3]")


def test_format_keeps_strategy() -> None:
    el = FormattableElement(BaseBy.css_selector(".item-{}"), _Impl).format(7)
    assert el.by == BaseBy.css_selector(".item-7")


def test_template_locator_unchanged() -> None:
    tmpl = _template("//li[{}]")
    tmpl.format(1)
    tmpl.format(2)
    assert tmpl.locator == BaseBy.xpath("//li[{}]")


def test_default_name_includes_template_locator() -> None:
    tmpl = FormattableElement(BaseBy.css_selector(".x-{}"), _Impl)
    assert tmpl.name == "FormattableElement(css selector=.x-{})"
    assert repr(tmpl) == "FormattableElement(css selector=.x-{})"


def test_explicit_name() -> None:
    tmpl = FormattableElement(BaseBy.css_selector(".x-{}"), _Impl, name="Строка")
    assert tmpl.name == "Строка"


def test_accepts_by_subclass_preserving_concrete_type() -> None:
    # Платформенный `By` - подкласс `BaseBy`, поэтому принимается напрямую,
    # а `format()` сохраняет его конкретный тип (через `_replace`).
    captured: list[_By] = []

    def build(loc: _By) -> _Impl:
        captured.append(loc)
        return _Impl(loc)

    FormattableElement(_By.accessibility_id("cell_{}"), build).format(3)
    (loc,) = captured
    assert isinstance(loc, _By)
    assert loc == _By("accessibility id", "cell_3")
