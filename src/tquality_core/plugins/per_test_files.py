"""Per-test pytest plugin: пересобирает зарегистрированные конфиги
из директории каждого теста, не из CWD pytest.

Для чего: `BaseConfig` уже умеет цепочку `config.json5` от стартовой
директории к границе проекта, а `CapabilitiesConfig` (в appium-пакете) -
first-match upward от неё. Но pytest-у в принципе всё равно, в какой
подпапке лежит тест: CWD один на весь процесс. Этот плагин перед каждым
тестом отдаёт зарегистрированным rebuilder'ам директорию текущего теста,
чтобы цепочка/lookup шли от теста вверх.

Использование интегрируется на уровне composition root'а. Стартовую
директорию поиска смещает `PathUtils.override_config_search_dir` -
тред-безопасно, без глобального `os.chdir`:

```python
from tquality_core import PathUtils, register_per_test_rebuilder

def _rebuild_for_test(test_dir: Path):
    with PathUtils.override_config_search_dir(test_dir):
        new_cfg = MyConfig()
    MyServices.config.override(new_cfg)
    return MyServices.config.reset_override  # вызовется по teardown
register_per_test_rebuilder(_rebuild_for_test)
```

`find_upwards` (реэкспорт `PathUtils.find_upwards`) - помощник для случаев,
когда нужно явно проверить наличие файла в цепочке (например,
перестраивать сервис только если есть свой `capabilities.json5` в
поддереве).
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from tquality_core.utils.path_utils import PathUtils

#: Реэкспорт для обратной совместимости - канонично живёт в `PathUtils`.
find_upwards = PathUtils.find_upwards

Rebuilder = Callable[[Path], "Callable[[], None] | None"]

_rebuilders: list[Rebuilder] = []


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


def pytest_runtest_setup(item: Any) -> None:
    test_dir = Path(str(item.path)).resolve().parent
    for rebuilder in _rebuilders:
        teardown = rebuilder(test_dir)
        if teardown is not None:
            # pytest вызовет финализаторы в обратном порядке на teardown
            # и поднимет их ошибки (а не проглотит молча).
            item.addfinalizer(teardown)


__all__ = [
    "find_upwards",
    "register_per_test_rebuilder",
]
