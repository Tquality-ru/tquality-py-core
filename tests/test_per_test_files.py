"""Тесты per-test pytest-плагина: смещение `config_search_dir` на директорию
теста и проигрывание rebuilder-teardown'ов (в обратном порядке).

Плагин обёрнут в `pytest_runtest_protocol`-hookwrapper - смещение обязано
произойти РАНЬШЕ любого setup-хука / фикстуры (иначе конфиг, собранный рано,
закешируется как testlocal с директорией CWD). См. регрессию в конце файла.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import pytest

from tquality_core import PathUtils
from tquality_core.plugins import per_test_files as ptf


class _FakeItem:
    """Минимальная замена pytest-`Item`: только путь."""

    def __init__(self, path: Path) -> None:
        self.path = path


@pytest.fixture(autouse=True)
def _isolated_rebuilders(monkeypatch: pytest.MonkeyPatch) -> None:
    """Чистый реестр rebuilder'ов на каждый тест."""
    monkeypatch.setattr(ptf, "_rebuilders", [])


def _run_setup(item: _FakeItem) -> Generator[None, Any, None]:
    """Прогнать pre-yield плагина (смещение + rebuilder'ы), остановиться на yield."""
    gen = ptf.pytest_runtest_protocol(item, None)
    next(gen)
    return gen


def _run_teardown(gen: Generator[None, Any, None]) -> None:
    """Досмотреть генератор - проигрывает teardown'ы в `finally`."""
    with pytest.raises(StopIteration):
        next(gen)


def test_rebuilder_called_on_setup_teardown_runs_on_teardown(
    tmp_path: Path,
) -> None:
    calls: dict[str, object] = {}

    def rebuilder(test_dir: Path) -> Callable[[], None]:
        calls["dir"] = test_dir

        def teardown() -> None:
            calls["torn_down"] = True

        return teardown

    ptf.register_per_test_rebuilder(rebuilder)

    test_file = tmp_path / "test_x.py"
    test_file.write_text("", encoding="utf-8")
    item = _FakeItem(test_file)

    gen = _run_setup(item)
    assert calls["dir"] == tmp_path.resolve()
    assert calls.get("torn_down") is None  # teardown ещё не звался

    _run_teardown(gen)
    assert calls.get("torn_down") is True


def test_teardowns_run_in_reverse_order(tmp_path: Path) -> None:
    order: list[int] = []

    for n in (1, 2, 3):

        def make(n: int) -> ptf.Rebuilder:
            return lambda _test_dir: lambda: order.append(n)

        ptf.register_per_test_rebuilder(make(n))

    test_file = tmp_path / "test_o.py"
    test_file.write_text("", encoding="utf-8")
    item = _FakeItem(test_file)

    gen = _run_setup(item)
    _run_teardown(gen)
    # search_dir сбрасывается последним, rebuilder'ы - в обратном порядке.
    assert order == [3, 2, 1]


def test_rebuilder_returning_none_adds_no_extra_teardown(tmp_path: Path) -> None:
    """None-rebuilder не добавляет teardown, но сброс search_dir всё равно есть."""
    ptf.register_per_test_rebuilder(lambda _test_dir: None)

    before = PathUtils.config_search_dir()
    test_file = tmp_path / "test_y.py"
    test_file.write_text("", encoding="utf-8")
    item = _FakeItem(test_file)

    gen = _run_setup(item)
    assert PathUtils.config_search_dir() == tmp_path.resolve()
    _run_teardown(gen)  # без ошибок
    assert PathUtils.config_search_dir() == before


def test_search_dir_set_to_test_dir_and_reset(tmp_path: Path) -> None:
    """Плагин смещает config_search_dir на директорию теста и снимает на teardown."""
    before = PathUtils.config_search_dir()
    test_file = tmp_path / "test_s.py"
    test_file.write_text("", encoding="utf-8")
    item = _FakeItem(test_file)

    gen = _run_setup(item)
    assert PathUtils.config_search_dir() == tmp_path.resolve()

    _run_teardown(gen)
    assert PathUtils.config_search_dir() == before


def test_teardown_exception_is_swallowed(tmp_path: Path) -> None:
    def rebuilder(_test_dir: Path) -> Callable[[], None]:
        def teardown() -> None:
            raise RuntimeError("boom")

        return teardown

    ptf.register_per_test_rebuilder(rebuilder)

    test_file = tmp_path / "test_e.py"
    test_file.write_text("", encoding="utf-8")
    item = _FakeItem(test_file)

    gen = _run_setup(item)
    _run_teardown(gen)  # не должно ронять прогон


def test_register_is_idempotent() -> None:
    def rebuilder(_test_dir: Path) -> None:
        return None

    ptf.register_per_test_rebuilder(rebuilder)
    ptf.register_per_test_rebuilder(rebuilder)

    assert ptf._rebuilders.count(rebuilder) == 1


def test_search_dir_shifted_before_early_setup_access(tmp_path: Path) -> None:
    """Регрессия: `config_search_dir` смещён на директорию теста ещё ДО самого
    раннего setup-доступа (conftest-хук / фикстура), а не CWD.

    Раньше плагин был обычным `pytest_runtest_setup`-хуком; conftest-хук
    (регистрируется позже, вызывается раньше по LIFO) видел config_search_dir =
    CWD (корень проекта с project-маркером). Конфиг, собранный там, кешировался
    как testlocal с неправильной директорией - `capabilities.json5` рядом с
    тестом не находился (`find_upwards` останавливался на маркере в CWD).

    Прогоняется в подпроцессе: нужен реальный pytest-протокол + entry-point
    плагина + изолированный `config_search_dir`-ContextVar.
    """
    # project-маркер в корне: без смещения find_upwards/цепочка остановятся тут.
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'regression'\nversion = '0'\n", encoding="utf-8",
    )
    # conftest-хук фиксирует config_search_dir на самом раннем setup-этапе.
    (tmp_path / "conftest.py").write_text(
        textwrap.dedent("""
            from tquality_core import PathUtils

            def pytest_runtest_setup(item):
                d = str(PathUtils.config_search_dir())
                assert d.endswith("sub"), (
                    f"config_search_dir не смещён до setup-хука: {d!r} "
                    f"(ожидался каталог теста .../sub)"
                )
        """),
        encoding="utf-8",
    )
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "test_x.py").write_text("def test_ok():\n    pass\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "sub/test_x.py", "-q", "-p", "no:cacheprovider"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"регрессия: config_search_dir не смещён до раннего доступа\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
