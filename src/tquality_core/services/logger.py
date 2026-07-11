"""Логгер тестов с интеграцией в allure.

Каждый тест получает свой файл лога, именованный по pytest node ID. Декоратор
и контекстный менеджер `step` оборачивают действия в allure-шаги. Шаги уровня
CRITICAL делают скриншот в конце (успех или сбой) через подключаемый провайдер.
"""

from __future__ import annotations

import enum
import functools
import hashlib
import logging
import re
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

import allure
from static_dependency_injector.testing import TestContext
from typing_extensions import deprecated

from tquality_core.models.config import LoggingConfig, LogLevelName, LogStream

if TYPE_CHECKING:
    from tquality_core.models import BaseConfig

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
_LOG_DATEFMT = "%H:%M:%S"
#: Каналы device/network пишут уже сформированные строки (со своими
#: метками времени от ОС-источника) - без префикса logging-форматтера.
_CHANNEL_FORMAT = "%(message)s"


class LogLevel(enum.Enum):
    """Уровень важности шага.

    - NORMAL: только лог + allure-шаг.
    - CRITICAL: + скриншот в конце (успех или сбой).
    - WITH_SCREENCAST: + запись экрана в виде GIF на время выполнения шага.
      Требует зарегистрированного `ScreencastProvider` (обычно из selenium).
    """

    NORMAL = "normal"
    CRITICAL = "critical"
    WITH_SCREENCAST = "with-screencast"


class ScreenshotProvider(Protocol):
    """Интерфейс драйвер-специфичного провайдера скриншотов.

    Регистрируется как DI-сервис (`providers.Singleton(...)`) в контейнере
    и инжектится в `Logger.__init__`. CRITICAL-шаги вызывают `capture()` в
    конце (успех или сбой) и прикрепляют PNG к allure-отчету.
    """

    def is_available(self) -> bool:
        """Вернуть True, если сессия драйвера сейчас активна."""
        ...

    def capture(self) -> bytes:
        """Вернуть текущий экран как PNG-байты."""
        ...


class ScreencastProvider(Protocol):
    """Интерфейс провайдера screencast-записи.

    Регистрируется как DI-сервис и инжектится в `Logger.__init__`.
    Шаги уровня `WITH_SCREENCAST` вызывают `start()` на входе и `stop()`
    на выходе; полученный бинарник (GIF/mp4) прикрепляется к allure-шагу.
    """

    def is_available(self) -> bool:
        """Вернуть True, если сессия драйвера сейчас активна."""
        ...

    def start(self) -> None:
        """Начать запись. Должен быть идемпотентным при повторном вызове."""
        ...

    def stop(self) -> bytes | None:
        """Остановить запись и вернуть бинарник или None, если кадров нет."""
        ...

    def mime_type(self) -> str:
        """MIME-тип результата `stop()` - например, 'image/gif' или 'video/mp4'."""
        ...


StepEnterHook = Callable[["Step"], None]
StepExitHook = Callable[
    ["Step", type[BaseException] | None, BaseException | None],
    None,
]


class Step:
    """Шаг - контекстный менеджер и декоратор. Передается в step-хуки и
    доступен через `Logger.current_step` / `active_step_stack`, поэтому
    `title` / `level` - публичные."""

    def __init__(
        self,
        logger: Logger,
        title: str,
        level: LogLevel = LogLevel.NORMAL,
    ) -> None:
        self._logger = logger
        self._title = title
        self._level = level
        self._allure_step = allure.step(title)

    @property
    def title(self) -> str:
        return self._title

    @property
    def level(self) -> LogLevel:
        return self._level

    def __enter__(self) -> Step:
        self._logger.info("Шаг: %s", self._title)
        self._allure_step.__enter__()  # type: ignore[no-untyped-call]
        self._logger._step_stack += (self,)
        for hook in self._logger._enter_hooks:
            try:
                hook(self)
            except Exception as exc:  # noqa: BLE001
                self._logger.warning(
                    "Step enter hook %r упал: %s",
                    hook,
                    exc,
                )
        if self._level == LogLevel.WITH_SCREENCAST:
            provider = self._logger.screencast_provider
            if provider is None:
                self._logger.warning(
                    "WITH_SCREENCAST: ScreencastProvider не зарегистрирован, пропускаю",
                )
            elif not provider.is_available():
                self._logger.warning(
                    "WITH_SCREENCAST: сессия драйвера неактивна, пропускаю",
                )
            else:
                try:
                    provider.start()
                except Exception:  # noqa: BLE001
                    self._logger.warning(
                        "Не удалось начать screencast: %s",
                        self._title,
                    )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if self._level == LogLevel.CRITICAL:
                self._attach_screenshot(failed=exc_type is not None)
            elif self._level == LogLevel.WITH_SCREENCAST:
                self._attach_screencast()
            for hook in self._logger._exit_hooks:
                try:
                    hook(self, exc_type, exc_val)
                except Exception as exc:  # noqa: BLE001
                    self._logger.warning(
                        "Step exit hook %r упал: %s",
                        hook,
                        exc,
                    )
        finally:
            stack = self._logger._step_stack
            if stack and stack[-1] is self:
                self._logger._step_stack = stack[:-1]
            self._allure_step.__exit__(exc_type, exc_val, exc_tb)  # type: ignore[no-untyped-call]
            status = "СБОЙ" if exc_type else "завершен"
            self._logger.info("Шаг %s: %s", status, self._title)

    def _attach_screenshot(self, *, failed: bool) -> None:
        provider = self._logger.screenshot_provider
        if provider is None:
            self._logger.warning(
                "CRITICAL: ScreenshotProvider не зарегистрирован, пропускаю",
            )
            return
        if not provider.is_available():
            self._logger.warning(
                "CRITICAL: сессия драйвера неактивна, пропускаю скриншот",
            )
            return
        label = f"Скриншот [СБОЙ]: {self._title}" if failed else f"Скриншот: {self._title}"
        try:
            png = provider.capture()
        except Exception:  # noqa: BLE001
            self._logger.warning("Не удалось снять скриншот: %s", self._title)
            return
        allure.attach(png, name=label, attachment_type=allure.attachment_type.PNG)

    def _attach_screencast(self) -> None:
        provider = self._logger.screencast_provider
        if provider is None:
            self._logger.warning(
                "WITH_SCREENCAST: ScreencastProvider не зарегистрирован, пропускаю прикрепление записи",
            )
            return
        try:
            payload = provider.stop()
        except Exception:  # noqa: BLE001
            self._logger.warning(
                "Не удалось остановить screencast: %s",
                self._title,
            )
            return
        if not payload:
            return
        # Передаём attachment_type с MIME, а не только extension: иначе allure
        # сохраняет вложение без типа и в отчёте не показывает встроенный
        # видеоплеер (скачанный файл при этом проигрывается - тип угадывает ОС).
        mime = provider.mime_type()
        video_type = {
            "video/mp4": allure.attachment_type.MP4,
            "video/webm": allure.attachment_type.WEBM,
            "video/ogg": allure.attachment_type.OGG,
        }.get(mime)
        name = f"Screencast: {self._title}"
        if video_type is not None:
            allure.attach(payload, name=name, attachment_type=video_type)
        else:
            allure.attach(payload, name=name, extension=mime.split("/")[-1])

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return func(*args, **kwargs)

        return wrapper


class Logger:
    """Логгер на один контекст теста с отдельным файловым обработчиком.

    Получает `screenshot_provider` и `screencast_provider` через DI -
    шаги уровня CRITICAL и WITH_SCREENCAST используют их для
    прикрепления артефактов к allure-отчету.
    """

    def __init__(
        self,
        config: BaseConfig,
        screenshot_provider: ScreenshotProvider | None = None,
        screencast_provider: ScreencastProvider | None = None,
    ) -> None:
        self.screenshot_provider = screenshot_provider
        self.screencast_provider = screencast_provider

        # Стек активных шагов и хуки на enter/exit - per-Logger,
        # чтобы в параллельных прогонах не путать "innermost step какого
        # из тестов". Каждый тест получает свой Logger, свой стек, свои хуки.
        self._step_stack: tuple[Step, ...] = ()
        self._enter_hooks: list[StepEnterHook] = []
        self._exit_hooks: list[StepExitHook] = []

        self._started_at = datetime.now()
        timestamp = self._started_at.strftime("%Y%m%d_%H%M%S")
        node_id = self._test_node_id()

        log_cfg: LoggingConfig = getattr(config, "logging", None) or LoggingConfig()
        self._log_dir = Path(config.log_dir)
        self._base_name = f"{timestamp}_{node_id}"
        #: Вспомогательные файловые каналы (device/network логи драйвера),
        #: создаваемые лениво через `add_file_channel`.
        self._channels: dict[str, logging.Logger] = {}

        self._log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self._log_dir / f"{self._base_name}.log"

        self._logger = logging.getLogger(f"tquality.{self._base_name}")
        # Своя цепочка обработчиков - не пропускаем в root, чтобы pytest/
        # другие хендлеры не дублировали записи.
        self._logger.propagate = False
        # При совпадении node_id+timestamp (теоретически) getLogger вернёт
        # тот же объект - чистим, чтобы не накопить дублирующие обработчики.
        for handler in list(self._logger.handlers):
            self._logger.removeHandler(handler)

        formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATEFMT)

        if log_cfg.file_enabled:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(log_cfg.file_level.value)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

        stream = self._resolve_stream(log_cfg.stream)
        if stream is not None:
            stream_handler = logging.StreamHandler(stream)
            stream_handler.setLevel(log_cfg.stream_level.value)
            stream_handler.setFormatter(formatter)
            self._logger.addHandler(stream_handler)

        # Уровень самого логгера - не строже самого мягкого обработчика,
        # иначе тот не получит сообщения, которые готов пропустить.
        self._logger.setLevel(self._root_level(log_cfg))

        self._logger.info("Лог запущен: %s", log_file)

    @staticmethod
    def _resolve_stream(stream: LogStream) -> Any:
        """Поток для `StreamHandler` по `LogStream`; `None` для `NONE`."""
        if stream == LogStream.STDOUT:
            return sys.stdout
        if stream == LogStream.STDERR:
            return sys.stderr
        return None

    @staticmethod
    def _root_level(log_cfg: LoggingConfig) -> int:
        """Числовой уровень логгера = минимум среди включённых обработчиков.

        Логгер фильтрует до обработчиков, поэтому он должен пропускать всё,
        что готов записать хотя бы один из них. Если не включён ни один -
        остаётся `INFO`.
        """
        levels: list[int] = []
        if log_cfg.file_enabled:
            levels.append(logging.getLevelName(log_cfg.file_level.value))
        if log_cfg.stream != LogStream.NONE:
            levels.append(logging.getLevelName(log_cfg.stream_level.value))
        return min(levels) if levels else logging.INFO

    @property
    def log_dir(self) -> Path:
        """Директория, куда пишутся файлы лога этого теста."""
        return self._log_dir

    @property
    def base_name(self) -> str:
        """Базовое имя файлов лога теста (`<timestamp>_<node_id>`)."""
        return self._base_name

    def add_file_channel(
        self,
        name: str,
        level: LogLevelName | str = LogLevelName.INFO,
    ) -> logging.Logger:
        """Открыть вспомогательный файловый канал `<base_name>.<name>.log`.

        Возвращает отдельный `logging.Logger` с собственным
        `FileHandler` (формат - голое сообщение, см. `_CHANNEL_FORMAT`).
        Предназначен для драйвер-специфичных коллекторов, складывающих
        сырые потоки (например, appium device/network логи) в отдельные
        файлы рядом с основным логом теста. Повторный вызов с тем же
        `name` возвращает уже открытый канал.
        """
        existing = self._channels.get(name)
        if existing is not None:
            return existing

        level_value = level.value if isinstance(level, LogLevelName) else level
        self._log_dir.mkdir(parents=True, exist_ok=True)
        channel_file = self._log_dir / f"{self._base_name}.{name}.log"

        channel = logging.getLogger(f"tquality.{self._base_name}.{name}")
        channel.propagate = False
        channel.setLevel(level_value)
        for handler in list(channel.handlers):
            handler.close()
            channel.removeHandler(handler)

        handler = logging.FileHandler(channel_file, encoding="utf-8")
        handler.setLevel(level_value)
        handler.setFormatter(logging.Formatter(_CHANNEL_FORMAT))
        channel.addHandler(handler)

        self._channels[name] = channel
        return channel

    def close_file_channel(self, name: str) -> None:
        """Закрыть и снять обработчики вспомогательного канала `name`.

        No-op, если канал не открывался. Освобождает файловый дескриптор -
        вызывайте при teardown коллектора.
        """
        channel = self._channels.pop(name, None)
        if channel is None:
            return
        for handler in list(channel.handlers):
            handler.close()
            channel.removeHandler(handler)

    def info(self, msg: str, *args: Any) -> None:
        self._logger.info(msg, *args)

    def warning(self, msg: str, *args: Any) -> None:
        self._logger.warning(msg, *args)

    def error(self, msg: str, *args: Any) -> None:
        self._logger.error(msg, *args)

    def debug(self, msg: str, *args: Any) -> None:
        self._logger.debug(msg, *args)

    def step(self, title: str, level: LogLevel = LogLevel.NORMAL) -> Step:
        return Step(self, title, level=level)

    def register_step_enter_hook(
        self,
        hook: StepEnterHook,
    ) -> Callable[[], None]:
        """Зарегистрировать колбэк, вызываемый при входе в любой шаг.

        Колбэк получает `(step,)`. Хук вызывается уже после push в стек,
        поэтому внутри хука `logger.current_step is step`. Исключения
        логируются как warning, не ломают шаг. Возвращает unregister-callable.
        """
        self._enter_hooks.append(hook)

        def _unregister() -> None:
            try:
                self._enter_hooks.remove(hook)
            except ValueError:
                pass

        return _unregister

    def register_step_exit_hook(
        self,
        hook: StepExitHook,
    ) -> Callable[[], None]:
        """Зарегистрировать колбэк, вызываемый при выходе из любого шага.

        Колбэк получает `(step, exc_type, exc_val)` - может судить по
        `exc_type`, упал ли шаг, и читать `step.title` / `step.level`.
        Хук вызывается до pop из стека (`logger.current_step is step` внутри).
        Исключения логируются как warning, не ломают шаг. Возвращает
        unregister-callable.
        """
        self._exit_hooks.append(hook)

        def _unregister() -> None:
            try:
                self._exit_hooks.remove(hook)
            except ValueError:
                pass

        return _unregister

    @property
    def current_step(self) -> Step | None:
        """Innermost активный шаг (вершина стека) или None если нет активных."""
        return self._step_stack[-1] if self._step_stack else None

    @property
    def active_step_stack(self) -> tuple[Step, ...]:
        """Снимок стека активных шагов от outermost к innermost."""
        return self._step_stack

    @staticmethod
    def _test_node_id() -> str:
        """Сформировать безопасное для файловой системы имя из ID активного теста.

        Источник - `TestContext.current.id` (pytest nodeid / unittest id) из
        static-di: фреймворк-нейтрально, без чтения `PYTEST_CURRENT_TEST` из
        окружения и без обрезки суффикса фазы (` (setup)` и т.п.) - в nodeid его
        нет. Вне теста (`TestContext.is_active()` == False) возвращает `unknown`.
        ASCII-only, с MD5-хэшем для уникальности при не-ASCII параметрах.
        """
        if not TestContext.is_active():
            return "unknown"
        node_id = TestContext.current.id
        ascii_part = re.sub(r"[^a-zA-Z0-9_\-]", "_", node_id)
        ascii_part = re.sub(r"_+", "_", ascii_part).strip("_")
        node_hash = hashlib.md5(node_id.encode()).hexdigest()[:8]
        return f"{ascii_part[:80]}_{node_hash}"


@deprecated(
    "set_logger_resolver больше не нужен и ничего не делает: активный Logger "
    "разрешается внутренней логикой DI-контейнера (`CoreServices.logger` через "
    "`Delegate`). Заглушка оставлена как временный слой совместимости - удалите вызов.",
)
def set_logger_resolver(resolver: Callable[[], Logger] | None = None) -> None:
    """No-op-заглушка совместимости: разрешение активного Logger теперь забота
    DI-контейнера, а не глобального резолвера. Ничего не делает."""


class step:  # noqa: N801 - lowercase: используется как декоратор/CM (`@step(...)`, `with step(...)`)
    """Ленивый шаг: резолвит активный `Logger` в момент входа (`with`) или
    вызова обёрнутой функции (декоратор), а не при создании.

    Критично при использовании декоратором на тестовом методе: декоратор
    применяется на импорте, когда активного теста (и его `Logger`) ещё нет.
    Раннее разрешение построило бы `Logger` на импорте - с неверным именем
    (`unknown`, т.к. активного теста ещё нет - `TestContext.is_active()` False) и
    не тем экземпляром. Ленивое разрешение откладывает создание `Step` и `Logger` до
    прогона теста.

    Здесь же живёт РЕЕСТР активного Logger (`resolve`/`current` + protected
    `_set_resolver`): «какой Logger активен» - вопрос композиции, а не самого
    `Logger` (тот - per-test экземпляр), и нужен именно потребителю - `step` и
    опциональным интеграциям. Публичный контракт `step` - только сигнатура
    `(title, level)`; резолвер «абстрактный» - его выставляет DI-контейнер
    (`CoreServicesABC` авто-регистрируется), до этого `resolve()` бросает.
    """

    #: Резолвер активного Logger. Заполняется автоматически: `CoreServicesABC`
    #: в `__init_subclass__` связывает его со своим `logger`-провайдером.
    _resolver: ClassVar[Callable[[], Logger] | None] = None

    @classmethod
    def _set_resolver(cls, resolver: Callable[[], Logger] | None) -> None:
        """Зарегистрировать резолвер активного Logger.

        Protected НАМЕРЕННО: внутренний шов между DI-слоем и `step`, а не
        публичный шаг настройки. Штатный вызов один - авто-регистрация в
        `CoreServicesABC.__init_subclass__` (`di`→`services`, без обратного
        импорта). Publicly объявлять нельзя - иначе выглядит как API, «который
        надо не забыть вызвать»; на деле любой контейнер-наследник регистрируется
        сам. Тесты, подменяющие активный Logger, зовут его напрямую как
        protected."""
        cls._resolver = resolver

    @classmethod
    def resolve(cls) -> Logger:
        """Активный Logger; бросает, если ни один контейнер ещё не объявлен."""
        if cls._resolver is None:
            raise RuntimeError(
                "Активный Logger не зарегистрирован: объявите контейнер-наследник "
                "`CoreServicesABC` (например, `CoreServices`) - он регистрируется сам.",
            )
        return cls._resolver()

    @classmethod
    def current(cls) -> Logger | None:
        """Активный Logger либо None - для опциональных интеграций, которые
        логируют только когда логирование настроено (не бросает, в отличие от
        `resolve()`)."""
        return cls._resolver() if cls._resolver is not None else None

    def __init__(self, title: str, level: LogLevel = LogLevel.NORMAL) -> None:
        self.title = title
        self.level = level
        self._active: Step | None = None

    def __enter__(self) -> Step:
        self._active = step.resolve().step(self.title, level=self.level)
        return self._active.__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        active, self._active = self._active, None
        if active is not None:
            active.__exit__(exc_type, exc_val, exc_tb)

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with step.resolve().step(self.title, level=self.level):
                return func(*args, **kwargs)

        return wrapper
