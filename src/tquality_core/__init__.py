from typing import TYPE_CHECKING

from tquality_core.elements._base_by import BaseBy
from tquality_core.elements._base_element import BaseElement
from tquality_core.elements._element_state import (
    ElementState,
    StatePredicate,
    StateSpec,
)
from tquality_core.elements._formattable_element import FormattableElement
from tquality_core.models import (
    BaseConfig,
    JsoncConfigSettingsSource,
    LoggingConfig,
    LogLevelName,
    LogStream,
    WaiterConfig,
)
from tquality_core.pages.base_form import BaseForm
from tquality_core.plugins.per_test_files import (
    find_upwards,
    register_per_test_rebuilder,
)
from tquality_core.services.lazy_elements import LazyElements
from tquality_core.services.logger import (
    Logger,
    LogLevel,
    ScreencastProvider,
    ScreenshotProvider,
    Step,
    StepEnterHook,
    StepExitHook,
    set_logger_resolver,  # ty: ignore[deprecated] - намеренный ре-экспорт deprecated-заглушки
    step,
)
from tquality_core.services.resolved_waiter import ResolvedWaiter
from tquality_core.services.waiter import Waiter, WaitTimeoutError
from tquality_core.services.webdriver_screenshot_provider import (
    WebDriverScreenshotProvider,
)
from tquality_core.services.webm_screencast import WebmScreencastRecorder
from tquality_core.utils.os_utils import OSUtils
from tquality_core.utils.path_utils import PathUtils
from tquality_core.utils.string_utils import StringUtils
from tquality_core.utils.xpath_utils import XPathUtils

__all__ = [
    "BaseBy",
    "BaseConfig",
    "BaseElement",
    "BaseForm",
    "ElementState",
    "FormattableElement",
    "JsoncConfigSettingsSource",
    "LazyElements",
    "Logger",
    "LogLevel",
    "LogLevelName",
    "LogStream",
    "LoggingConfig",
    "OSUtils",
    "PathUtils",
    "ResolvedWaiter",
    "ScreencastProvider",
    "ScreenshotProvider",
    "StatePredicate",
    "StateSpec",
    "Step",
    "StepEnterHook",
    "StepExitHook",
    "StringUtils",
    "Waiter",
    "WaitTimeoutError",
    "WaiterConfig",
    "WebDriverScreenshotProvider",
    "WebmScreencastRecorder",
    "XPathUtils",
    "find_upwards",
    "register_per_test_rebuilder",
    "set_logger_resolver",
    "step",
]

# Опциональный http_client: ленивый ре-экспорт с верхнего уровня, только при
# установленном extra `http_client`. `import tquality_core` остаётся лёгким (без
# requests), а `from tquality_core import BaseClient` работает при наличии extra.
if TYPE_CHECKING:  # для статических чекеров; в рантайме имена даёт __getattr__
    from tquality_core.http_client import (  # noqa: F401  # ре-экспорт верхнего уровня
        ApiResponse,
        BaseClient,
        ContentType,
        Headers,
        ModelType,
        RequestArgsDict,
        Timeout,
        TimeoutHTTPAdapter,
    )

_HTTP_CLIENT_EXPORTS = frozenset(
    {
        "ApiResponse",
        "BaseClient",
        "ContentType",
        "Headers",
        "ModelType",
        "RequestArgsDict",
        "Timeout",
        "TimeoutHTTPAdapter",
    }
)


def __getattr__(name: str) -> object:  # PEP 562
    if name in _HTTP_CLIENT_EXPORTS:
        try:
            import tquality_core.http_client as http_client
        except ImportError as exc:
            raise ImportError(
                f"'{name}' требует extra 'http_client': pip install \"tquality-py-core[http_client]\""
            ) from exc
        return getattr(http_client, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
