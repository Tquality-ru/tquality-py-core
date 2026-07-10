"""Базовая конфигурация для проектов автоматизации тестирования.

Расширяйте `BaseConfig` в своем проекте, чтобы добавить поля, специфичные
для драйвера (тип браузера, размер окна и т.д.). Ядро определяет только
поля, универсальные для всех драйверов.
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar, override

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from tquality_core.models.jsonc_settings_source import JsoncConfigSettingsSource
from tquality_core.utils.path_utils import PathUtils


class LogStream(StrEnum):
    """Куда направлять консольный (stream) обработчик логов теста.

    `stdout` / `stderr` - соответствующий стандартный поток; `none` -
    отключить stream-обработчик вовсе (лог пишется только в файл, если
    тот включён).
    """

    STDOUT = "stdout"
    STDERR = "stderr"
    NONE = "none"


class LogLevelName(StrEnum):
    """Уровень стандартного `logging` для обработчика лога.

    Совпадает с именами уровней `logging`; значение передаётся в
    `Handler.setLevel(...)` как есть.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingConfig(BaseModel):
    """Настройки файлового и консольного обработчиков лога теста.

    Каждый тест получает свой `logging.Logger` (см. `Logger`), к которому
    подключены до двух обработчиков: файловый (пишет `<тест>.log` в
    `log_dir`) и консольный (stdout/stderr). Уровни обработчиков
    независимы - можно слать в консоль только `WARNING+`, а в файл -
    весь `DEBUG`.

    Драйверные пакеты расширяют этот блок дополнительными каналами
    (например, `tquality-py-appium` добавляет `device`/`network`-логи
    устройства), наследуясь от `LoggingConfig`.
    """

    stream: LogStream = Field(
        default=LogStream.STDERR,
        description=(
            "Куда писать консольный обработчик: `stdout`, `stderr` или "
            "`none` (отключить консольный вывод, оставить только файл)."
        ),
    )
    stream_level: LogLevelName = Field(
        default=LogLevelName.INFO,
        description=(
            "Минимальный уровень сообщений для консольного обработчика "
            "(`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`). Игнорируется "
            "при `stream: none`."
        ),
    )
    file_enabled: bool = Field(
        default=True,
        description=(
            "Писать ли лог теста в файл `<тест>.log` внутри `log_dir`. Отключите, если нужен только консольный вывод."
        ),
    )
    file_level: LogLevelName = Field(
        default=LogLevelName.INFO,
        description=(
            "Минимальный уровень сообщений для файлового обработчика "
            "(`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`). Игнорируется "
            "при `file_enabled: false`."
        ),
    )


class WaiterConfig(BaseModel):
    """Настройки explicit-waiter: таймаут ожидания и интервал опроса."""

    timeout: float = Field(
        default=10.0,
        description=("Таймаут по умолчанию для explicit wait операций с элементами (сек). Должен быть положительным."),
        gt=0,
    )
    poll_interval: float = Field(
        default=0.5,
        description=("Пауза между опросами условия в explicit wait (сек). Должна быть положительной."),
        gt=0,
    )


class BaseConfig(BaseSettings):
    """Драйвер-независимая конфигурация.

    Наследуйтесь от этого класса для добавления полей, специфичных для
    драйвера.

    ### Порядок разрешения настроек (от высшего приоритета к низшему)

    1. Аргументы конструктора
    2. Переменные окружения (префикс `TEST_`)
    3. Файл `.env`
    4. Цепочка `config.json5` от текущей директории вверх до границы проекта
       (корень workspace - uv `[tool.uv.workspace]`, poetry `[tool.poetry]`
       или conda `environment.yml`; иначе корень проекта по маркерам
       `pyproject.toml` / `setup.py` / `requirements.txt`; до корня ФС обход
       не доходит). Более специфичный (ближний к cwd) побеждает
       менее специфичный. Например, при запуске из `tests/integration/critical/`
       приоритет: `critical/config.json5` > `integration/config.json5` >
       `tests/config.json5` > `config.json5` в корне проекта.
    5. Значения по умолчанию.
    """

    model_config = SettingsConfigDict(
        env_prefix="TEST_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    #: Имя файла конфига в цепочке `config_search_dir` → корень проекта.
    #: Подклассы могут переопределить под свой драйвер.
    CONFIG_FILENAME: ClassVar[str] = "config.json5"

    base_url: str = Field(
        default="http://localhost",
        description=("Базовый URL тестируемого приложения. Абсолютный, со схемой http или https."),
        pattern=r"^https?://\S+$",
    )
    waiter: WaiterConfig = Field(
        default_factory=WaiterConfig,
        description=(
            "Настройки explicit-waiter: таймаут ожидания (`timeout`) и интервал опроса условия (`poll_interval`)."
        ),
    )
    log_dir: str = Field(
        default="logs",
        description=(
            "Директория для файлов логов тестов (относительно корня проекта "
            "или абсолютный путь). Создается автоматически если отсутствует."
        ),
        min_length=1,
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description=(
            "Обработчики лога теста: консольный поток (`stream`: "
            "stdout/stderr/none) и файл `<тест>.log` в `log_dir` "
            "(`file_enabled`), каждый со своим уровнем (`stream_level` / "
            "`file_level`). Драйверные пакеты добавляют сюда свои каналы."
        ),
    )
    highlight_elements: bool = Field(
        default=False,
        description=(
            "Подсвечивать элемент красной рамкой на время взаимодействия. Удобно при отладке и записи скринкастов."
        ),
    )

    @classmethod
    @override
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        sources: list[PydanticBaseSettingsSource] = [
            init_settings,
            env_settings,
            dotenv_settings,
        ]

        config_chain = PathUtils.resolve_path_chain(
            PathUtils.config_search_dir(),
            cls.CONFIG_FILENAME,
        )

        # Цепочка упорядочена от специфичного к общему.
        # pydantic-settings отдает приоритет источникам, идущим раньше,
        # поэтому порядок сохраняется как есть.
        for config_path in config_chain:
            sources.append(JsoncConfigSettingsSource(settings_cls, json_file=config_path))

        return tuple(sources)
