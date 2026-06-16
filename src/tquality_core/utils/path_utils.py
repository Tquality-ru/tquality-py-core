"""Файловые хелперы для разрешения конфигов: стартовая директория поиска
и обход дерева вверх до границы проекта."""

from __future__ import annotations

import contextvars
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar


class PathUtils:
    """Обход файлового дерева для разрешения конфигов.

    Стартовая директория поиска хранится в `ContextVar`, поэтому
    переопределение изолировано per-context: каждый поток (`--threadpool`)
    и каждый процесс (`-n` / xdist) видит своё значение, а конкурентные
    сессии не дерутся за общий `os.chdir`. Так per-test пересборка конфигов
    из директории теста делается без смены глобального CWD. По умолчанию
    (`None`) берётся `Path.cwd()`.
    """

    #: Маркеры корня проекта - наличие любого из этих файлов в директории
    #: означает корень проекта (граница обхода `config.json5`-цепочки).
    PROJECT_MARKERS: ClassVar[tuple[str, ...]] = (
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
    )

    #: Маркеры корня workspace - пары `(имя файла, требуемая подстрока в
    #: содержимом | None)`. `None` означает, что достаточно факта наличия
    #: файла. Покрывают uv (`pyproject.toml` с `[tool.uv.workspace]`),
    #: poetry (`pyproject.toml` с `[tool.poetry]`) и conda
    #: (`environment.yml` / `environment.yaml`).
    WORKSPACE_MARKERS: ClassVar[tuple[tuple[str, str | None], ...]] = (
        ("pyproject.toml", "tool.uv.workspace"),
        ("pyproject.toml", "tool.poetry"),
        ("environment.yml", None),
        ("environment.yaml", None),
    )

    _search_dir: contextvars.ContextVar[Path | None] = contextvars.ContextVar(
        "_tquality_config_search_dir",
        default=None,
    )

    @classmethod
    def config_search_dir(cls) -> Path:
        """Текущая стартовая директория поиска (по контексту или CWD)."""
        return cls._search_dir.get() or Path.cwd()

    @classmethod
    def use_config_search_dir(
        cls,
        path: Path | str | None,
    ) -> Callable[[], None]:
        """Сделать `path` стартовой директорией поиска конфигов; вернуть
        callable, восстанавливающий прежнее значение.

        Не контекст-менеджер - для случаев, где `set` и `reset` происходят в
        разных местах (например, pytest `setup`/`teardown`-хуки). Значение
        живёт в `ContextVar`, поэтому изменение видно только в текущем
        контексте. `None` возвращает к CWD.
        """
        resolved = Path(path).resolve() if path is not None else None
        token = cls._search_dir.set(resolved)
        return lambda: cls._search_dir.reset(token)

    @classmethod
    @contextmanager
    def override_config_search_dir(
        cls,
        path: Path | str | None,
    ) -> Iterator[None]:
        """Временно сделать `path` стартовой директорией поиска конфигов.

        Тред-безопасная замена `os.chdir`: значение живёт в `ContextVar`,
        поэтому влияет только на текущий контекст. `None` возвращает к CWD.
        """
        reset = cls.use_config_search_dir(path)
        try:
            yield
        finally:
            reset()

    @staticmethod
    def find_project_root(start: Path | None = None) -> Path | None:
        """Корень проекта - ближайшая вверх директория с любым из
        `PROJECT_MARKERS` (`pyproject.toml` / `setup.py` / `requirements.txt`).
        """
        current = (start or PathUtils.config_search_dir()).resolve()
        for parent in (current, *current.parents):
            if any((parent / marker).exists() for marker in PathUtils.PROJECT_MARKERS):
                return parent
        return None

    @staticmethod
    def find_workspace_root(start: Path | None = None) -> Path | None:
        """Корень workspace - ближайшая вверх директория с одним из
        `WORKSPACE_MARKERS` (uv: `pyproject.toml` с `[tool.uv.workspace]`;
        poetry: `pyproject.toml` с `[tool.poetry]`; conda: `environment.yml`
        / `environment.yaml`).
        """
        current = (start or PathUtils.config_search_dir()).resolve()
        for parent in (current, *current.parents):
            for filename, required in PathUtils.WORKSPACE_MARKERS:
                candidate = parent / filename
                if not candidate.exists():
                    continue
                if required is None or required in candidate.read_text(
                    encoding="utf-8",
                ):
                    return parent
        return None

    @staticmethod
    def resolve_path_chain(
        start: Path,
        filename: str,
        stop: Path | None = None,
    ) -> list[Path]:
        """Собрать `filename` от `start` вверх до границы проекта (включительно).

        Возвращает список путей, упорядоченный от самого специфичного (ближний
        к `start`) до самого общего. Пропускает директории без `filename`.

        Граница обхода `stop` по умолчанию - корень workspace, иначе корень
        проекта, иначе сам `start`; обход никогда не доходит до корня ФС, чтобы
        не подхватывать чужие `config.json5` из домашней директории и выше.
        """
        start = start.resolve()
        if stop is None:
            stop = PathUtils.find_workspace_root(start) or PathUtils.find_project_root(start) or start
        stop = stop.resolve()

        found: list[Path] = []
        current = start
        while True:
            candidate = current / filename
            if candidate.exists():
                found.append(candidate)
            if current == stop or current.parent == current:
                break
            current = current.parent

        return found

    @staticmethod
    def find_upwards(
        start: Path,
        filename: str,
        stop_at: tuple[str, ...] | None = None,
    ) -> Path | None:
        """Найти первый `filename`, поднимаясь от `start` вверх.

        Останавливается на первой директории, где есть один из `stop_at`-
        маркеров (по умолчанию - `PROJECT_MARKERS`, то есть граница проекта).
        Маркер проверяется ПОСЛЕ файла - если файл и маркер в одной директории,
        возвращается файл. Возвращает `None`, если ничего не нашлось.
        """
        markers = stop_at if stop_at is not None else PathUtils.PROJECT_MARKERS
        current = start.resolve()
        for parent in (current, *current.parents):
            candidate = parent / filename
            if candidate.exists():
                return candidate
            if any((parent / marker).exists() for marker in markers):
                return None
        return None
