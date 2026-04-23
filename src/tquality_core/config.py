"""Базовая конфигурация для проектов автоматизации тестирования.

Расширяйте `BaseConfig` в своем проекте, чтобы добавить поля, специфичные
для драйвера (тип браузера, размер окна и т.д.). Ядро определяет только
поля, универсальные для всех драйверов.
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

CONFIG_FILENAME = "config.json"


def _find_project_root() -> Path | None:
    """Найти корень workspace, поднимаясь по родительским директориям."""
    current = Path.cwd().resolve()
    for parent in (current, *current.parents):
        pyproject = parent / "pyproject.toml"
        if pyproject.exists() and "tool.uv.workspace" in pyproject.read_text():
            return parent
    return None


def _collect_config_chain(start: Path, stop: Path | None) -> list[Path]:
    """Собрать `config.json` от start к stop (включительно).

    Возвращает список путей, упорядоченный от самого специфичного (ближнего к
    start) до самого общего (в stop). Пропускает директории без config.json.
    Останавливается при достижении stop или корня файловой системы.
    """
    found: list[Path] = []
    current = start.resolve()
    stop_resolved = stop.resolve() if stop is not None else None

    while True:
        candidate = current / CONFIG_FILENAME
        if candidate.exists():
            found.append(candidate)
        if stop_resolved is not None and current == stop_resolved:
            break
        if current.parent == current:
            break
        current = current.parent

    return found


class BaseConfig(BaseSettings):
    """Драйвер-независимая конфигурация.

    Наследуйтесь от этого класса для добавления полей, специфичных для
    драйвера.

    ### Порядок разрешения настроек (от высшего приоритета к низшему)

    1. Аргументы конструктора
    2. Переменные окружения (префикс `TEST_`)
    3. Файл `.env`
    4. Цепочка `config.json` от текущей директории вверх до корня workspace.
       Более специфичный (ближний к cwd) побеждает менее специфичный.
       Например, при запуске из `tests/integration/critical/` приоритет:
       `critical/config.json` > `integration/config.json` > `tests/config.json`
       > `config.json` в корне workspace.
    5. Значения по умолчанию.
    """

    model_config = SettingsConfigDict(
        env_prefix="TEST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = "http://localhost"
    default_timeout: float = 10.0
    log_dir: str = "logs"
    highlight_elements: bool = False

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        sources: list[PydanticBaseSettingsSource] = [
            init_settings, env_settings, dotenv_settings,
        ]

        project_root = _find_project_root()
        config_chain = _collect_config_chain(Path.cwd(), project_root)

        # Цепочка упорядочена от специфичного к общему.
        # pydantic-settings отдает приоритет источникам, идущим раньше,
        # поэтому порядок сохраняется как есть.
        for config_path in config_chain:
            sources.append(
                JsonConfigSettingsSource(settings_cls, json_file=config_path)
            )

        return tuple(sources)
