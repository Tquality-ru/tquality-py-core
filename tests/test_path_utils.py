"""Тесты PathUtils.find_upwards и границ обхода."""

from __future__ import annotations

from pathlib import Path

from tquality_core import PathUtils


def test_find_upwards_returns_first_match(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    target = tmp_path / "a" / "caps.json5"
    target.write_text("{}", encoding="utf-8")

    assert PathUtils.find_upwards(sub, "caps.json5") == target


def test_find_upwards_stops_at_project_marker(tmp_path: Path) -> None:
    """Файл выше границы проекта не находится."""
    (tmp_path / "caps.json5").write_text("{}", encoding="utf-8")  # выше границы
    project = tmp_path / "proj"
    project.mkdir()
    (project / "requirements.txt").write_text("", encoding="utf-8")  # маркер
    sub = project / "tests"
    sub.mkdir()

    assert PathUtils.find_upwards(sub, "caps.json5") is None


def test_find_upwards_custom_stop_at(tmp_path: Path) -> None:
    (tmp_path / "caps.json5").write_text("{}", encoding="utf-8")
    project = tmp_path / "proj"
    project.mkdir()
    (project / "requirements.txt").write_text("", encoding="utf-8")
    sub = project / "tests"
    sub.mkdir()

    # requirements.txt больше не граница - поиск доходит до tmp_path/caps.json5.
    found = PathUtils.find_upwards(sub, "caps.json5", stop_at=(".git",))
    assert found == tmp_path / "caps.json5"


def test_find_upwards_marker_and_file_same_dir_returns_file(tmp_path: Path) -> None:
    """Файл проверяется ДО маркера - в одной директории побеждает файл."""
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    target = tmp_path / "caps.json5"
    target.write_text("{}", encoding="utf-8")

    assert PathUtils.find_upwards(tmp_path, "caps.json5") == target
