"""Тесты для CLI-команд."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tquality_core.cli import main
from tquality_core.schema import SCHEMA_URL


def test_init_creates_config(tmp_path: Path) -> None:
    exit_code = main(["init", "--path", str(tmp_path)])

    assert exit_code == 0
    config_file = tmp_path / "config.json5"
    assert config_file.exists()

    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert data["$schema"] == SCHEMA_URL
    assert data["base_url"] == "http://localhost"
    assert data["waiter"] == {"timeout": 10.0, "poll_interval": 0.5}
    assert data["log_dir"] == "logs"
    assert data["highlight_elements"] is False


def test_init_refuses_to_overwrite_without_force(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_file = tmp_path / "config.json5"
    config_file.write_text('{"base_url": "https://custom"}', encoding="utf-8")

    exit_code = main(["init", "--path", str(tmp_path)])

    assert exit_code == 1
    assert "уже существует" in capsys.readouterr().err
    assert config_file.read_text(encoding="utf-8") == '{"base_url": "https://custom"}'


def test_init_overwrites_with_force(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json5"
    config_file.write_text('{"base_url": "https://custom"}', encoding="utf-8")

    exit_code = main(["init", "--path", str(tmp_path), "--force"])

    assert exit_code == 0
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert data["base_url"] == "http://localhost"


def test_schema_writes_file(tmp_path: Path) -> None:
    exit_code = main(["schema", "--path", str(tmp_path)])

    assert exit_code == 0
    schema_file = tmp_path / "schema" / "config.schema.json"
    assert schema_file.exists()

    data = json.loads(schema_file.read_text(encoding="utf-8"))
    assert data["$id"] == SCHEMA_URL
    assert "base_url" in data["properties"]
    assert "waiter" in data["properties"]
    assert "WaiterConfig" in data["$defs"]
