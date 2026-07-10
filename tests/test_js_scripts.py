"""Тесты целостности JS-слоя: каждый `.js`-файл зарегистрирован в моделях, и
каждая зарегистрированная опция покрыта методом-обёрткой сервиса.

Инварианты вынесены в `_assert_*`-хелперы, поэтому позитивные тесты (реальные
реестры согласованы) и негативные (на сломанных данных проверка падает) гоняют
один и тот же код-алерт - негатив гарантирует, что позитив реально что-то ловит."""

from __future__ import annotations

import inspect
import re

import pytest

from tquality_core import PathUtils
from tquality_core.models.assets.js_scripts.common_element_js_scripts import (
    CommonElementJSScripts,
)
from tquality_core.models.assets.js_scripts.common_js_scripts import CommonJSScripts
from tquality_core.services.js_actions import JSActions
from tquality_core.services.js_element_actions import JsElementActions


def _registry_names(registry_cls: type) -> set[str]:
    """Имена зарегистрированных скриптов (UPPER_CASE-атрибуты реестра)."""
    return {name for name in dir(registry_cls) if name.isupper()}


def _assert_registry_matches_disk(registered: set[str], on_disk: set[str], ctx: str) -> None:
    """Падает, если есть `.js`-файл без записи реестра ИЛИ запись без файла."""
    assert registered == on_disk, (
        f"{ctx}: рассинхрон "
        f"(только в реестре: {sorted(registered - on_disk)}; "
        f"только на диске: {sorted(on_disk - registered)})"
    )


def _assert_every_script_covered(registered: set[str], referenced: set[str], ctx: str) -> None:
    """Падает, если зарегистрированный скрипт не используется ни одним методом."""
    missing = registered - referenced
    assert not missing, f"{ctx}: нет метода-обёртки для {sorted(missing)}"


# ── позитив: реальные реестры и файлы согласованы ────────────────────────────


@pytest.mark.parametrize(
    ("registry_cls", "subdir"),
    [
        (CommonElementJSScripts, "element"),
        (CommonJSScripts, "document"),
    ],
)
def test_all_js_files_registered(registry_cls: type, subdir: str) -> None:
    """Множество `.js`-файлов в `assets/js_scripts/<subdir>` совпадает с
    множеством записей реестра: ни «забытого» файла, ни записи без файла."""
    registered = {getattr(registry_cls, name).name for name in _registry_names(registry_cls)}
    on_disk = {
        child.name for child in PathUtils.get_js_scripts_dir().joinpath(subdir).iterdir() if child.name.endswith(".js")
    }
    _assert_registry_matches_disk(registered, on_disk, registry_cls.__name__)


@pytest.mark.parametrize(
    ("service_cls", "registry_cls", "registry_name"),
    [
        (JSActions, CommonJSScripts, "CommonJSScripts"),
        (JsElementActions, CommonElementJSScripts, "CommonElementJSScripts"),
    ],
)
def test_every_script_has_wrapper_method(
    service_cls: type,
    registry_cls: type,
    registry_name: str,
) -> None:
    """Каждая запись реестра используется в коде сервиса-обёртки (есть метод,
    дергающий `Registry.<NAME>`)."""
    source = inspect.getsource(service_cls)
    referenced = set(re.findall(rf"{registry_name}\.([A-Z_][A-Z0-9_]*)", source))
    _assert_every_script_covered(_registry_names(registry_cls), referenced, service_cls.__name__)


# ── негатив: те же проверки реально срабатывают на сломанных данных ───────────


def test_orphan_script_file_is_detected() -> None:
    """`.js`-файл без записи в реестре - проверка целостности падает."""
    with pytest.raises(AssertionError, match="только на диске"):
        _assert_registry_matches_disk({"a.js"}, {"a.js", "orphan.js"}, "fake")


def test_registry_entry_without_file_is_detected() -> None:
    """Запись реестра без `.js`-файла на диске - проверка целостности падает."""
    with pytest.raises(AssertionError, match="только в реестре"):
        _assert_registry_matches_disk({"a.js", "ghost.js"}, {"a.js"}, "fake")


def test_script_without_wrapper_method_is_detected() -> None:
    """Зарегистрированный скрипт без метода-обёртки - проверка покрытия падает."""
    with pytest.raises(AssertionError, match="UNUSED"):
        _assert_every_script_covered({"USED", "UNUSED"}, {"USED"}, "fake")
