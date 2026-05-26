"""`ElementState` - предусловие перед любым действием над элементом
(click / type / text / ...).

Семантика одинаковая для обеих платформ: appium-WebDriver и
selenium-WebDriver. Сам класс хранит только enum/предикат-типы;
конкретная мапа `state → wait.until_*` живёт в платформенном
`BaseElement._await_state(...)` (он знает, какой `ElementWaiter`
использовать).

Default'ы:
- `BaseElement`, `Label`, `Input` - `DISPLAYED`
- `Button`, `CheckBox` - `CLICKABLE`

Когда стандартного поведения не хватает:

```python
# Поле с невменяемыми bounds: is_displayed() == False, но send_keys
# работает - отключаем все проверки.
phone = element_factory.input(..., state=ElementState.EXISTS_IN_ANY_STATE)

# Своё условие: ждём пока в тексте появится подстрока.
def has_loaded(el) -> bool:
    return "Готово" in el.text

submit = element_factory.button(..., state=has_loaded)
```
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Union


class ElementState(Enum):
    """Предусловие для взаимодействия с элементом."""

    DISPLAYED = "displayed"
    """Ждать `wait.until_visible()` (`is_displayed() == True`)."""

    CLICKABLE = "clickable"
    """Ждать `wait.until_clickable()` (visible + enabled)."""

    EXISTS_IN_ANY_STATE = "exists_in_any_state"
    """Не проверять состояние - сразу `_find()` и действие. Полезно для
    элементов, которые не соответствуют стандартам видимости/кликабельности
    (нестандартные bounds, overlay'и, кастомные web-компоненты), но при
    этом штатно принимают ввод/клик."""


StatePredicate = Callable[[Any], bool]
"""Произвольное предусловие. Принимает сам элемент (типизация на стороне
конкретного `ElementWaiter`); возвращает bool. Опрашивается через
стандартный `Waiter`-таймаут."""


StateSpec = Union[ElementState, StatePredicate]
"""Допустимые значения параметра `state` у элемента и фабрики."""


__all__ = ["ElementState", "StatePredicate", "StateSpec"]
