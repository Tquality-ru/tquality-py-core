/* global arguments */

/** @type {HTMLSelectElement} */
const element = arguments[0];
/** @type {string} */
const text = arguments[1];

for (let i = 0; i < element.options.length; i++) {
    if (element.options[i].text === text) {
        element.options[i].selected = true;
    }
}
element.dispatchEvent(new Event('change', {bubbles: true}));
