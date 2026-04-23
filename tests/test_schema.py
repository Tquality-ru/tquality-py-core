"""Тесты генерации JSON-схемы конфига."""
from __future__ import annotations

import json
from pathlib import Path

from tquality_core.config import BaseConfig
from tquality_core.schema import SCHEMA_URL, generate_schema


def test_generated_schema_contains_all_fields() -> None:
    schema = generate_schema()

    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema["$id"] == SCHEMA_URL
    assert set(schema["properties"].keys()) == {
        "base_url", "default_timeout", "log_dir", "highlight_elements",
    }


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


def test_schema_for_subclass_includes_new_fields() -> None:
    class MyConfig(BaseConfig):
        extra_field: str = "default-value"

    schema = generate_schema(MyConfig)
    assert "extra_field" in schema["properties"]
    assert "base_url" in schema["properties"]
