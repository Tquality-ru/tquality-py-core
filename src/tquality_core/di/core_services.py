"""Core-level composition root (`CoreServices`).

Driver-независимый спайн сервисов на `static_dependency_injector`: `config`,
`logger`, `waiter`. Платформенные пакеты (selenium/appium) наследуют
`CoreServices` и добавляют driver-bound сервисы (browser, screenshot/screencast
provider, фабрики элементов, driver-waiter), переопределяя при необходимости
слоты (`config` → `SeleniumConfig`, `logger` → с providers).

Скоупы:
- `config` — `Singleton`: одна конфигурация на контейнер (платформа
  переопределяет тип и/или пересобирает per-test через `set_overrides`).
- `logger` — testlocal (`TestContextSingleton`): свежий per-test экземпляр,
  сбрасывается бандл-плагином `static_dependency_injector` после каждого теста.
- `waiter` — `ContextLocalSingleton`: `logger_resolver=Delegate(logger)`
  передаёт сам ПРОВАЙДЕР `logger` как callable (а не разрешённое значение),
  поэтому `Waiter` лениво тянет текущий Logger из контейнера - в т.ч. свежий
  после per-test сброса. Никакого глобального резолвера/`setup()` не нужно.

Наследование: библиотека не переписывает провайдеры автоматически. Подкласс,
переопределяя `logger`, помечается декоратором `@copy(CoreServices)` - он
перевязывает унаследованный `waiter` на переопределённый `logger` (`Delegate`
начинает указывать на новый провайдер, без ПЕРЕобъявления `waiter`).

Активный Logger для standalone-`step` / `Logger.current()`: авто-регистрация
живёт в `CoreServicesABC` (см. `core_services_abc.py`) - `__init_subclass__`
регистрирует свежеобъявленный контейнер как активный источник, «залинкованный
последним» выигрывает. `CoreServices` наследует это, ничего не делая.
"""

from __future__ import annotations

from static_dependency_injector.static_providers import ContextLocalSingleton, Delegate, Singleton, TestContextSingleton

from tquality_core import BaseConfig, Logger, Waiter
from tquality_core.di.core_services_abc import CoreServicesABC

__all__ = ["CoreServices"]


class CoreServices(CoreServicesABC):
    """Driver-независимый composition root: `config` → `logger` → `waiter`.

    От `CoreServicesABC` наследует авто-регистрацию активного Logger-источника
    (для standalone-`step`). Наследники добавляют driver-bound сервисы и
    переопределяют слоты.
    """

    config: BaseConfig = Singleton(BaseConfig)
    logger: Logger = TestContextSingleton(Logger, config=config)
    waiter: Waiter = ContextLocalSingleton(Waiter, config=config, logger_resolver=Delegate(logger))
