// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {HTMLSelectElement} */
const element = arguments[0];

/** @type {string[]} */
const texts = [];
for (let i = 0; i < element.options.length; i++) {
    texts.push(element.options[i].text);
}
return texts;
