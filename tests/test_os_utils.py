"""Тесты для OSUtils."""

from __future__ import annotations

import sys

from tquality_core.utils.os_utils import OSUtils


def test_exactly_one_platform_is_true() -> None:
    """На любой ОС ровно одна из трёх проверок возвращает True."""
    flags = [OSUtils.is_macos(), OSUtils.is_windows(), OSUtils.is_linux()]
    assert sum(flags) == 1


def test_current_platform_matches_sys_platform() -> None:
    assert OSUtils.current_platform() == sys.platform
