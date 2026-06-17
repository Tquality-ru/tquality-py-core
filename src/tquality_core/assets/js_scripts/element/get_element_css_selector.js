// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];

/**
 * @param {Element} el
 * @returns {Element | null}
 */
function previousElementSibling(el) {
    if (el.previousElementSibling !== undefined) {
        return el.previousElementSibling;
    }
    let node = el;
    while ((node = node.previousSibling)) {
        if (node.nodeType === Node.ELEMENT_NODE) {
            return node;
        }
    }
    return null;
}

/**
 * @param {Element} el
 * @returns {string}
 */
function getCssPath(el) {
    if (!(el instanceof HTMLElement)) {
        return '';
    }
    /** @type {string[]} */
    const path = [];
    while (el.nodeType === Node.ELEMENT_NODE) {
        let selector = el.nodeName;
        if (el.id) {
            selector += '#' + el.id;
        } else {
            let sibling = el;
            /** @type {string[]} */
            const siblingSelectors = [];
            while (sibling !== null && sibling.nodeType === Node.ELEMENT_NODE) {
                siblingSelectors.unshift(sibling.nodeName);
                sibling = previousElementSibling(sibling);
            }
            if (siblingSelectors[0] !== 'HTML') {
                siblingSelectors[0] = siblingSelectors[0] + ':first-child';
            }
            selector = siblingSelectors.join(' + ');
        }
        path.unshift(selector);
        el = el.parentNode;
    }
    return path.join(' > ');
}

/** @type {string} */
return getCssPath(element);
