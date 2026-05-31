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


StepEnterHook = Callable[["Step"], None]
StepExitHook = Callable[
    ["Step", type[BaseException] | None, BaseException | None], None,
]


class Step:
    """Шаг - контекстный менеджер и декоратор. Передается в step-хуки и
    доступен через `Logger.current_step` / `active_step_stack`, поэтому
    `title` / `level` - публичные."""

    def __init__(
        self, logger: Logger, title: str, level: LogLevel = LogLevel.NORMAL,
    ) -> None:
        self._logger = logger
        self._title = title
        self._level = level
        self._allure_step = allure.step(title)

    @property
    def title(self) -> str:
        return self._title

    @property
    def level(self) -> LogLevel:
        return self._level

    def __enter__(self) -> Step:
        self._logger.info("Шаг: %s", self._title)
        self._allure_step.__enter__()  # type: ignore[no-untyped-call]
        self._logger._step_stack += (self,)
        for hook in self._logger._enter_hooks:
            try:
                hook(self)
            except Exception as exc:  # noqa: BLE001
                self._logger.warning(
                    "Step enter hook %r упал: %s", hook, exc,
                )
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
            for hook in self._logger._exit_hooks:
                try:
                    hook(self, exc_type, exc_val)
                except Exception as exc:  # noqa: BLE001
                    self._logger.warning(
                        "Step exit hook %r упал: %s", hook, exc,
                    )
        finally:
            stack = self._logger._step_stack
            if stack and stack[-1] is self:
                self._logger._step_stack = stack[:-1]
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

        # Стек активных шагов и хуки на enter/exit - per-Logger,
        # чтобы в параллельных прогонах не путать "innermost step какого
        # из тестов". Каждый тест получает свой Logger, свой стек, свои хуки.
        self._step_stack: tuple[Step, ...] = ()
        self._enter_hooks: list[StepEnterHook] = []
        self._exit_hooks: list[StepExitHook] = []

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

    def step(self, title: str, level: LogLevel = LogLevel.NORMAL) -> Step:
        return Step(self, title, level=level)

    def register_step_enter_hook(
        self, hook: StepEnterHook,
    ) -> Callable[[], None]:
        """Зарегистрировать колбэк, вызываемый при входе в любой шаг.

        Колбэк получает `(step,)`. Хук вызывается уже после push в стек,
        поэтому внутри хука `logger.current_step is step`. Исключения
        логируются как warning, не ломают шаг. Возвращает unregister-callable.
        """
        self._enter_hooks.append(hook)

        def _unregister() -> None:
            try:
                self._enter_hooks.remove(hook)
            except ValueError:
                pass

        return _unregister

    def register_step_exit_hook(
        self, hook: StepExitHook,
    ) -> Callable[[], None]:
        """Зарегистрировать колбэк, вызываемый при выходе из любого шага.

        Колбэк получает `(step, exc_type, exc_val)` - может судить по
        `exc_type`, упал ли шаг, и читать `step.title` / `step.level`.
        Хук вызывается до pop из стека (`logger.current_step is step` внутри).
        Исключения логируются как warning, не ломают шаг. Возвращает
        unregister-callable.
        """
        self._exit_hooks.append(hook)

        def _unregister() -> None:
            try:
                self._exit_hooks.remove(hook)
            except ValueError:
                pass

        return _unregister

    @property
    def current_step(self) -> Step | None:
        """Innermost активный шаг (вершина стека) или None если нет активных."""
        return self._step_stack[-1] if self._step_stack else None

    @property
    def active_step_stack(self) -> tuple[Step, ...]:
        """Снимок стека активных шагов от outermost к innermost."""
        return self._step_stack


_logger_resolver: Callable[[], Logger] | None = None


def set_logger_resolver(resolver: Callable[[], Logger] | None) -> None:
    """Зарегистрировать способ получения активного Logger из любого места.

    Обычно связывается с провайдером DI-контейнера (например, `Container.logger`).
    """
    global _logger_resolver
    _logger_resolver = resolver


def step(title: str, level: LogLevel = LogLevel.NORMAL) -> Step:
    """Фабрика шагов уровня модуля, делегирующая зарегистрированному Logger."""
    if _logger_resolver is None:
        raise RuntimeError(
            "Резолвер логгера не зарегистрирован. "
            "Вызовите set_logger_resolver() при настройке."
        )
    return _logger_resolver().step(title, level=level)
