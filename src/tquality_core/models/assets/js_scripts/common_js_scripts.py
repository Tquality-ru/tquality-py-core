"""Реестр page/global-scope JS-скриптов: исполняются в контексте документа/окна
и не принимают DOM-элемент аргументом. Значения - `Traversable`-пути к
`.js`-файлам в `assets/js_scripts/document`; содержимое читается через
`.read_text()`. Element-scope скрипты - в `CommonElementJSScripts`."""

from tquality_core import PathUtils


class CommonJSScripts:
    __JS_DIR = PathUtils.get_js_scripts_dir() / "document"

    AUTO_ACCEPT_ALERTS = __JS_DIR / "auto_accept_alerts.js"
    CLEAR_HIGHLIGHTS = __JS_DIR / "clear_highlights.js"
    GET_DEVICE_PIXEL_RATIO = __JS_DIR / "get_device_pixel_ratio.js"
    GET_ELEMENT_BY_XPATH = __JS_DIR / "get_element_by_xpath.js"
    GET_ELEMENTS_FROM_POINT = __JS_DIR / "get_elements_from_point.js"
    GET_PSEUDO_ELEMENT_STYLE = __JS_DIR / "get_pseudo_element_style.js"
    IS_PAGE_LOADED = __JS_DIR / "is_page_loaded.js"
    OPEN_IN_NEW_TAB = __JS_DIR / "open_in_new_tab.js"
    OPEN_IN_NEW_WINDOW = __JS_DIR / "open_in_new_window.js"
    OPEN_NEW_TAB = __JS_DIR / "open_new_tab.js"
    OPEN_NEW_WINDOW = __JS_DIR / "open_new_window.js"
    SCROLL_TO_BOTTOM = __JS_DIR / "scroll_to_bottom.js"
    SCROLL_TO_BOTTOM_INFINITE = __JS_DIR / "scroll_to_bottom_infinite.js"
    SCROLL_TO_TOP = __JS_DIR / "scroll_to_top.js"
    SCROLL_WINDOW_BY = __JS_DIR / "scroll_window_by.js"
