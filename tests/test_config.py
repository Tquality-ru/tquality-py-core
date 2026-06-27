"""Тесты для BaseConfig."""
from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from tquality_core import BaseConfig, PathUtils

SearchDir = Callable[[Path], None]


@pytest.fixture
def search_dir() -> Iterator[SearchDir]:
    """Параллельно-безопасно нацеливает разрешение конфигов на директорию
    (через `ContextVar`), в отличие от глобального `monkeypatch`/`chdir`."""
    resets: list[Callable[[], None]] = []

    def _set(path: Path) -> None:
        resets.append(PathUtils.use_config_search_dir(path))

    yield _set
    for reset in reversed(resets):
        reset()


def test_defaults(tmp_path: Path, search_dir: SearchDir) -> None:
    search_dir(tmp_path)
    cfg = BaseConfig()
    assert cfg.base_url == "http://localhost"
    assert cfg.waiter.timeout == 10.0
    assert cfg.waiter.poll_interval == 0.5
    assert cfg.log_dir == "logs"
    assert cfg.highlight_elements is False


def test_constructor_overrides_defaults(
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    search_dir(tmp_path)
    cfg = BaseConfig(base_url="https://example.com", waiter={"timeout": 5.0})  # ty:ignore[invalid-argument-type]
    assert cfg.base_url == "https://example.com"
    assert cfg.waiter.timeout == 5.0


def test_subclass_adds_fields(
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    search_dir(tmp_path)

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
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json5", {"base_url": "https://root"})
    sub = tmp_path / "tests"
    sub.mkdir()
    search_dir(sub)

    cfg = BaseConfig()

    assert cfg.base_url == "https://root"


def test_more_specific_config_wins_over_less_specific(
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json5", {
        "base_url": "https://root",
        "waiter": {"timeout": 10.0},
    })
    sub = tmp_path / "tests" / "integration"
    _write_config(sub / "config.json5", {"base_url": "https://integration"})
    search_dir(sub)

    cfg = BaseConfig()

    # Специфичный config переопределяет base_url
    assert cfg.base_url == "https://integration"
    # waiter.timeout берется из root config, т.к. не определен в integration
    assert cfg.waiter.timeout == 10.0


def test_three_level_chain_resolves_each_field_from_closest_config(
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json5", {
        "base_url": "https://root",
        "waiter": {"timeout": 10.0, "poll_interval": 0.3},
        "log_dir": "root-logs",
    })
    _write_config(tmp_path / "tests" / "config.json5", {
        "waiter": {"timeout": 20.0},
        "log_dir": "tests-logs",
    })
    leaf = tmp_path / "tests" / "integration" / "critical"
    _write_config(leaf / "config.json5", {"log_dir": "critical-logs"})
    search_dir(leaf)

    cfg = BaseConfig()

    assert cfg.base_url == "https://root"        # только root определяет
    # Вложенный waiter мёржится поля-в-поле через цепочку:
    assert cfg.waiter.timeout == 20.0            # tests переопределяет root
    assert cfg.waiter.poll_interval == 0.3       # не задан в tests - берётся из root
    assert cfg.log_dir == "critical-logs"        # critical переопределяет всё


def test_env_vars_override_config_files(
    tmp_path: Path, search_dir: SearchDir, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json5", {"base_url": "https://root"})
    search_dir(tmp_path)
    monkeypatch.setenv("TEST_BASE_URL", "https://from-env")

    cfg = BaseConfig()

    assert cfg.base_url == "https://from-env"


def test_constructor_args_override_everything(
    tmp_path: Path, search_dir: SearchDir, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_workspace(tmp_path)
    _write_config(tmp_path / "config.json5", {"base_url": "https://root"})
    search_dir(tmp_path)
    monkeypatch.setenv("TEST_BASE_URL", "https://from-env")

    cfg = BaseConfig(base_url="https://explicit")

    assert cfg.base_url == "https://explicit"


def test_jsonc_comments_and_trailing_commas_supported(
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    """config.json5 может содержать комментарии и висячие запятые (jsonc/json5)."""
    _make_workspace(tmp_path)
    (tmp_path / "config.json5").write_text(
        """
        {
            // Главная причина выбора: тестовая окружающая среда.
            "base_url": "https://staging.example.com",
            "waiter": {
                /* Таймаут увеличен, потому что БД на staging медленнее prod */
                "timeout": 25.0,
            },
        }
        """,
        encoding="utf-8",
    )
    search_dir(tmp_path)

    cfg = BaseConfig()

    assert cfg.base_url == "https://staging.example.com"
    assert cfg.waiter.timeout == 25.0


def test_chain_stops_at_workspace_root(
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    """config.json5 выше workspace root не должен читаться."""
    outer = tmp_path / "outer"
    outer.mkdir()
    _write_config(outer / "config.json5", {"base_url": "https://should-not-be-read"})

    workspace = outer / "workspace"
    workspace.mkdir()
    _make_workspace(workspace)
    _write_config(workspace / "config.json5", {"base_url": "https://workspace"})

    search_dir(workspace)
    cfg = BaseConfig()

    assert cfg.base_url == "https://workspace"


def test_conda_environment_marks_workspace_root(
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    """`environment.yml` (conda) - тоже маркер корня workspace: config выше
    него не читается, config в корне - читается."""
    outer = tmp_path / "outer"
    outer.mkdir()
    _write_config(outer / "config.json5", {"base_url": "https://should-not-be-read"})

    workspace = outer / "workspace"
    workspace.mkdir()
    (workspace / "environment.yml").write_text(
        "name: demo\ndependencies:\n  - python\n", encoding="utf-8",
    )
    _write_config(workspace / "config.json5", {"base_url": "https://conda-root"})
    leaf = workspace / "tests" / "e2e"
    _write_config(leaf / "config.json5", {"highlight_elements": True})
    search_dir(leaf)

    cfg = BaseConfig()

    assert cfg.base_url == "https://conda-root"   # из корня conda-workspace
    assert cfg.highlight_elements is True         # из leaf
    # config над workspace не подхвачен.


def test_poetry_pyproject_marks_workspace_root(
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    """`pyproject.toml` с `[tool.poetry]` - маркер корня workspace."""
    outer = tmp_path / "outer"
    outer.mkdir()
    _write_config(outer / "config.json5", {"base_url": "https://should-not-be-read"})

    workspace = outer / "workspace"
    workspace.mkdir()
    (workspace / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "demo"\n', encoding="utf-8",
    )
    _write_config(workspace / "config.json5", {"base_url": "https://poetry-root"})
    leaf = workspace / "tests"
    _write_config(leaf / "config.json5", {"highlight_elements": True})
    search_dir(leaf)

    cfg = BaseConfig()

    assert cfg.base_url == "https://poetry-root"
    assert cfg.highlight_elements is True


def test_chain_stops_at_project_root_without_workspace(
    tmp_path: Path, search_dir: SearchDir,
) -> None:
    """Без uv-workspace цепочка стопает на корне проекта (`pyproject.toml`),
    а не уходит до корня ФС - config.json5 выше проекта не читается."""
    outer = tmp_path / "outer"
    outer.mkdir()
    _write_config(outer / "config.json5", {"base_url": "https://should-not-be-read"})

    # Обычный проект без [tool.uv.workspace], помеченный requirements.txt -
    # один из PathUtils.PROJECT_MARKERS (не pyproject.toml).
    project = outer / "project"
    project.mkdir()
    (project / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    _write_config(project / "config.json5", {"base_url": "https://project"})
    sub = project / "tests"
    sub.mkdir()
    search_dir(sub)

    cfg = BaseConfig()

    assert cfg.base_url == "https://project"


def test_override_config_search_dir_redirects_resolution(tmp_path: Path) -> None:
    """`PathUtils.override_config_search_dir` смещает поиск конфигов на
    указанную директорию (без chdir)."""
    _make_workspace(tmp_path)
    leaf = tmp_path / "tests" / "android"
    _write_config(leaf / "config.json5", {"base_url": "https://android"})
    empty = tmp_path / "tests" / "ios"  # без своего config.json5
    empty.mkdir(parents=True)

    with PathUtils.override_config_search_dir(leaf):
        assert BaseConfig().base_url == "https://android"
    # Другая директория без config.json5 в цепочке - дефолт.
    with PathUtils.override_config_search_dir(empty):
        assert BaseConfig().base_url == "http://localhost"
