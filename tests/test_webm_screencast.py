"""Тесты `WebmScreencastRecorder` - background-захват PNG + склейка в webm."""
from __future__ import annotations

import io
import time
from collections.abc import Iterator
from unittest.mock import Mock

import pytest

from tquality_core import WebmScreencastRecorder


def _make_png(width: int = 16, height: int = 16) -> bytes:
    from PIL import Image
    img = Image.new("RGB", (width, height), color=(120, 30, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_captures_and_stitches_to_webm() -> None:
    src = Mock(return_value=_make_png())
    rec = WebmScreencastRecorder(
        frame_source=src,
        frame_interval=0.1,
        output_fps=5,
    )
    rec.start()
    time.sleep(0.4)
    payload = rec.stop()

    assert payload is not None
    # webm container starts with EBML magic bytes.
    assert payload[:4] == b"\x1aE\xdf\xa3"
    assert src.call_count >= 2


def test_no_frames_returns_none() -> None:
    src = Mock(return_value=None)  # source never yields a PNG
    rec = WebmScreencastRecorder(
        frame_source=src,
        frame_interval=0.05,
    )
    rec.start()
    time.sleep(0.15)
    assert rec.stop() is None


def test_availability_check_pauses_capture() -> None:
    src = Mock(return_value=_make_png())
    rec = WebmScreencastRecorder(
        frame_source=src,
        availability_check=lambda: False,
        frame_interval=0.05,
    )
    rec.start()
    time.sleep(0.15)
    rec.stop()
    src.assert_not_called()


def test_stop_without_start_returns_none() -> None:
    rec = WebmScreencastRecorder(frame_source=lambda: _make_png())
    assert rec.stop() is None


def test_double_start_is_noop() -> None:
    src = Mock(return_value=_make_png())
    rec = WebmScreencastRecorder(frame_source=src, frame_interval=0.05)
    rec.start()
    rec.start()  # should not crash, should not start a 2nd thread
    time.sleep(0.1)
    payload = rec.stop()
    assert payload is not None


def test_source_exceptions_are_swallowed() -> None:
    sequence: Iterator[bytes | Exception] = iter([
        RuntimeError("transient blip"),
        _make_png(),
        _make_png(),
    ])

    def src() -> bytes:
        item = next(sequence)
        if isinstance(item, Exception):
            raise item
        return item

    rec = WebmScreencastRecorder(frame_source=src, frame_interval=0.05)
    rec.start()
    time.sleep(0.3)
    payload = rec.stop()
    # Despite the first call raising, the recorder kept polling and produced webm.
    assert payload is not None


def test_max_duration_caps_capture() -> None:
    src = Mock(return_value=_make_png())
    rec = WebmScreencastRecorder(
        frame_source=src,
        frame_interval=0.05,
        max_duration=0.1,
    )
    rec.start()
    time.sleep(0.5)  # well past max_duration; loop should have exited on its own
    payload = rec.stop()
    # Frames are limited to those captured within the 0.1s budget.
    assert payload is not None
    assert src.call_count <= 4
