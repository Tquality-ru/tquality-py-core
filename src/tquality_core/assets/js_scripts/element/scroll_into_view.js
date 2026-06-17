/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];
/** @type {ScrollLogicalPosition} */
const block = arguments[1];
/** @type {ScrollBehavior} */
const behavior = arguments[2];

element.scrollIntoView({block: block, behavior: behavior});