/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];

element.dispatchEvent(new Event('blur', {bubbles: true}));
if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur();
}
