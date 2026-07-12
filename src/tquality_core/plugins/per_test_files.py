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

from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import pytest

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


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: Any, nextitem: Any) -> Generator[None, Any, None]:
    """Сместить `config_search_dir` на директорию теста на всё время его
    прогона (setup → call → teardown), затем восстановить.

    Обёрнуто в `pytest_runtest_protocol`-hookwrapper намеренно: смещение
    ОБЯЗАНО произойти раньше любого setup-хука и любой фикстуры. Иначе
    конфиг, собранный рано (фикстурой / плагином / conftest-хуком) до
    смещения, закешируется как testlocal с директорией CWD вместо
    директории теста - и `find_upwards`/цепочка `config.json5` не найдут
    файлы рядом с тестом (CWD - корень проекта, где стоит project-маркер,
    на котором поиск останавливается)."""
    test_dir = Path(str(item.path)).resolve().parent
    # Смещаем первым делом, затем даём rebuilder'ам пересобрать конфиги.
    teardowns: list[Callable[[], None]] = [PathUtils.use_config_search_dir(test_dir)]
    for rebuilder in _rebuilders:
        teardown = rebuilder(test_dir)
        if teardown is not None:
            teardowns.append(teardown)
    try:
        yield
    finally:
        # В обратном порядке: сначала rebuilder'ы, затем сброс search_dir.
        for teardown in reversed(teardowns):
            try:
                teardown()
            except Exception:  # noqa: BLE001 - teardown не должен ронять прогон
                pass


__all__ = [
    "find_upwards",
    "register_per_test_rebuilder",
]
