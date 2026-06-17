// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];

const rect = element.getBoundingClientRect();
/** @type {[number, number]} */
return [rect.left, rect.top];
