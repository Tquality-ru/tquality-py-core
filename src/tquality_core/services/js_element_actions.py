from collections.abc import Callable
from typing import Any, Literal

from tquality_core.models.assets.js_scripts.common_element_js_scripts import (
    CommonElementJSScripts,
)
from tquality_core.services.base_js_actions import BaseJSActions


class JsElementActions(BaseJSActions):
    """Element-scope JS-действия: исполняют скрипты `CommonElementJSScripts`,
    подставляя текущий элемент первым аргументом (`element_getter`). Доп.
    аргументы метода уходят после элемента (`arguments[1]`, `arguments[2]`, ...).
    Page/global-scope действия - в `JSActions`."""

    def __init__(
        self,
        js_executor: Callable[..., Any],
        js_async_executor: Callable[..., Any],
        element_getter: Callable[..., Any],
    ) -> None:
        super().__init__(js_executor, js_async_executor)
        self._get_element = element_getter

    def _prefix_args(self) -> tuple[Any, ...]:
        return (self._get_element(),)

    # ── взаимодействие ───────────────────────────────────────────────────────
    def click(self) -> None:
        self.execute_script(CommonElementJSScripts.ELEMENT_CLICK)

    def hover(self) -> None:
        self.execute_script(CommonElementJSScripts.MOUSE_HOVER)

    def set_focus(self) -> None:
        self.execute_script(CommonElementJSScripts.SET_FOCUS)

    def blur(self) -> None:
        """Снять фокус: эмитит `blur` на элементе и зовёт `blur()` у активного."""
        self.execute_script(CommonElementJSScripts.BLUR)

    def highlight(self, border: str = "3px solid red") -> None:
        """Подсветить элемент CSS-рамкой (по умолчанию красной)."""
        self.execute_script(CommonElementJSScripts.BORDER_ELEMENT, border)

    # ── ввод / атрибуты ──────────────────────────────────────────────────────
    def set_value(self, value: str) -> None:
        """Проставить значение надёжно: берёт нативный сеттер `value` с прототипа
        элемента (обходит переопределение React/Vue), на `contenteditable` пишет
        `textContent`, иначе - запасное присваивание; затем эмитит `input` и
        `change`. Тип элемента определяется в JS - снаружи ничего не нужно."""
        self.execute_script(CommonElementJSScripts.SET_VALUE, value)

    def set_inner_html(self, html: str) -> None:
        self.execute_script(CommonElementJSScripts.SET_INNER_HTML, html)

    def set_attribute(self, name: str, value: str) -> None:
        self.execute_script(CommonElementJSScripts.SET_ATTRIBUTE, name, value)

    def select_combobox_value_by_text(self, text: str) -> None:
        self.execute_script(CommonElementJSScripts.SELECT_COMBOBOX_VALUE_BY_TEXT, text)

    # ── чтение ───────────────────────────────────────────────────────────────
    def get_text(self) -> str:
        return str(self.execute_script(CommonElementJSScripts.GET_ELEMENT_TEXT))

    def get_first_child_text(self) -> str:
        return str(self.execute_script(CommonElementJSScripts.GET_TEXT_FIRST_CHILD))

    def get_xpath(self) -> str:
        return str(self.execute_script(CommonElementJSScripts.GET_ELEMENT_XPATH))

    def get_css_selector(self) -> str:
        return str(self.execute_script(CommonElementJSScripts.GET_ELEMENT_CSS_SELECTOR))

    def get_checkbox_state(self) -> bool:
        return bool(self.execute_script(CommonElementJSScripts.GET_CHECKBOX_STATE))

    def get_computed_style(self, property_name: str) -> str:
        """Вычисленное значение CSS-свойства (пустая строка, если его нет)."""
        return str(
            self.execute_script(CommonElementJSScripts.GET_COMPUTED_STYLE, property_name),
        )

    def get_computed_styles(self) -> dict[str, str]:
        """Все вычисленные CSS-свойства элемента одним запросом (выгоднее, чем
        дёргать `get_computed_style` в цикле)."""
        styles = self.execute_script(CommonElementJSScripts.GET_COMPUTED_STYLES)
        return {str(name): str(value) for name, value in styles.items()}

    def get_combobox_selected_text(self) -> str:
        return str(
            self.execute_script(CommonElementJSScripts.GET_COMBOBOX_SELECTED_TEXT),
        )

    def get_combobox_options(self) -> list[str]:
        """Тексты всех опций combobox - пара к `select_combobox_value_by_text`."""
        return list(self.execute_script(CommonElementJSScripts.GET_COMBOBOX_OPTIONS))

    def is_on_screen(self) -> bool:
        return bool(self.execute_script(CommonElementJSScripts.ELEMENT_IS_ON_SCREEN))

    def get_viewport_coordinates(self) -> tuple[float, float]:
        """`(left, top)` элемента относительно вьюпорта."""
        coords = self.execute_script(CommonElementJSScripts.GET_VIEWPORT_COORDINATES)
        return (float(coords[0]), float(coords[1]))

    def expand_shadow_root(self) -> Any:
        """Сырой `ShadowRoot` хост-элемента (или `None`)."""
        return self.execute_script(CommonElementJSScripts.EXPAND_SHADOW_ROOT)

    # ── скролл к элементу ────────────────────────────────────────────────────
    def scroll_into_view(
        self,
        block: Literal["start", "center", "end", "nearest"] = "center",
        behavior: Literal["instant", "smooth"] = "instant",
    ) -> None:
        self.execute_script(CommonElementJSScripts.SCROLL_INTO_VIEW, block, behavior)

    def scroll_to_center(self) -> None:
        self.execute_script(CommonElementJSScripts.SCROLL_TO_ELEMENT_CENTER)

    def scroll_by(self, x: float, y: float) -> None:
        self.execute_script(CommonElementJSScripts.SCROLL_ELEMENT_BY, x, y)
