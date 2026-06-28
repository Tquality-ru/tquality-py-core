"""Шаблонный элемент с параметризуемым локатором.

`FormattableElement` хранит локатор-шаблон (значение содержит
placeholder'ы в синтаксисе :py:meth:`str.format` - позиционные `{}`/`{0}`
или именованные `{id}`) и фабрику, собирающую конкретный элемент `E` по
готовому локатору. Сам по себе шаблон элементом не является - искать
по нему нечего, пока placeholder'ы не подставлены.

`format(*args, **kwargs)` форматирует **только** `value` локатора
(стратегия `by` не трогается) и возвращает обычный, готовый к действиям
элемент `E`.

```python
# Шаблон строки таблицы по тексту ячейки.
row = element_factory.formattable.button(
    By.xpath("//tr[td[normalize-space()={!r}]]"),
)
row.format("Иванов").click()        # //tr[td[normalize-space()='Иванов']]

# Именованные placeholder'ы.
cell = element_factory.formattable.label(
    By.xpath("//tr[@data-id={row}]/td[{col}]"),
)
cell.format(row=42, col=3).text     # //tr[@data-id=42]/td[3]
```
"""
from __future__ import annotations

from typing import Any, Callable, Generic, override

from typing_extensions import TypeVar

from tquality_core.elements._base_by import BaseBy
from tquality_core.elements._base_element import BaseElement

E = TypeVar("E", bound=BaseElement)
L = TypeVar("L", bound=BaseBy, default=BaseBy)


class FormattableElement(Generic[E, L]):
    """Шаблон элемента: локатор с placeholder'ами + фабрика конкретного `E`.

    Параметризуется типом элемента `E` и типом локатора `L` (любой подкласс
    `BaseBy`, напр. платформенный `By`). `L` по умолчанию - `BaseBy`, поэтому
    в типовых аннотациях достаточно `FormattableElement[E]` не указывая локатор.

    Не наследует `BaseElement` намеренно - до `format()` искать нечего,
    поэтому здесь нет ни `click()`, ни `text`, ни ожиданий. Единственная
    операция - подстановка аргументов в локатор.
    """

    def __init__(
        self,
        locator: L,
        builder: Callable[[L], E],
        name: str = "",
    ) -> None:
        self._locator = locator
        self._builder = builder
        self._name = name or f"{self.__class__.__name__}({locator})"

    @property
    def name(self) -> str:
        return self._name

    @property
    def locator(self) -> L:
        """Локатор-шаблон (с неподставленными placeholder'ами)."""
        return self._locator

    def format(self, *args: Any, **kwargs: Any) -> E:
        """Подставить аргументы в `value` локатора и вернуть готовый `E`.

        Форматирование - через :py:meth:`str.format`, поэтому работают и
        позиционные (`{}`, `{0}`), и именованные (`{name}`) placeholder'ы,
        и спецификаторы (`{!r}`, `{:>4}`). Стратегия `by` не меняется.
        """
        value = self._locator.value.format(*args, **kwargs)
        return self._builder(self._locator._replace(value=value))

    @override
    def __repr__(self) -> str:
        return self._name


__all__ = ["FormattableElement"]
