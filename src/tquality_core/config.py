"""Base configuration for test automation projects.

Extend `BaseConfig` in your project to add driver-specific fields (browser type,
window size, etc.). The core only defines fields that are universal across drivers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple, Type

from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

CONFIG_FILENAME = "config.json"


def _find_project_root() -> Path | None:
    current = Path.cwd().resolve()
    for parent in (current, *current.parents):
        pyproject = parent / "pyproject.toml"
        if pyproject.exists() and "tool.uv.workspace" in pyproject.read_text():
            return parent
    return None


class BaseConfig(BaseSettings):
    """Driver-agnostic configuration.

    Subclass this to add driver-specific fields. The settings resolution order
    (init args > env vars > .env > subproject config.json > workspace config.json >
    defaults) is preserved automatically.
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
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        sources = [init_settings, env_settings, dotenv_settings]

        subproject_config = Path.cwd() / CONFIG_FILENAME
        project_root = _find_project_root()
        project_config = project_root / CONFIG_FILENAME if project_root else None

        if subproject_config.exists():
            sources.append(
                JsonConfigSettingsSource(settings_cls, json_file=subproject_config)
            )
        if project_config and project_config.exists() and project_config != subproject_config:
            sources.append(
                JsonConfigSettingsSource(settings_cls, json_file=project_config)
            )

        return tuple(sources)
