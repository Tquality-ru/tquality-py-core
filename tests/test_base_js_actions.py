"""Тесты диспетчеризации скриптов в `BaseJSActions`: пользователь может передать
свой литеральный JS (`str`) ИЛИ свой путь к `.js`-файлу (`Path`) - в первом
случае строка исполняется дословно, во втором читается содержимое файла.
Аргументы прокидываются после неявных префиксных (которые подставляет подкласс)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from tquality_core.services.base_js_actions import BaseJSActions

if TYPE_CHECKING:
    from pathlib import Path


class _Recorder:
    """Фейковый executor: запоминает `(source, *args)` последнего вызова."""

    def __init__(self, result: Any = None) -> None:
        self.result = result
        self.source: str | None = None
        self.args: tuple[Any, ...] = ()

    def __call__(self, source: str, *args: Any) -> Any:
        self.source = source
        self.args = args
        return self.result


def test_execute_script_with_custom_literal() -> None:
    """Свой литеральный JS исполняется как есть - без чтения файла."""
    sync = _Recorder(result=42)
    actions = BaseJSActions(sync, _Recorder())
    script = "return arguments[0] + 1;"

    result = actions.execute_script(script, 41)

    assert result == 42
    assert sync.source == script  # строка ушла дословно
    assert sync.args == (41,)


def test_execute_script_with_custom_path(tmp_path: Path) -> None:
    """Свой `Path` к `.js`-файлу читается, исполняется его содержимое."""
    sync = _Recorder()
    actions = BaseJSActions(sync, _Recorder())
    script_file = tmp_path / "custom.js"
    script_file.write_text("return document.title;", encoding="utf-8")

    actions.execute_script(script_file)

    assert sync.source == "return document.title;"
    assert sync.args == ()


def test_execute_async_script_uses_async_executor(tmp_path: Path) -> None:
    """`execute_async_script` идёт в async-executor; `Path` так же читается."""
    sync, async_executor = _Recorder(), _Recorder(result="done")
    actions = BaseJSActions(sync, async_executor)
    script_file = tmp_path / "async.js"
    script_file.write_text("arguments[0]();", encoding="utf-8")

    result = actions.execute_async_script(script_file, "callback")

    assert result == "done"
    assert async_executor.source == "arguments[0]();"
    assert async_executor.args == ("callback",)
    assert sync.source is None  # sync-executor не дёргали


def test_prefix_args_precede_user_args() -> None:
    """Неявные префиксные аргументы подкласса идут ПЕРЕД пользовательскими."""
    sync = _Recorder()

    class _WithPrefix(BaseJSActions):
        @override
        def _prefix_args(self) -> tuple[Any, ...]:
            return ("<element>",)

    _WithPrefix(sync, _Recorder()).execute_script("noop;", "user-arg")

    assert sync.args == ("<element>", "user-arg")
