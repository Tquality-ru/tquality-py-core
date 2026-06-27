"""Тесты генерации JSON-схемы конфига."""
# ruff: noqa - тестовый файл, длинные строки OK
from __future__ import annotations

import json
from pathlib import Path

from tquality_core.models import BaseConfig
from tquality_core.schema import generate_schema


def test_committed_schema_matches_base_config() -> None:
    """Коммиченная схема должна совпадать со схемой, генерируемой из BaseConfig.

    Если тест упал - запустите `tquality-config schema` и закоммитьте
    обновленный schema/config.schema.json.
    """
    repo_root = Path(__file__).resolve().parent.parent
    committed = json.loads(
        (repo_root / "schema" / "config.schema.json").read_text(encoding="utf-8")
    )
    current = generate_schema()

    assert committed == current, (
        "Коммиченная схема устарела. Запустите `tquality-config schema`."
    )


def test_schema_url_resolves_to_master_on_dev_install() -> None:
    """Dev-версия (с '+g...' или '.dev') резолвится в @master."""
    from tquality_core.schema import _resolve_ref
    import tquality_core.schema as schema_mod

    def _stub_version(distribution_name: str) -> str:
        return "0.1.3+gabc123.d20260424"

    original = schema_mod.importlib.metadata.version  # type: ignore[attr-defined]
    schema_mod.importlib.metadata.version = _stub_version  # type: ignore[attr-defined]  # ty:ignore[invalid-assignment]
    try:
        assert _resolve_ref() == "master"
    finally:
        schema_mod.importlib.metadata.version = original  # type: ignore[attr-defined]


def test_schema_url_resolves_to_version_on_release_install() -> None:
    """Чистая релизная версия резолвится в @vX.Y.Z."""
    from tquality_core.schema import _resolve_ref
    import tquality_core.schema as schema_mod

    def _stub_version(distribution_name: str) -> str:
        return "0.1.3"

    original = schema_mod.importlib.metadata.version  # type: ignore[attr-defined]
    schema_mod.importlib.metadata.version = _stub_version  # type: ignore[attr-defined]  # ty:ignore[invalid-assignment]
    try:
        assert _resolve_ref() == "v0.1.3"
    finally:
        schema_mod.importlib.metadata.version = original  # type: ignore[attr-defined]


def test_schema_for_subclass_includes_new_fields() -> None:
    class MyConfig(BaseConfig):
        extra_field: str = "default-value"

    schema = generate_schema(MyConfig)
    assert "extra_field" in schema["properties"]
    assert "base_url" in schema["properties"]
