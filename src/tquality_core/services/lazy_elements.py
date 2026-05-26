"""`LazyElements`: лениво-резолвимая коллекция типизированных элементов.

Платформо-агностичная: ждёт от инжектированного `driver_resolver`
объект, на котором есть `find_elements(by, value)` - сигнатура,
общая для appium-WebDriver, selenium-WebDriver, BrowserService и
AppiumDriverService.

### Кэширование между итерациями

В рамках одной итерации/comprehension (`__iter__`, `to_list`,
`__getitem__(slice)`) `find_elements` вызывается ровно один раз -
элементы привязаны к этому snapshot'у, и `_find()` возвращает
сохранённый элемент без повторного похода в иерархию.

Между итерациями кэш не переиспользуется. Одиночный индексный доступ
`collection[i]` всегда делает свежий resolve.
"""
from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any, Callable, overload


class LazyElements[E](Sequence[E]):
    def __init__(
        self,
        element_cls: Callable[..., E],
        by: Any,
        name_prefix: str = "",
        *,
        driver_resolver: Callable[[], Any],
    ) -> None:
        self._element_cls = element_cls
        self._by = by
        self._name_prefix = name_prefix or getattr(element_cls, "__name__", "Element")
        self._driver_resolver = driver_resolver

    @property
    def _driver(self) -> Any:
        return self._driver_resolver()

    def __len__(self) -> int:
        return len(self._driver.find_elements(*self._by))

    def __iter__(self) -> Iterator[E]:
        snapshot = self._driver.find_elements(*self._by)
        for i in range(len(snapshot)):
            yield self._make(i, snapshot)

    @overload
    def __getitem__(self, index: int) -> E: ...
    @overload
    def __getitem__(self, index: slice) -> list[E]: ...
    def __getitem__(self, index: int | slice) -> E | list[E]:
        if isinstance(index, slice):
            snapshot = self._driver.find_elements(*self._by)
            return [
                self._make(i, snapshot)
                for i in range(*index.indices(len(snapshot)))
            ]
        if index < 0:
            index += len(self)
        return self._make(index)

    def to_list(self) -> list[E]:
        snapshot = self._driver.find_elements(*self._by)
        return [self._make(i, snapshot) for i in range(len(snapshot))]

    def _make(
        self,
        index: int,
        snapshot: list[Any] | None = None,
    ) -> E:
        name = f"{self._name_prefix} #{index + 1}"
        elem = self._element_cls(self._by, name)
        by = self._by

        if snapshot is None:
            def _find() -> Any:
                return self._driver.find_elements(*by)[index]
        else:
            bound = snapshot

            def _find() -> Any:
                return bound[index]

        elem._find = _find  # type: ignore[attr-defined]
        return elem


__all__ = ["LazyElements"]
