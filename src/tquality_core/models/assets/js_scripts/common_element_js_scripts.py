"""Реестр element-scope JS-скриптов: первым аргументом принимают DOM-элемент.
Значения - `Traversable`-пути к `.js`-файлам в `assets/js_scripts`; содержимое
читается через `.read_text()`. Page/global-scope скрипты - в `CommonJSScripts`."""
from tquality_core import PathUtils


class CommonElementJSScripts:
    __JS_DIR = PathUtils.get_js_scripts_dir() / "element"

    APPLY_HIGHLIGHT = __JS_DIR / "apply_highlight.js"
    BLUR = __JS_DIR / "blur.js"
    ELEMENT_CLICK = __JS_DIR / "element_click.js"
    ELEMENT_IS_ON_SCREEN = __JS_DIR / "element_is_on_screen.js"
    EXPAND_SHADOW_ROOT = __JS_DIR / "expand_shadow_root.js"
    GET_CHECKBOX_STATE = __JS_DIR / "get_checkbox_state.js"
    GET_COMBOBOX_OPTIONS = __JS_DIR / "get_combobox_options.js"
    GET_COMBOBOX_SELECTED_TEXT = __JS_DIR / "get_combobox_selected_text.js"
    GET_COMPUTED_STYLE = __JS_DIR / "get_computed_style.js"
    GET_COMPUTED_STYLES = __JS_DIR / "get_computed_styles.js"
    GET_ELEMENT_CSS_SELECTOR = __JS_DIR / "get_element_css_selector.js"
    GET_ELEMENT_TEXT = __JS_DIR / "get_element_text.js"
    GET_ELEMENT_XPATH = __JS_DIR / "get_element_xpath.js"
    GET_TEXT_FIRST_CHILD = __JS_DIR / "get_text_first_child.js"
    GET_VIEWPORT_COORDINATES = __JS_DIR / "get_viewport_coordinates.js"
    MOUSE_HOVER = __JS_DIR / "mouse_hover.js"
    SCROLL_ELEMENT_BY = __JS_DIR / "scroll_element_by.js"
    SCROLL_INTO_VIEW = __JS_DIR / "scroll_into_view.js"
    SCROLL_TO_ELEMENT_CENTER = __JS_DIR / "scroll_to_element_center.js"
    SELECT_COMBOBOX_VALUE_BY_TEXT = __JS_DIR / "select_combobox_value_by_text.js"
    SET_ATTRIBUTE = __JS_DIR / "set_attribute.js"
    SET_FOCUS = __JS_DIR / "set_focus.js"
    SET_INNER_HTML = __JS_DIR / "set_inner_html.js"
    SET_VALUE = __JS_DIR / "set_value.js"
