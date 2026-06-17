/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];
/** @type {string} */
const name = arguments[1];
/** @type {string} */
const value = arguments[2];

element.setAttribute(name, value);
