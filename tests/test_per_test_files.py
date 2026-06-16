"""Тесты per-test pytest-плагина: вызов rebuilder'ов с директорией теста
и регистрация teardown через `item.addfinalizer`."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from tquality_core.plugins import per_test_files as ptf


class _FakeItem:
    """Минимальная замена pytest-`Item`: путь + сбор финализаторов."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.finalizers: list[object] = []

    def addfinalizer(self, fin: object) -> None:
        self.finalizers.append(fin)


@pytest.fixture(autouse=True)
def _isolated_rebuilders(monkeypatch: pytest.MonkeyPatch) -> None:
    """Чистый реестр rebuilder'ов на каждый тест."""
    monkeypatch.setattr(ptf, "_rebuilders", [])


def test_rebuilder_called_with_test_dir_and_teardown_registered(
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
    assert len(item.finalizers) == 1

    item.finalizers[0]()  # type: ignore[operator]
    assert calls.get("torn_down") is True


def test_rebuilder_returning_none_registers_no_teardown(tmp_path: Path) -> None:
    ptf.register_per_test_rebuilder(lambda _test_dir: None)

    test_file = tmp_path / "test_y.py"
    test_file.write_text("", encoding="utf-8")
    item = _FakeItem(test_file)
    ptf.pytest_runtest_setup(item)

    assert item.finalizers == []


def test_register_is_idempotent() -> None:
    def rebuilder(_test_dir: Path) -> None:
        return None

    ptf.register_per_test_rebuilder(rebuilder)
    ptf.register_per_test_rebuilder(rebuilder)

    assert ptf._rebuilders.count(rebuilder) == 1
