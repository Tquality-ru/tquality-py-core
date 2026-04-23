"""Тесты для BaseConfig."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tquality_core import BaseConfig


def test_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = BaseConfig()
    assert cfg.base_url == "http://localhost"
    assert cfg.default_timeout == 10.0
    assert cfg.log_dir == "logs"
    assert cfg.highlight_elements is False


def test_constructor_overrides_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = BaseConfig(base_url="https://example.com", default_timeout=5.0)
    assert cfg.base_url == "https://example.com"
    assert cfg.default_timeout == 5.0


def test_subclass_adds_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    class MyConfig(BaseConfig):
        custom_field: str = "default-value"

    cfg = MyConfig()
    assert cfg.custom_field == "default-value"
    assert cfg.base_url == "http://localhost"


def _make_workspace(root: Path) -> None:
    """Создать минимальный uv workspace, чтобы _find_project_root его нашел."""
    (root / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = []\n',
        encoding="utf-8",
    )


def _write_config(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_resolves_from_workspace_root_when_cwd_has_no_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json", {"base_url": "https://root"})
    sub = tmp_path / "tests"
    sub.mkdir()
    monkeypatch.chdir(sub)

    cfg = BaseConfig()

    assert cfg.base_url == "https://root"


def test_more_specific_config_wins_over_less_specific(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json", {
        "base_url": "https://root",
        "default_timeout": 10.0,
    })
    sub = tmp_path / "tests" / "integration"
    _write_config(sub / "config.json", {"base_url": "https://integration"})
    monkeypatch.chdir(sub)

    cfg = BaseConfig()

    # Специфичный config переопределяет base_url
    assert cfg.base_url == "https://integration"
    # default_timeout берется из root config, т.к. не определен в integration
    assert cfg.default_timeout == 10.0


def test_three_level_chain_resolves_each_field_from_closest_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json", {
        "base_url": "https://root",
        "default_timeout": 10.0,
        "log_dir": "root-logs",
    })
    _write_config(tmp_path / "tests" / "config.json", {
        "default_timeout": 20.0,
        "log_dir": "tests-logs",
    })
    leaf = tmp_path / "tests" / "integration" / "critical"
    _write_config(leaf / "config.json", {"log_dir": "critical-logs"})
    monkeypatch.chdir(leaf)

    cfg = BaseConfig()

    assert cfg.base_url == "https://root"        # только root определяет
    assert cfg.default_timeout == 20.0           # tests переопределяет root
    assert cfg.log_dir == "critical-logs"        # critical переопределяет всё


def test_env_vars_override_config_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json", {"base_url": "https://root"})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TEST_BASE_URL", "https://from-env")

    cfg = BaseConfig()

    assert cfg.base_url == "https://from-env"


def test_constructor_args_override_everything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json", {"base_url": "https://root"})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TEST_BASE_URL", "https://from-env")

    cfg = BaseConfig(base_url="https://explicit")

    assert cfg.base_url == "https://explicit"


def test_chain_stops_at_workspace_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """config.json выше workspace root не должен читаться."""
    outer = tmp_path / "outer"
    outer.mkdir()
    _write_config(outer / "config.json", {"base_url": "https://should-not-be-read"})

    workspace = outer / "workspace"
    workspace.mkdir()
    _make_workspace(workspace)
    _write_config(workspace / "config.json", {"base_url": "https://workspace"})

    monkeypatch.chdir(workspace)
    cfg = BaseConfig()

    assert cfg.base_url == "https://workspace"
