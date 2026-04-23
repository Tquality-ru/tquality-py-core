"""Логгер тестов с интеграцией в allure.

Каждый тест получает свой файл лога, именованный по pytest node ID. Декоратор
и контекстный менеджер `step` оборачивают действия в allure-шаги. Шаги уровня
CRITICAL делают скриншот в конце (успех или сбой) через подключаемый провайдер.
"""
from __future__ import annotations

import enum
import functools
import hashlib
import logging
import os
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Protocol, TYPE_CHECKING

import allure

if TYPE_CHECKING:
    from tquality_core.config import BaseConfig

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
_LOG_DATEFMT = "%H:%M:%S"


class LogLevel(enum.Enum):
    """Уровень важности шага.

    - NORMAL: только лог + allure-шаг.
    - CRITICAL: + скриншот в конце (успех или сбой).
    - WITH_SCREENCAST: + запись экрана в виде GIF на время выполнения шага.
      Требует зарегистрированного `ScreencastProvider` (обычно из selenium).
    """

    NORMAL = "normal"
    CRITICAL = "critical"
    WITH_SCREENCAST = "with-screencast"


class ScreenshotProvider(Protocol):
    """Интерфейс драйвер-специфичного провайдера скриншотов.

    Регистрируется как DI-сервис (`providers.Singleton(...)`) в контейнере
    и инжектится в `Logger.__init__`. CRITICAL-шаги вызывают `capture()` в
    конце (успех или сбой) и прикрепляют PNG к allure-отчету.
    """

    def is_available(self) -> bool:
        """Вернуть True, если сессия драйвера сейчас активна."""
        ...

    def capture(self) -> bytes:
        """Вернуть текущий экран как PNG-байты."""
        ...


class ScreencastProvider(Protocol):
    """Интерфейс провайдера screencast-записи.

    Регистрируется как DI-сервис и инжектится в `Logger.__init__`.
    Шаги уровня `WITH_SCREENCAST` вызывают `start()` на входе и `stop()`
    на выходе; полученный бинарник (GIF/mp4) прикрепляется к allure-шагу.
    """

    def is_available(self) -> bool:
        """Вернуть True, если сессия драйвера сейчас активна."""
        ...

    def start(self) -> None:
        """Начать запись. Должен быть идемпотентным при повторном вызове."""
        ...

    def stop(self) -> bytes | None:
        """Остановить запись и вернуть бинарник или None, если кадров нет."""
        ...

    def mime_type(self) -> str:
        """MIME-тип результата `stop()` - например, 'image/gif' или 'video/mp4'."""
        ...


class _Step:
    """Внутренняя реализация шага, используется как контекстный менеджер и декоратор."""

    def __init__(
        self, logger: Logger, title: str, level: LogLevel = LogLevel.NORMAL,
    ) -> None:
        self._logger = logger
        self._title = title
        self._level = level
        self._allure_step = allure.step(title)

    def __enter__(self) -> _Step:
        self._logger.info("Шаг: %s", self._title)
        self._allure_step.__enter__()  # type: ignore[no-untyped-call]
        if self._level == LogLevel.WITH_SCREENCAST:
            provider = self._logger.screencast_provider
            if provider is None:
                self._logger.warning(
                    "WITH_SCREENCAST: ScreencastProvider не зарегистрирован, пропускаю",
                )
            elif not provider.is_available():
                self._logger.warning(
                    "WITH_SCREENCAST: сессия драйвера неактивна, пропускаю",
                )
            else:
                try:
                    provider.start()
                except Exception:  # noqa: BLE001
                    self._logger.warning(
                        "Не удалось начать screencast: %s",
                        self._title,
                    )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if self._level == LogLevel.CRITICAL:
                self._attach_screenshot(failed=exc_type is not None)
            elif self._level == LogLevel.WITH_SCREENCAST:
                self._attach_screencast()
        finally:
            self._allure_step.__exit__(exc_type, exc_val, exc_tb)  # type: ignore[no-untyped-call]
            status = "СБОЙ" if exc_type else "завершен"
            self._logger.info("Шаг %s: %s", status, self._title)

    def _attach_screenshot(self, *, failed: bool) -> None:
        provider = self._logger.screenshot_provider
        if provider is None:
            self._logger.warning(
                "CRITICAL: ScreenshotProvider не зарегистрирован, пропускаю",
            )
            return
        if not provider.is_available():
            self._logger.warning(
                "CRITICAL: сессия драйвера неактивна, пропускаю скриншот",
            )
            return
        label = (
            f"Скриншот [СБОЙ]: {self._title}"
            if failed else f"Скриншот: {self._title}"
        )
        try:
            png = provider.capture()
        except Exception:  # noqa: BLE001
            self._logger.warning("Не удалось снять скриншот: %s", self._title)
            return
        allure.attach(png, name=label, attachment_type=allure.attachment_type.PNG)

    def _attach_screencast(self) -> None:
        provider = self._logger.screencast_provider
        if provider is None:
            self._logger.warning(
                "WITH_SCREENCAST: ScreencastProvider не зарегистрирован, "
                "пропускаю прикрепление записи",
            )
            return
        try:
            payload = provider.stop()
        except Exception:  # noqa: BLE001
            self._logger.warning(
                "Не удалось остановить screencast: %s", self._title,
            )
            return
        if not payload:
            return
        allure.attach(
            payload,
            name=f"Screencast: {self._title}",
            extension=provider.mime_type().split("/")[-1],
        )

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return func(*args, **kwargs)
        return wrapper


def _get_test_node_id() -> str:
    """Сформировать безопасное для файловой системы имя из pytest node ID.

    ASCII-only, с MD5-хэшем для уникальности при не-ASCII параметрах.
    """
    current = os.environ.get("PYTEST_CURRENT_TEST", "")
    if not current:
        return "unknown"
    node_id = re.sub(r"\s+\(.*\)$", "", current)
    ascii_part = re.sub(r"[^a-zA-Z0-9_\-]", "_", node_id)
    ascii_part = re.sub(r"_+", "_", ascii_part).strip("_")
    node_hash = hashlib.md5(node_id.encode()).hexdigest()[:8]
    return f"{ascii_part[:80]}_{node_hash}"


class Logger:
    """Логгер на один контекст теста с отдельным файловым обработчиком.

    Получает `screenshot_provider` и `screencast_provider` через DI -
    шаги уровня CRITICAL и WITH_SCREENCAST используют их для
    прикрепления артефактов к allure-отчету.
    """

    def __init__(
        self,
        config: BaseConfig,
        screenshot_provider: ScreenshotProvider | None = None,
        screencast_provider: ScreencastProvider | None = None,
    ) -> None:
        self.screenshot_provider = screenshot_provider
        self.screencast_provider = screencast_provider

        self._started_at = datetime.now()
        timestamp = self._started_at.strftime("%Y%m%d_%H%M%S")
        node_id = _get_test_node_id()

        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{timestamp}_{node_id}.log"

        self._logger = logging.getLogger(f"tquality.{timestamp}_{node_id}")
        self._logger.setLevel(logging.INFO)

        formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATEFMT)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self._logger.addHandler(stream_handler)

        self._logger.info("Лог запущен: %s", log_file)

    def info(self, msg: str, *args: Any) -> None:
        self._logger.info(msg, *args)

    def warning(self, msg: str, *args: Any) -> None:
        self._logger.warning(msg, *args)

    def error(self, msg: str, *args: Any) -> None:
        self._logger.error(msg, *args)

    def debug(self, msg: str, *args: Any) -> None:
        self._logger.debug(msg, *args)

    def step(self, title: str, level: LogLevel = LogLevel.NORMAL) -> _Step:
        return _Step(self, title, level=level)


_logger_resolver: Callable[[], Logger] | None = None


def set_logger_resolver(resolver: Callable[[], Logger] | None) -> None:
    """Зарегистрировать способ получения активного Logger из любого места.

    Обычно связывается с провайдером DI-контейнера (например, `Container.logger`).
    """
    global _logger_resolver
    _logger_resolver = resolver


def step(title: str, level: LogLevel = LogLevel.NORMAL) -> _Step:
    """Фабрика шагов уровня модуля, делегирующая зарегистрированному Logger."""
    if _logger_resolver is None:
        raise RuntimeError(
            "Резолвер логгера не зарегистрирован. "
            "Вызовите set_logger_resolver() при настройке."
        )
    return _logger_resolver().step(title, level=level)
