"""Генерация JSON-схемы для конфигурации.

`SCHEMA_URL` вычисляется по установленной версии пакета `tquality-py-core`:

- Релизная версия (например, `0.1.3`) → `@v0.1.3` - пин на тег.
- Dev/editable сборка (версия содержит `+g...` или `.dev`) → `@master`.

`tquality-config init`, выполненный на релизной установке, запекает в
config.json5 ссылку на конкретный тег. В dev-окружении - ссылка на master.

Хелперы `resolve_ref`, `build_schema_url`, `generate_schema(config_cls,
schema_url=...)`, `write_schema_file(path, config_cls, schema_url=...)`
переиспользуются драйверными пакетами (`tquality-py-selenium`,
`tquality-py-appium`), чтобы не дублировать одну и ту же плиту.
"""
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

from tquality_core.models import BaseConfig

_REPO_BASE_TEMPLATE = "https://cdn.jsdelivr.net/gh/{owner}/{repo}"
_SCHEMA_PATH = "schema/config.schema.json"

_CORE_REPO_OWNER = "Tquality-ru"
_CORE_REPO_NAME = "tquality-py-core"
_CORE_PACKAGE_NAME = "tquality-py-core"


def resolve_ref(package_name: str) -> str:
    """Вернуть git-ref (`master` либо `vX.Y.Z`) для версии пакета.

    Чистый релиз ("0.1.3") → "v0.1.3". Dev ("0.1.3+g...", "0.0+g...",
    "0.1.3.dev1") → "master". Пакет не установлен → "master".
    """
    try:
        version = importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "master"
    if "+" in version or ".dev" in version:
        return "master"
    return f"v{version}"


def build_schema_url(
    *, package_name: str, repo_owner: str, repo_name: str,
) -> str:
    """Собрать публичный URL JSON-схемы для драйверного пакета.

    Используется и `tquality-py-core`, и downstream-пакетами:

    ```python
    SELENIUM_SCHEMA_URL = build_schema_url(
        package_name="tquality-py-selenium",
        repo_owner="Tquality-ru",
        repo_name="tquality-py-selenium",
    )
    ```
    """
    base = _REPO_BASE_TEMPLATE.format(owner=repo_owner, repo=repo_name)
    return f"{base}@{resolve_ref(package_name)}/{_SCHEMA_PATH}"


def _resolve_ref() -> str:
    """Shim обратной совместимости для старых тестов/импортов."""
    return resolve_ref(_CORE_PACKAGE_NAME)


SCHEMA_URL = build_schema_url(
    package_name=_CORE_PACKAGE_NAME,
    repo_owner=_CORE_REPO_OWNER,
    repo_name=_CORE_REPO_NAME,
)


def generate_schema(
    config_cls: type[BaseConfig] = BaseConfig,
    *,
    schema_url: str | None = None,
) -> dict[str, Any]:
    """Вернуть JSON-схему для переданного класса конфигурации.

    По умолчанию использует SCHEMA_URL пакета `tquality-py-core`. Драйверные
    пакеты передают свой `schema_url` (см. `build_schema_url`).
    """
    schema: dict[str, Any] = config_cls.model_json_schema()
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    schema["$id"] = schema_url if schema_url is not None else SCHEMA_URL
    return schema


def write_schema_file(
    path: Path,
    config_cls: type[BaseConfig] = BaseConfig,
    *,
    schema_url: str | None = None,
) -> None:
    """Записать JSON-схему в файл с отступами и завершающей новой строкой."""
    schema = generate_schema(config_cls, schema_url=schema_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
