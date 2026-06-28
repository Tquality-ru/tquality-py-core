"""Драйвер-независимый локатор-база со стратегиями, общими для всех платформ.

`BaseBy` - неизменяемая пара `(by, value)`, где `by` - стратегия поиска
(строка), а `value` - сам локатор. Это подкласс `tuple[str, str]`, поэтому
прозрачно подходит и для `driver.find_element(*by)`, и для любого
selenium/appium API, ожидающего `(strategy, value)`-кортеж - без приведения
типов.

В отличие от «голого» кортежа, `BaseBy` - это **наследуемый** базовый класс
с classmethod-конструкторами под общие W3C-стратегии (`xpath`, `css_selector`,
`id`, `name`, `class_name`, `tag_name`, `link_text`, `partial_link_text`).
Платформенные пакеты наследуют его и добавляют свои стратегии, не дублируя
общие и не завися от selenium:

```python
class By(BaseBy):                       # tquality-py-appium
    @classmethod
    def accessibility_id(cls, value: str) -> Self:
        return cls("accessibility id", value)

By.xpath("//x")            # унаследовано из BaseBy
By.accessibility_id("ok")  # своё
```

Конструкторы используют `cls`, поэтому на подклассе возвращают этот же
подкласс - типизация `By.xpath(...) -> By` сохраняется автоматически.
"""
from __future__ import annotations

from typing import Self, override


class BaseBy(tuple[str, str]):
    """Неизменяемая `(стратегия, value)`-пара, общая база платформенных `By`."""

    __slots__ = ()

    def __new__(cls, by: str, value: str) -> Self:
        return super().__new__(cls, (by, value))

    @property
    def by(self) -> str:
        return self[0]

    @property
    def value(self) -> str:
        return self[1]

    def _replace(self, *, value: str) -> Self:
        """Копия с другим `value`, того же конкретного типа (сохраняет подкласс).
        Имя - как у `NamedTuple._replace`, для взаимозаменяемости в коде,
        ожидавшем кортеж (напр. `FormattableElement`)."""
        return type(self)(self[0], value)

    @override
    def __str__(self) -> str:
        return f"{self[0]}={self[1]}"

    @override
    def __repr__(self) -> str:
        return f"{type(self).__name__}(by={self[0]!r}, value={self[1]!r})"

    @classmethod
    def id(cls, value: str) -> Self:
        return cls("id", value)

    @classmethod
    def xpath(cls, value: str) -> Self:
        return cls("xpath", value)

    @classmethod
    def name(cls, value: str) -> Self:
        return cls("name", value)

    @classmethod
    def class_name(cls, value: str) -> Self:
        return cls("class name", value)

    @classmethod
    def tag_name(cls, value: str) -> Self:
        return cls("tag name", value)

    @classmethod
    def css_selector(cls, value: str) -> Self:
        return cls("css selector", value)

    @classmethod
    def link_text(cls, value: str) -> Self:
        return cls("link text", value)

    @classmethod
    def partial_link_text(cls, value: str) -> Self:
        return cls("partial link text", value)


__all__ = ["BaseBy"]
