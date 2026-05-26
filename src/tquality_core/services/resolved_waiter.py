"""Адаптер к `Waiter`, прокидывающий лениво-вычисляемый объект в condition.

`Waiter` опрашивает `Callable[[], Any]` без аргументов. На практике
условия часто работают над driver'ом, browser-сервисом или другим
контекстом. `ResolvedWaiter[T]` принимает резолвер этого контекста
и адаптирует `until(Callable[[T], Any])` → `until(Callable[[], Any])`,
вызывая `condition(resolver())` на каждой итерации.

Резолвер вызывается на КАЖДОМ опросе - это даёт «свежий» контекст
(например, всегда актуальный driver), без stale-проблем между
итерациями polling-цикла.

Используется как `DriverWaiter` в appium- и selenium-фреймворках
(оба - тонкие алиасы поверх `ResolvedWaiter`).
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from tquality_core.services.waiter import Waiter


class ResolvedWaiter[T]:
    def __init__(
        self,
        waiter: Waiter,
        resolver: Callable[[], T],
    ) -> None:
        self._waiter = waiter
        self._resolver = resolver

    def until(
        self,
        condition: Callable[[T], Any],
        *,
        timeout: float | None = None,
        poll_interval: float | None = None,
        raise_on_timeout: bool | type[BaseException] = False,
        message: str = "",
        ignored_exceptions: Iterable[type[BaseException]] | None = None,
    ) -> bool:
        return self._waiter.until(
            lambda: condition(self._resolver()),
            timeout=timeout,
            poll_interval=poll_interval,
            raise_on_timeout=raise_on_timeout,
            message=message,
            ignored_exceptions=ignored_exceptions,
        )


__all__ = ["ResolvedWaiter"]
