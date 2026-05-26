"""Per-test pytest plugin: пересобирает зарегистрированные конфиги
из директории каждого теста, не из CWD pytest.

Для чего: `BaseConfig` уже умеет цепочку `config.json5` от CWD к корню
workspace, а `CapabilitiesConfig` (в appium-пакете) - first-match upward
от CWD. Но pytest-у в принципе всё равно, в какой подпапке лежит тест:
CWD один на весь процесс. Этот плагин ставит CWD равной директории
текущего теста на время пересборки конфигов, чтобы цепочка/lookup
шли от теста вверх.

Использование интегрируется на уровне composition root'а:

```python
from tquality_core import register_per_test_rebuilder

def _rebuild_for_test(test_dir: Path):
    with _cwd(test_dir):
        new_cfg = MyConfig()
    MyServices.config.override(new_cfg)
    return MyServices.config.reset_override  # вызовется по teardown
register_per_test_rebuilder(_rebuild_for_test)
```

`find_upwards(start, filename)` - помощник для случаев, когда нужно
явно проверить наличие файла в цепочке (например, перестраивать
сервис только если есть свой `capabilities.json5` в поддереве).
Останавливается на первом `pyproject.toml` (граница workspace).
"""
from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

Rebuilder = Callable[[Path], "Callable[[], None] | None"]

_rebuilders: list[Rebuilder] = []
_TEARDOWN_ATTR = "_tquality_per_test_teardowns"


def register_per_test_rebuilder(rebuilder: Rebuilder) -> None:
    """Зарегистрировать функцию, перестраивающую DI-сервисы под тест.

    Плагин вызовет её перед каждым тестом с `test_dir` (директория
    тестового файла). Возвращаемый колбэк (или `None`) исполняется на
    teardown - используйте его, чтобы откатить `.override(...)` назад.

    Регистрация идемпотентна: повторный вызов с тем же объектом не
    добавляет дубль (важно, если `setup()` зовётся несколько раз -
    например в тестах самой интеграции).
    """
    if rebuilder not in _rebuilders:
        _rebuilders.append(rebuilder)


def find_upwards(
    start: Path,
    filename: str,
    *,
    stop_at: tuple[str, ...] = ("pyproject.toml",),
) -> Path | None:
    """Найти `filename`, поднимаясь от `start` к корню ФС.

    Останавливается на первой директории, где есть один из `stop_at`-
    маркеров (по умолчанию - `pyproject.toml`, то есть корень workspace).
    Маркер проверяется ПОСЛЕ файла - если файл и маркер в одной директории,
    файл будет найден. Возвращает `None`, если ничего не нашлось.
    """
    current = start.resolve()
    for parent in (current, *current.parents):
        candidate = parent / filename
        if candidate.exists():
            return candidate
        if any((parent / marker).exists() for marker in stop_at):
            return None
    return None


@contextmanager
def cwd(path: Path) -> Iterator[None]:
    """Временно сменить CWD - удобно для конструкторов, читающих файлы
    относительно текущей директории."""
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def pytest_runtest_setup(item: Any) -> None:
    test_dir = Path(str(item.path)).resolve().parent
    teardowns: list[Callable[[], None]] = []
    for rebuilder in _rebuilders:
        teardown = rebuilder(test_dir)
        if teardown is not None:
            teardowns.append(teardown)
    setattr(item, _TEARDOWN_ATTR, teardowns)


def pytest_runtest_teardown(item: Any) -> None:
    teardowns: list[Callable[[], None]] = getattr(item, _TEARDOWN_ATTR, [])
    for teardown in reversed(teardowns):
        try:
            teardown()
        except Exception:
            pass
    if hasattr(item, _TEARDOWN_ATTR):
        delattr(item, _TEARDOWN_ATTR)


__all__ = [
    "cwd",
    "find_upwards",
    "register_per_test_rebuilder",
]
