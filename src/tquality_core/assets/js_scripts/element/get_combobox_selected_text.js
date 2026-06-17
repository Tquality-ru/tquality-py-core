// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {HTMLSelectElement} */
const element = arguments[0];

/** @type {string} */
return element.options[element.selectedIndex].text;
