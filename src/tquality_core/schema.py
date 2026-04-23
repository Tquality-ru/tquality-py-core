"""Генерация JSON-схемы для конфигурации.

Используется CLI-командой `tquality-config schema` для записи
`schema/config.schema.json` в корень репозитория.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tquality_core.config import BaseConfig

SCHEMA_URL = (
    "https://cdn.jsdelivr.net/gh/Tquality-ru/tquality-py-core@main"
    "/schema/config.schema.json"
)


def generate_schema(config_cls: type[BaseConfig] = BaseConfig) -> dict[str, Any]:
    """Вернуть JSON-схему для переданного класса конфигурации.

    По умолчанию возвращает схему BaseConfig. Проекты могут передать свой
    подкласс для генерации схемы с дополнительными полями.
    """
    schema: dict[str, Any] = config_cls.model_json_schema()
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    schema["$id"] = SCHEMA_URL
    return schema


def write_schema_file(
    path: Path,
    config_cls: type[BaseConfig] = BaseConfig,
) -> None:
    """Записать JSON-схему в файл с отступами и завершающей новой строкой."""
    schema = generate_schema(config_cls)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
