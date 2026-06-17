/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];

const viewportHeight = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
const elementTop = element.getBoundingClientRect().top;
window.scrollBy(0, elementTop - (viewportHeight / 2));
