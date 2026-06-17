// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];

/** @type {ShadowRoot | null} */
return element.shadowRoot;
