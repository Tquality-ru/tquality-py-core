"""Тесты core-`Waiter`: bool-возврат, raise_on_timeout, poll_interval,
message override, ignored_exceptions."""

from __future__ import annotations

import time
from unittest.mock import Mock

import pytest

from tquality_core import Waiter, WaiterConfig, WaitTimeoutError


class _DummyConfig:
    waiter = WaiterConfig(timeout=1.0)


def _make_waiter(
    *,
    ignored_exceptions: tuple[type[BaseException], ...] = (),
    default_raise_cls: type[BaseException] = WaitTimeoutError,
) -> tuple[Waiter, Mock]:
    logger = Mock()
    waiter = Waiter(
        config=_DummyConfig(),  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
        logger_resolver=lambda: logger,
        ignored_exceptions=ignored_exceptions,
        default_raise_cls=default_raise_cls,
    )
    return waiter, logger


def test_returns_true_when_condition_truthy() -> None:
    waiter, _ = _make_waiter()
    assert waiter.until(lambda: True) is True


def test_returns_false_on_timeout_by_default() -> None:
    waiter, _ = _make_waiter()
    assert waiter.until(lambda: False, timeout=0.05, poll_interval=0.01) is False


def test_raise_on_timeout_true_raises_default_cls() -> None:
    waiter, _ = _make_waiter()
    with pytest.raises(WaitTimeoutError, match="custom-msg"):
        waiter.until(
            lambda: False,
            timeout=0.05,
            poll_interval=0.01,
            raise_on_timeout=True,
            message="custom-msg",
        )


def test_raise_on_timeout_uses_default_raise_cls_from_init() -> None:
    class MyError(Exception):
        pass

    waiter, _ = _make_waiter(default_raise_cls=MyError)
    with pytest.raises(MyError):
        waiter.until(
            lambda: False,
            timeout=0.05,
            poll_interval=0.01,
            raise_on_timeout=True,
        )


def test_raise_on_timeout_explicit_class_overrides_default() -> None:
    class MyError(Exception):
        pass

    waiter, _ = _make_waiter()
    with pytest.raises(MyError, match="explicit"):
        waiter.until(
            lambda: False,
            timeout=0.05,
            poll_interval=0.01,
            raise_on_timeout=MyError,
            message="explicit",
        )


def test_ignored_exceptions_are_swallowed() -> None:
    waiter, _ = _make_waiter(ignored_exceptions=(KeyError,))
    seq = iter([KeyError("not yet"), KeyError("still not"), True])

    def cond() -> bool:
        return next(seq)  # type: ignore[return-value]  # ty:ignore[invalid-return-type]

    assert waiter.until(cond, poll_interval=0.01) is True


def test_per_call_ignored_overrides_init_ignored() -> None:
    waiter, _ = _make_waiter(ignored_exceptions=(KeyError,))

    def cond() -> bool:
        raise ValueError("real error")

    # KeyError default doesn't catch ValueError - it propagates.
    with pytest.raises(ValueError):
        waiter.until(cond, poll_interval=0.01)

    # Per-call override that DOES include ValueError swallows it.
    started = time.monotonic()
    assert (
        waiter.until(
            cond,
            timeout=0.05,
            poll_interval=0.01,
            ignored_exceptions=(ValueError,),
        )
        is False
    )
    assert time.monotonic() - started < 0.5


def test_non_ignored_exception_propagates() -> None:
    waiter, _ = _make_waiter(ignored_exceptions=(KeyError,))

    def cond() -> bool:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        waiter.until(cond, timeout=0.05, poll_interval=0.01)


def test_message_falls_back_to_default() -> None:
    waiter, logger = _make_waiter()
    waiter.until(lambda: True)
    # First log line is "Waiting (...): condition" - default placeholder.
    call_args = logger.info.call_args_list[0]
    assert call_args.args[-1] == "condition"


def test_message_passes_to_log_and_exception() -> None:
    waiter, logger = _make_waiter()
    with pytest.raises(WaitTimeoutError, match="search results screen"):
        waiter.until(
            lambda: False,
            timeout=0.05,
            poll_interval=0.01,
            raise_on_timeout=True,
            message="search results screen to be present",
        )
    waiting_log = logger.info.call_args_list[0].args[-1]
    assert waiting_log == "search results screen to be present"


def test_timeout_uses_config_default() -> None:
    class _C:
        waiter = WaiterConfig(timeout=0.05)

    logger = Mock()
    w = Waiter(
        config=_C(),  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
        logger_resolver=lambda: logger,
    )
    started = time.monotonic()
    assert w.until(lambda: False, poll_interval=0.01) is False
    elapsed = time.monotonic() - started
    # Within 100ms of the configured 50ms
    assert 0.04 <= elapsed <= 0.5


def test_poll_interval_uses_config_default() -> None:
    class _C:
        waiter = WaiterConfig(timeout=0.25, poll_interval=0.1)

    logger = Mock()
    w = Waiter(
        config=_C(),  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
        logger_resolver=lambda: logger,
    )
    calls: list[float] = []

    def cond() -> bool:
        calls.append(time.monotonic())
        return False

    # No per-call poll_interval - falls back to config.waiter.poll_interval.
    w.until(cond)
    # 0.25s budget at 0.1s interval - expect roughly 3 polls (0, 0.1, 0.2).
    assert 2 <= len(calls) <= 4


def test_poll_interval_controls_polling_frequency() -> None:
    waiter, _ = _make_waiter()
    calls: list[float] = []

    def cond() -> bool:
        calls.append(time.monotonic())
        return False

    waiter.until(cond, timeout=0.25, poll_interval=0.1)
    # 0.25s budget at 0.1s interval - expect roughly 3 polls (0, 0.1, 0.2).
    assert 2 <= len(calls) <= 4


def test_returning_falsy_keeps_polling_until_truthy() -> None:
    waiter, _ = _make_waiter()
    seq = iter([False, 0, None, "", "ok"])
    assert waiter.until(lambda: next(seq), poll_interval=0.01) is True
