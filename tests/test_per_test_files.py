"""Тесты per-test pytest-плагина: вызов rebuilder'ов с директорией теста
на setup и проигрывание teardown'ов (в обратном порядке) на teardown."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from tquality_core.plugins import per_test_files as ptf


class _FakeItem:
    """Минимальная замена pytest-`Item`: только путь. Teardown'ы плагин
    складывает на сам item через setattr."""

    def __init__(self, path: Path) -> None:
        self.path = path


@pytest.fixture(autouse=True)
def _isolated_rebuilders(monkeypatch: pytest.MonkeyPatch) -> None:
    """Чистый реестр rebuilder'ов на каждый тест."""
    monkeypatch.setattr(ptf, "_rebuilders", [])


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

    ptf.pytest_runtest_setup(item)
    assert calls["dir"] == tmp_path.resolve()
    assert calls.get("torn_down") is None  # teardown ещё не звался

    ptf.pytest_runtest_teardown(item)
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

    ptf.pytest_runtest_setup(item)
    ptf.pytest_runtest_teardown(item)
    assert order == [3, 2, 1]


def test_rebuilder_returning_none_adds_no_teardown(tmp_path: Path) -> None:
    ptf.register_per_test_rebuilder(lambda _test_dir: None)

    test_file = tmp_path / "test_y.py"
    test_file.write_text("", encoding="utf-8")
    item = _FakeItem(test_file)

    ptf.pytest_runtest_setup(item)
    assert getattr(item, ptf._TEARDOWN_ATTR) == []
    ptf.pytest_runtest_teardown(item)  # без ошибок


def test_teardown_exception_is_swallowed(tmp_path: Path) -> None:
    def rebuilder(_test_dir: Path) -> Callable[[], None]:
        def teardown() -> None:
            raise RuntimeError("boom")

        return teardown

    ptf.register_per_test_rebuilder(rebuilder)

    test_file = tmp_path / "test_e.py"
    test_file.write_text("", encoding="utf-8")
    item = _FakeItem(test_file)

    ptf.pytest_runtest_setup(item)
    ptf.pytest_runtest_teardown(item)  # не должно ронять прогон


def test_register_is_idempotent() -> None:
    def rebuilder(_test_dir: Path) -> None:
        return None

    ptf.register_per_test_rebuilder(rebuilder)
    ptf.register_per_test_rebuilder(rebuilder)

    assert ptf._rebuilders.count(rebuilder) == 1
