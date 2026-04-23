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


class BaseConfig(BaseSettings):
    """Драйвер-независимая конфигурация.

    Наследуйтесь от этого класса для добавления полей, специфичных для
    драйвера. Порядок разрешения настроек (аргументы конструктора > env vars >
    .env > config.json подпроекта > config.json workspace > значения по
    умолчанию) сохраняется автоматически.
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

        subproject_config = Path.cwd() / CONFIG_FILENAME
        project_root = _find_project_root()
        project_config = project_root / CONFIG_FILENAME if project_root else None

        if subproject_config.exists():
            sources.append(
                JsonConfigSettingsSource(settings_cls, json_file=subproject_config)
            )
        if (
            project_config is not None
            and project_config.exists()
            and project_config != subproject_config
        ):
            sources.append(
                JsonConfigSettingsSource(settings_cls, json_file=project_config)
            )

        return tuple(sources)
