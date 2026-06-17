/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];

const event = new MouseEvent('mouseover', {view: window, bubbles: true, cancelable: true});
element.dispatchEvent(event);
