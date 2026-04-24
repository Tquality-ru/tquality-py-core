"""Генерация JSON-схемы для конфигурации.

`SCHEMA_URL` вычисляется по установленной версии пакета:

- Релизная версия (например, `0.1.3`) → `@v0.1.3` - пин на тег.
- Dev/editable сборка (версия содержит `+g...` или `.dev`) → `@master`.

Это значит: `tquality-config init`, выполненный на релизной установке,
запекает в config.json5 ссылку на конкретный тег. В dev-окружении -
ссылка на master, чтобы отслеживать текущую разработку.
"""
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

from tquality_core.config import BaseConfig

_REPO_BASE = "https://cdn.jsdelivr.net/gh/Tquality-ru/tquality-py-core"
_SCHEMA_PATH = "schema/config.schema.json"
_PACKAGE_NAME = "tquality-py-core"


def _resolve_ref() -> str:
    """Вернуть git-ref для URL схемы.

    Чистый релиз ("0.1.3") → "v0.1.3". Dev ("0.1.3+g...", "0.0+g...",
    "0.1.3.dev1") → "master". Пакет не установлен → "master".
    """
    try:
        version = importlib.metadata.version(_PACKAGE_NAME)
    except importlib.metadata.PackageNotFoundError:
        return "master"
    if "+" in version or ".dev" in version:
        return "master"
    return f"v{version}"


SCHEMA_URL = f"{_REPO_BASE}@{_resolve_ref()}/{_SCHEMA_PATH}"


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
