"""Test logger with allure step integration.

Each test gets its own log file named by pytest node ID. The `step` decorator
and context manager wrap actions with allure reporting. CRITICAL level steps
capture a screenshot at the end (success or failure) via a pluggable hook.
"""
from __future__ import annotations

import enum
import functools
import hashlib
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Protocol, TYPE_CHECKING

import allure

if TYPE_CHECKING:
    from tquality_core.config import BaseConfig

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
_LOG_DATEFMT = "%H:%M:%S"


class LogLevel(enum.Enum):
    NORMAL = "normal"
    CRITICAL = "critical"


class ScreenshotProvider(Protocol):
    """Interface for driver-specific screenshot providers.

    Implementations (Selenium, Appium, WinAppDriver) should register an instance
    via `set_screenshot_provider`. CRITICAL steps call `capture()` to attach a
    screenshot to the allure report.
    """

    def is_available(self) -> bool:
        """Return True if a driver session is currently active."""
        ...

    def capture(self) -> bytes:
        """Return the current screen as PNG bytes."""
        ...


_screenshot_provider: Optional[ScreenshotProvider] = None


def set_screenshot_provider(provider: ScreenshotProvider | None) -> None:
    """Register a driver-specific screenshot provider.

    Pass None to unregister (e.g., after driver teardown).
    """
    global _screenshot_provider
    _screenshot_provider = provider


def _attach_screenshot(label: str) -> None:
    try:
        if _screenshot_provider is None or not _screenshot_provider.is_available():
            logging.getLogger(__name__).warning(
                "Screenshot attempt without an active driver session"
            )
            return
        screenshot = _screenshot_provider.capture()
        allure.attach(
            screenshot,
            name=label,
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:
        pass


class _Step:
    def __init__(
        self, logger: Logger, title: str, level: LogLevel = LogLevel.NORMAL,
    ) -> None:
        self._logger = logger
        self._title = title
        self._level = level
        self._allure_step = allure.step(title)

    def __enter__(self):
        self._logger.info("Step: %s", self._title)
        self._allure_step.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self._level == LogLevel.CRITICAL:
                failed = exc_type is not None
                label = (
                    f"Screenshot [FAIL]: {self._title}"
                    if failed
                    else f"Screenshot: {self._title}"
                )
                _attach_screenshot(label)
        finally:
            self._allure_step.__exit__(exc_type, exc_val, exc_tb)
            status = "FAILED" if exc_type else "completed"
            self._logger.info("Step %s: %s", status, self._title)
        return False

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


def _get_test_node_id() -> str:
    current = os.environ.get("PYTEST_CURRENT_TEST", "")
    if not current:
        return "unknown"
    node_id = re.sub(r"\s+\(.*\)$", "", current)
    ascii_part = re.sub(r"[^a-zA-Z0-9_\-]", "_", node_id)
    ascii_part = re.sub(r"_+", "_", ascii_part).strip("_")
    node_hash = hashlib.md5(node_id.encode()).hexdigest()[:8]
    return f"{ascii_part[:80]}_{node_hash}"


class Logger:
    """Per-test-context logger with a dedicated file handler.

    Each instance creates a uniquely named log file from the current pytest node
    ID. Use `step()` to wrap actions with allure and log markers.
    """

    def __init__(self, config: BaseConfig) -> None:
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

        self._logger.info("Log started: %s", log_file)

    def info(self, msg: str, *args) -> None:
        self._logger.info(msg, *args)

    def warning(self, msg: str, *args) -> None:
        self._logger.warning(msg, *args)

    def error(self, msg: str, *args) -> None:
        self._logger.error(msg, *args)

    def debug(self, msg: str, *args) -> None:
        self._logger.debug(msg, *args)

    def step(self, title: str, level: LogLevel = LogLevel.NORMAL) -> _Step:
        return _Step(self, title, level=level)


_logger_resolver: Optional[Callable[[], Logger]] = None


def set_logger_resolver(resolver: Callable[[], Logger] | None) -> None:
    """Register how to obtain the active Logger from anywhere.

    Typically bound to a DI container provider (e.g., `Container.logger`).
    """
    global _logger_resolver
    _logger_resolver = resolver


def step(title: str, level: LogLevel = LogLevel.NORMAL) -> _Step:
    """Module-level step factory that delegates to the registered Logger."""
    if _logger_resolver is None:
        raise RuntimeError(
            "No logger resolver registered. Call set_logger_resolver() during setup."
        )
    return _logger_resolver().step(title, level=level)
