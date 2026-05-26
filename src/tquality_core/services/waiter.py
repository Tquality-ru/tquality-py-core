"""Платформо-агностичный explicit-waiter с собственным polling-циклом.

Не знает ни о driver'е, ни о selenium - принимает условие без аргументов
(`Callable[[], Any]`) и опрашивает его до truthy либо до таймаута.
Прокидывание driver'а в условие - забота надстройки уровня платформы
(см. `DriverWaiter` в tquality-py-appium / tquality-py-selenium).

По умолчанию `until()` НЕ кидает исключение на таймаут - возвращает
`bool`. Для жёсткого падения - `raise_on_timeout=True` (поднимется
`default_raise_cls`, заданный при создании waiter'а) либо передайте
собственный класс (`raise_on_timeout=MyError`).

Гасятся только те исключения, что переданы в `ignored_exceptions`
(в init либо per-call). Остальные пробрасываются - пользовательский
код видит реальные ошибки, а не молчаливые таймауты.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from tquality_core.config import BaseConfig
    from tquality_core.services.logger import Logger


class WaitTimeoutError(TimeoutError):
    """Поднимается `Waiter.until(raise_on_timeout=True)`, если конкретный
    класс исключения не задан ни в `default_raise_cls`, ни per-call."""


_DEFAULT_POLL_INTERVAL = 0.5


class Waiter:
    def __init__(
        self,
        config: BaseConfig,
        *,
        logger_resolver: Callable[[], "Logger"],
        ignored_exceptions: Iterable[type[BaseException]] = (),
        default_raise_cls: type[BaseException] = WaitTimeoutError,
    ) -> None:
        self._config = config
        self._logger_resolver = logger_resolver
        self._ignored = tuple(ignored_exceptions)
        self._default_raise_cls = default_raise_cls

    @property
    def _log(self) -> Any:
        return self._logger_resolver()

    def until(
        self,
        condition: Callable[[], Any],
        *,
        timeout: float | None = None,
        poll_interval: float | None = None,
        raise_on_timeout: bool | type[BaseException] = False,
        message: str = "",
        ignored_exceptions: Iterable[type[BaseException]] | None = None,
    ) -> bool:
        """Опрашивать `condition()` пока truthy либо не истечёт `timeout`.

        - `timeout` (сек) - default из `config.default_timeout`.
        - `poll_interval` (сек) - пауза между опросами; default - 0.5s.
        - `raise_on_timeout`:
          - `False` (default) - вернуть `False` на таймаут.
          - `True` - поднять `default_raise_cls` (задан в init).
          - `<ExcCls>` - поднять `ExcCls(message)`.
        - `message` - кладётся в лог и в текст исключения.
        - `ignored_exceptions` - типы, считающиеся «ещё не готово»;
          по умолчанию - те, что переданы в init. Остальные пробрасываются.
        """
        t = timeout if timeout is not None else self._config.default_timeout
        poll = poll_interval if poll_interval is not None else _DEFAULT_POLL_INTERVAL
        ignored = tuple(ignored_exceptions) if ignored_exceptions is not None else self._ignored
        log_msg = message or "condition"
        self._log.info("Waiting (%.1fs): %s", t, log_msg)

        deadline = time.monotonic() + t
        last_ignored: BaseException | None = None
        while True:
            try:
                value = condition()
            except ignored as exc:
                value = None
                last_ignored = exc
            if value:
                self._log.info("Wait satisfied: %s", log_msg)
                return True
            now = time.monotonic()
            if now >= deadline:
                self._log.info("Wait timed out: %s", log_msg)
                if raise_on_timeout:
                    exc_cls = (
                        raise_on_timeout
                        if isinstance(raise_on_timeout, type)
                        else self._default_raise_cls
                    )
                    raise exc_cls(log_msg) from last_ignored
                return False
            time.sleep(min(poll, max(0.0, deadline - now)))


__all__ = ["Waiter", "WaitTimeoutError"]
