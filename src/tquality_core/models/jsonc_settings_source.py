"""Источник настроек pydantic-settings, читающий jsonc/json5.

Публичный - дочерние пакеты (`tquality-py-selenium`, `tquality-py-appium`)
переиспользуют его в `settings_customise_sources` своих `*Config`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import json5
from pydantic_settings import JsonConfigSettingsSource


class JsoncConfigSettingsSource(JsonConfigSettingsSource):
    """Как `JsonConfigSettingsSource`, но парсит jsonc/json5.

    Позволяет пользователю оставлять в `config.json5` комментарии
    (`//`, `/* */`) и висячие запятые - полезно, чтобы рядом с настройкой
    описать, зачем она такая.
    """

    def _read_file(self, file_path: Path) -> dict[str, Any]:
        with file_path.open(encoding=self.json_file_encoding) as f:
            data = json5.load(f)
        if not isinstance(data, dict):
            raise ValueError(
                f"{file_path}: ожидается JSON-объект на верхнем уровне",
            )
        return data
