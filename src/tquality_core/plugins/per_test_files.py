"""Per-test pytest plugin: разрешает конфиги от директории каждого теста,
а не от CWD pytest.

Для чего: `BaseConfig` умеет собирать цепочку `config.json5` от стартовой
директории до границы проекта, а `CapabilitiesConfig` (в appium-пакете) -
first-match upward от неё. Но pytest-у всё равно, в какой подпапке лежит тест: CWD один
на весь процесс. Плагин регистрируется автоматически (entry-point `pytest11`)
и перед каждым тестом смещает `PathUtils.config_search_dir` на директорию
этого теста. Поэтому `config.json5` / `capabilities.json5` рядом с тестом
подхватываются сами собой (ближе к тесту = выше приоритет) - без conftest и
без ручного `override`. На teardown директория восстанавливается.

Опционально composition root может зарегистрировать rebuilder - он вызывается
тем же `test_dir` и пересобирает типизированный `*Config` поверх DI-провайдера
(полезно, когда сервисы держат закешированный singleton-конфиг):

```python
from tquality_core import register_per_test_rebuilder

def _rebuild_for_test(test_dir: Path):
    # config_search_dir уже смещён плагином на test_dir
    MyServices.config.override(MyConfig())
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


def pytest_runtest_setup(item: Any) -> None:
    test_dir = Path(str(item.path)).resolve().parent
    teardowns: list[Callable[[], None]] = []
    # Смещаем директорию поиска конфигов на директорию теста - первым делом,
    # чтобы её видели и rebuilder'ы, и любой конфиг, собираемый в теле теста.
    teardowns.append(PathUtils.use_config_search_dir(test_dir))
    for rebuilder in _rebuilders:
        teardown = rebuilder(test_dir)
        if teardown is not None:
            teardowns.append(teardown)
    # Teardown'ы складываем на сам item и проигрываем в `pytest_runtest_teardown`
    # (в обратном порядке: сначала rebuilder'ы, затем сброс search_dir).
    # `item.addfinalizer` здесь нельзя: на этапе setup-хука item ещё не на стеке
    # pytest-овского SetupState, и регистрация финализатора падает ассертом.
    setattr(item, _TEARDOWN_ATTR, teardowns)


def pytest_runtest_teardown(item: Any) -> None:
    teardowns: list[Callable[[], None]] = getattr(item, _TEARDOWN_ATTR, [])
    for teardown in reversed(teardowns):
        try:
            teardown()
        except Exception:  # noqa: BLE001 - teardown не должен ронять прогон
            pass
    if hasattr(item, _TEARDOWN_ATTR):
        delattr(item, _TEARDOWN_ATTR)


__all__ = [
    "find_upwards",
    "register_per_test_rebuilder",
]
