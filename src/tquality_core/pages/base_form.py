"""Базовая форма / page object.

Page - частный случай Form (форма с полным контекстом). Наследуйте `BaseForm`
для любой адресуемой UI-области: главной страницы, модального окна, шапки,
боковой панели, попапа и т.д.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tquality_core.elements.base_element import BaseElement


class BaseForm:
    """Драйвер-независимая база для page object'ов и форм.

    Подклассы создают элементы в `__init__` и передают `unique_element`
    (действительно уникальный для этой формы) в `super().__init__()`. Тесты
    никогда не обращаются к элементам напрямую - они вызывают методы формы,
    описывающие бизнес-логику.
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

    def wait_for_displayed(self, timeout: float | None = None) -> BaseForm:
        self._unique_element.wait_for_displayed(timeout)
        return self
