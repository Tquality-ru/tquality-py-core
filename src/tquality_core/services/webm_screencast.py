"""Платформо-агностичный рекордер скринкаста: PNG-кадры → webm/VP9.

Знает только две вещи - откуда брать кадр (callable, возвращающий PNG-байты
или None) и доступна ли сейчас сессия для съёмки. Захват крутится в
фоновом потоке (`contextvars` копируются - вызывающая сторона видит свой
композишн-рут). На `stop()` кадры склеиваются в webm через
imageio-ffmpeg; каждый захваченный кадр повторяется столько output-тиков,
сколько нужно для покрытия его реальной длительности при заданном
`output_fps` - паузы в сценарии остаются паузами.

Используется как фолбэк в `AppiumScreencastProvider`
(`mobile: startRecordingScreen` запрещён MDM) и как единственный режим
в `SeleniumScreencastProvider` (Browser BiDi / CDP / classic screenshot).

Зависимости (`imageio`, `imageio-ffmpeg`, `numpy`, `Pillow`) импортируются
лениво при `stop()` - чтобы core оставался лёгким, а потребители тянули
их в свои pyproject.toml сами.
"""
from __future__ import annotations

import contextvars
import io
import logging
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable

_log = logging.getLogger(__name__)

MIME_TYPE = "video/webm"


class WebmScreencastRecorder:
    """Запись webm-скринкаста на фоновом потоке."""

    def __init__(
        self,
        *,
        frame_source: Callable[[], bytes | None],
        availability_check: Callable[[], bool] = lambda: True,
        frame_interval: float = 0.5,
        output_fps: int = 5,
        max_width: int = 1280,
        max_duration: float = 180.0,
    ) -> None:
        self._frame_source = frame_source
        self._availability_check = availability_check
        self._frame_interval = frame_interval
        self._output_fps = output_fps
        self._max_width = max_width
        self._max_duration = max_duration
        self._frames: list[tuple[bytes, float]] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Запустить фоновый сбор кадров. Повторный вызов игнорируется."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._frames = []
        self._stop_event = threading.Event()
        ctx = contextvars.copy_context()
        self._thread = threading.Thread(
            target=lambda: ctx.run(self._capture_loop),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> bytes | None:
        """Остановить сбор кадров, вернуть webm-байты или None если кадров нет."""
        if self._thread is None:
            return None
        self._stop_event.set()
        self._thread.join(timeout=5.0)
        self._thread = None
        frames = self._frames
        self._frames = []
        if not frames:
            _log.warning("WebmScreencastRecorder: ни одного кадра не захвачено")
            return None
        try:
            return self._encode_webm(frames)
        except Exception as exc:  # noqa: BLE001
            _log.warning(
                "WebmScreencastRecorder: не удалось закодировать webm: %s", exc,
            )
            return None

    def _capture_loop(self) -> None:
        started = time.monotonic()
        warned = False
        while (
            not self._stop_event.is_set()
            and time.monotonic() - started < self._max_duration
        ):
            if self._availability_check():
                try:
                    png = self._frame_source()
                    if png:
                        self._frames.append((png, time.monotonic()))
                except Exception as exc:  # noqa: BLE001
                    if not warned:
                        warned = True
                        _log.warning(
                            "WebmScreencastRecorder: ошибка захвата кадра, "
                            "дальнейшие будут пропущены тихо: %s",
                            exc,
                        )
            self._stop_event.wait(self._frame_interval)

    def _encode_webm(self, frames: list[tuple[bytes, float]]) -> bytes:
        import imageio.v3 as iio
        import numpy as np
        from PIL import Image

        fps = self._output_fps
        max_width = self._max_width
        frame_tick = 1.0 / fps
        rgb_frames: list[Any] = []
        target_size: tuple[int, int] | None = None
        for idx, (png, ts) in enumerate(frames):
            next_ts = (
                frames[idx + 1][1]
                if idx + 1 < len(frames)
                else ts + self._frame_interval
            )
            repeat = max(1, round((next_ts - ts) / frame_tick))

            img = Image.open(io.BytesIO(png)).convert("RGB")
            if img.width > max_width:
                ratio = max_width / img.width
                img = img.resize(
                    (max_width, int(img.height * ratio)),
                    Image.Resampling.LANCZOS,
                )
            # ffmpeg yuv420p требует чётные размеры.
            w, h = img.size
            if w % 2 or h % 2:
                img = img.resize((w - w % 2, h - h % 2), Image.Resampling.LANCZOS)
            # Кадры одной записи могут отличаться по размеру: источник кадра
            # переключается между способами съёмки (BiDi / CDP / классический
            # скриншот), а во время навигации размеры вьюпорта/скриншота
            # «плывут». `np.stack` требует одинаковой формы, иначе кодирование
            # падает с "all input arrays must have the same shape" и запись
            # теряется целиком. Приводим все кадры к размеру первого.
            if target_size is None:
                target_size = img.size
            elif img.size != target_size:
                img = img.resize(target_size, Image.Resampling.LANCZOS)
            arr = np.asarray(img)
            rgb_frames.extend([arr] * repeat)

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            iio.imwrite(
                tmp_path,
                np.stack(rgb_frames),
                fps=fps,
                codec="libvpx-vp9",
                output_params=["-b:v", "0", "-crf", "32"],
            )
            return tmp_path.read_bytes()
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass


__all__ = ["MIME_TYPE", "WebmScreencastRecorder"]
