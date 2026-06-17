// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];
/** @type {string} */
const property = arguments[1];

/** @type {string} */
return window.getComputedStyle(element).getPropertyValue(property);
