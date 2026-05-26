"""Реализация `ScreenshotProvider` поверх WebDriver-совместимого драйвера.

Любой объект с методом `get_screenshot_as_png() -> bytes` подходит:
selenium-WebDriver, appium-WebDriver, undetected-chromedriver и т.п.
Резолвер драйвера и проверка доступности инжектятся через конструктор -
сам класс не знает о DI-контейнере и о том, откуда берётся сессия.
"""
from __future__ import annotations

from typing import Any, Callable


class WebDriverScreenshotProvider:
    """Реализует `tquality_core.ScreenshotProvider`."""

    def __init__(
        self,
        driver_resolver: Callable[[], Any],
        availability_check: Callable[[], bool],
    ) -> None:
        self._driver_resolver = driver_resolver
        self._is_available = availability_check

    def is_available(self) -> bool:
        return self._is_available()

    def capture(self) -> bytes:
        png: bytes = self._driver_resolver().get_screenshot_as_png()
        return png


__all__ = ["WebDriverScreenshotProvider"]
