"""CLI-команды tquality-py-core.

Точка входа: `tquality-config`. Доступные подкоманды:

- `init` - сгенерировать config.json5 в корне проекта со значениями по умолчанию
- `schema` - сгенерировать/обновить schema/config.schema.json (для мейнтейнеров)

Дополнительно экспортирует `build_cli(...)` - фабрику, которую переиспользуют
драйверные пакеты (`tquality-py-selenium`, `tquality-py-appium`), чтобы не
дублировать одну и ту же argparse-плиту:

```python
from tquality_core.cli import build_cli

main = build_cli(
    prog="tquality-selenium-config",
    description="…",
    config_cls=SeleniumConfig,
    schema_url=SELENIUM_SCHEMA_URL,
)
```
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tquality_core.config import BaseConfig, CONFIG_FILENAME
from tquality_core.schema import SCHEMA_URL, write_schema_file


def _find_project_root() -> Path:
    """Найти корень проекта: поднимаемся до pyproject.toml."""
    current = Path.cwd().resolve()
    for parent in (current, *current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return current


def _default_config_dict(
    config_cls: type[BaseConfig], schema_url: str,
) -> dict[str, Any]:
    """Словарь значений по умолчанию `config_cls` с ссылкой на схему."""
    cfg = config_cls()
    data: dict[str, Any] = {"$schema": schema_url}
    data.update(cfg.model_dump(mode="json"))
    return data


def _make_init(
    config_cls: type[BaseConfig], schema_url: str,
) -> Callable[[argparse.Namespace], int]:
    def cmd_init(args: argparse.Namespace) -> int:
        target_dir = Path(args.path).resolve() if args.path else _find_project_root()
        target_file = target_dir / CONFIG_FILENAME

        if target_file.exists() and not args.force:
            print(
                f"Файл уже существует: {target_file}. "
                f"Используйте --force для перезаписи.",
                file=sys.stderr,
            )
            return 1

        target_file.write_text(
            json.dumps(
                _default_config_dict(config_cls, schema_url),
                indent=4,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"Создан {target_file}")
        return 0

    return cmd_init


def _make_schema(
    config_cls: type[BaseConfig], schema_url: str,
) -> Callable[[argparse.Namespace], int]:
    def cmd_schema(args: argparse.Namespace) -> int:
        target_dir = Path(args.path).resolve() if args.path else _find_project_root()
        target_file = target_dir / "schema" / "config.schema.json"

        write_schema_file(target_file, config_cls, schema_url=schema_url)
        print(f"Схема записана в {target_file}")
        return 0

    return cmd_schema


def build_cli(
    *,
    prog: str,
    description: str,
    config_cls: type[BaseConfig],
    schema_url: str,
) -> Callable[[list[str] | None], int]:
    """Собрать `main`-функцию CLI для заданного класса конфигурации.

    Драйверные пакеты делают:

    ```python
    main = build_cli(
        prog="tquality-selenium-config", description="...",
        config_cls=SeleniumConfig, schema_url=SELENIUM_SCHEMA_URL,
    )
    ```

    и регистрируют `main` как `[project.scripts]`-entry point.
    """
    cmd_init = _make_init(config_cls, schema_url)
    cmd_schema = _make_schema(config_cls, schema_url)

    def main(argv: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(prog=prog, description=description)
        subparsers = parser.add_subparsers(dest="command", required=True)

        p_init = subparsers.add_parser(
            "init",
            help="Сгенерировать config.json5 со значениями по умолчанию",
        )
        p_init.add_argument(
            "--path",
            help="Каталог, в котором создать config.json5 "
                 "(по умолчанию - корень проекта)",
        )
        p_init.add_argument(
            "--force",
            action="store_true",
            help="Перезаписать существующий config.json5",
        )
        p_init.set_defaults(func=cmd_init)

        p_schema = subparsers.add_parser(
            "schema",
            help="Сгенерировать schema/config.schema.json (для мейнтейнеров)",
        )
        p_schema.add_argument(
            "--path",
            help="Корень репозитория (по умолчанию - текущий проект)",
        )
        p_schema.set_defaults(func=cmd_schema)

        args = parser.parse_args(argv)
        result: int = args.func(args)
        return result

    return main


main = build_cli(
    prog="tquality-config",
    description="Утилиты работы с конфигурацией tquality-py-core",
    config_cls=BaseConfig,
    schema_url=SCHEMA_URL,
)


if __name__ == "__main__":
    sys.exit(main(None))
