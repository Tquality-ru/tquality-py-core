/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];
/** @type {string} */
const border = arguments[1] || '3px solid red';

element.style.border = border;
