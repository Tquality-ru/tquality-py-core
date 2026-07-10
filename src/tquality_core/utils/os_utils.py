"""Driver-agnostic проверки текущей платформы.

Тонкая обёртка над `sys.platform`. Конкретные карты поддержки (какие
браузеры под Selenium, какие платформы и драйверы под Appium) живут
в соответствующих пакетах и используют эти проверки.
"""

from __future__ import annotations

import sys


class OSUtils:
    """Stateless-хелперы определения текущей ОС."""

    @staticmethod
    def is_macos() -> bool:
        return sys.platform == "darwin"

    @staticmethod
    def is_windows() -> bool:
        return sys.platform == "win32"

    @staticmethod
    def is_linux() -> bool:
        return sys.platform == "linux"

    @staticmethod
    def current_platform() -> str:
        """Вернуть текущее значение `sys.platform` (`"linux"`, `"darwin"`, `"win32"`)."""
        return sys.platform
