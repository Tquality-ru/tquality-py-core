// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];

const rect = element.getBoundingClientRect();
const viewportH = window.innerHeight || document.documentElement.clientHeight;
const viewportW = window.innerWidth || document.documentElement.clientWidth;
return rect.top >= 0 && rect.left >= 0
    && rect.bottom <= viewportH && rect.bottom !== 0
    && rect.right <= viewportW && rect.right !== 0;
