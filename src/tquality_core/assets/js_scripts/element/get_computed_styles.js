// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];

const style = window.getComputedStyle(element);
/** @type {Object<string, string>} */
const result = {};
for (let i = 0; i < style.length; i++) {
    const name = style[i];
    result[name] = style.getPropertyValue(name);
}
return result;
