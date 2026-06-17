// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {number} */
const x = arguments[0];
/** @type {number} */
const y = arguments[1];

/** @type {Element[]} */
return document.elementsFromPoint(x, y);
