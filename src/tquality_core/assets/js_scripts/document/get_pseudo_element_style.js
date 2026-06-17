// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {string} */
const selector = arguments[0];
/** @type {string} */
const pseudo = arguments[1];
/** @type {string} */
const property = arguments[2];

/** @type {Element | null} */
const element = document.querySelector(selector);
if (!element) {
    return null;
}
/** @type {string} */
return window.getComputedStyle(element, pseudo).getPropertyValue(property);
