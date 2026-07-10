from collections.abc import Callable
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

#: Буквальный JS-скрипт либо путь к `.js`-файлу (`Path` / ресурс пакета).
Script = str | Path | Traversable


class BaseJSActions:
    """Общая база для JS-действий: хранит executor'ы, читает скрипт из
    `str`/`Path`/`Traversable` и исполняет его. Подклассы переопределяют
    `_prefix_args`, чтобы подставить неявные аргументы перед пользовательскими
    (`JsElementActions` подставляет текущий элемент)."""

    def __init__(
        self,
        js_executor: Callable[..., Any],
        js_async_executor: Callable[..., Any],
    ) -> None:
        self._execute_js = js_executor
        self._async_execute_js = js_async_executor

    @staticmethod
    def _to_source(script: Script) -> str:
        """Литеральный `str` - как есть; `Path`/`Traversable` - прочитать файл."""
        return script if isinstance(script, str) else script.read_text(encoding="utf-8")

    def _prefix_args(self) -> tuple[Any, ...]:
        """Неявные аргументы перед пользовательскими (по умолчанию - пусто)."""
        return ()

    def execute_script(self, script: Script, *args: Any) -> Any:
        """Исполнить скрипт. `script` - буквально JS либо путь к `.js`-файлу
        (`Path` / ресурс пакета): путь читается, строка исполняется как есть."""
        return self._execute_js(self._to_source(script), *self._prefix_args(), *args)

    def execute_async_script(self, script: Script, *args: Any) -> Any:
        return self._async_execute_js(
            self._to_source(script), *self._prefix_args(), *args,
        )

    def execute_global_script(self, script: Script, *args: Any) -> Any:
        """Как `execute_script`, но без неявных prefix-аргументов подкласса -
        для page/document-scope скриптов, которым текущий элемент не нужен
        (например, снятие подсветки идёт по всему документу, а не по элементу)."""
        return self._execute_js(self._to_source(script), *args)
