from collections.abc import Callable
from typing import Any, Literal

from tquality_core.models.assets.js_scripts.common_js_scripts import CommonJSScripts
from tquality_core.models.config import BaseConfig
from tquality_core.services.base_js_actions import BaseJSActions

#: CSS-псевдоэлемент для `get_pseudo_element_style` (второй аргумент
#: `getComputedStyle`).
PseudoElement = Literal[
    "::before",
    "::after",
    "::marker",
    "::placeholder",
    "::first-line",
    "::first-letter",
    "::selection",
    "::backdrop",
]


class JSActions(BaseJSActions):
    """Page/global-scope JS-действия: исполняют скрипты `CommonJSScripts`.
    Элемент первым аргументом не принимают. Element-scope действия -
    в `JsElementActions`."""

    def __init__(
        self,
        js_executor: Callable[..., Any],
        js_async_executor: Callable[..., Any],
        config: BaseConfig,
    ) -> None:
        super().__init__(js_executor, js_async_executor)
        self._config = config

    # ── alerts / page state ──────────────────────────────────────────────────
    def auto_accept_alerts(self) -> None:
        """Подменить `confirm`/`alert`/`prompt`, чтобы они авто-подтверждались."""
        self.execute_script(CommonJSScripts.AUTO_ACCEPT_ALERTS)

    def is_page_loaded(self) -> bool:
        return bool(self.execute_script(CommonJSScripts.IS_PAGE_LOADED))

    def get_device_pixel_ratio(self) -> float:
        return float(self.execute_script(CommonJSScripts.GET_DEVICE_PIXEL_RATIO))

    # ── поиск элементов (возвращают сырые web-элементы) ──────────────────────
    def get_element_by_xpath(self, xpath: str) -> Any:
        return self.execute_script(CommonJSScripts.GET_ELEMENT_BY_XPATH, xpath)

    def get_elements_from_point(self, x: float, y: float) -> list[Any]:
        return list(self.execute_script(CommonJSScripts.GET_ELEMENTS_FROM_POINT, x, y))

    def get_pseudo_element_style(
        self, selector: str, pseudo: PseudoElement, property_name: str,
    ) -> str | None:
        """Вычисленный стиль псевдоэлемента (`::before` и т.п.) у первого
        элемента под `selector`; `None`, если элемент не найден."""
        result = self.execute_script(
            CommonJSScripts.GET_PSEUDO_ELEMENT_STYLE, selector, pseudo, property_name,
        )
        return None if result is None else str(result)

    # ── вкладки / окна ───────────────────────────────────────────────────────
    def open_in_new_tab(self, url: str) -> None:
        self.execute_script(CommonJSScripts.OPEN_IN_NEW_TAB, url)

    def open_in_new_window(self, url: str) -> None:
        self.execute_script(CommonJSScripts.OPEN_IN_NEW_WINDOW, url)

    def open_new_tab(self) -> None:
        self.execute_script(CommonJSScripts.OPEN_NEW_TAB)

    def open_new_window(self) -> None:
        self.execute_script(CommonJSScripts.OPEN_NEW_WINDOW)

    # ── скролл страницы ──────────────────────────────────────────────────────
    def scroll_to_bottom(self) -> None:
        self.execute_script(CommonJSScripts.SCROLL_TO_BOTTOM)

    def scroll_to_top(self) -> None:
        self.execute_script(CommonJSScripts.SCROLL_TO_TOP)

    def scroll_window_by(self, x: float, y: float) -> None:
        self.execute_script(CommonJSScripts.SCROLL_WINDOW_BY, x, y)

    def scroll_to_bottom_infinite(
        self, timeout: float | None = None, polling_interval: float | None = None,
    ) -> None:
        """Доскроллить «бесконечную» ленту до конца: скроллит вниз и ждёт, пока
        DOM не перестанет меняться `polling_interval` секунд (или до `timeout`).

        `timeout` / `polling_interval` - в секундах (как `config.waiter.*`);
        скрипту передаются в миллисекундах в порядке `(quietPeriod, timeoutMs)`.
        Async-executor дописывает callback завершения последним аргументом."""
        timeout = timeout if timeout is not None else self._config.waiter.timeout
        polling_interval = (
            polling_interval if polling_interval is not None
            else self._config.waiter.poll_interval
        )
        self.execute_async_script(
            CommonJSScripts.SCROLL_TO_BOTTOM_INFINITE,
            polling_interval * 1000,  # quietPeriod (мс)
            timeout * 1000,           # timeoutMs (мс)
        )
