// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {string} */
const xpath = arguments[0];

/** @type {Node | null} */
return document.evaluate(
    xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null,
).singleNodeValue;
