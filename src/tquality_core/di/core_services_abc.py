"""Абстрактный корень композиции (`CoreServicesABC`).

Объявляет слот `logger` (заглушка `Provider()`, переопределяется конкретным
контейнером) и берёт на себя одну обязанность: регистрировать каждый
свежеобъявленный конкретный контейнер как активный источник Logger для
standalone-`step` / `Logger.current()`.

Регистрация в `__init_subclass__` (срабатывает и для `CoreServices`, и для
пользовательских подклассов) - «залинкованный последним» контейнер выигрывает.
Резолвер - связанный classmethod `cls._resolve_logger` (а не inline-lambda): он
читает поле `cls.logger` ЛЕНИВО, поэтому переживает перевязку `@copy` (она идёт
уже после создания класса) и остаётся типизированным (без `Any`). `Logger`
хранит обычный `Callable[[], Logger]`, поэтому не знает про контейнеры и не
образует циклический импорт.
"""

from __future__ import annotations

from typing import Any

from static_dependency_injector.containers import StaticDeclarativeContainer
from static_dependency_injector.static_providers import Provider

from tquality_core import Logger


class CoreServicesABC(StaticDeclarativeContainer):
    """База композиции: слот `logger` + авто-регистрация активного источника."""

    logger: Logger = Provider()

    @classmethod
    def _resolve_logger(cls) -> Logger:
        """Текущий Logger активного контейнера (ленивое чтение поля - учитывает `@copy`)."""
        return cls.logger

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Внутренний шов di→services: protected-метод зовём намеренно - это не
        # публичная настройка, а авто-регистрация (см. `Logger._set_resolver`).
        Logger._set_resolver(cls._resolve_logger)
