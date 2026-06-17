// noinspection JSAnnotator -- тело скрипта - функция в execute_script, return допустим
/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];

/**
 * @param {Element} el
 * @returns {string}
 */
function getXpath(el) {
    if (el.tagName === 'HTML') {
        return '/html';
    }
    if (el === document.body) {
        return '/html/body';
    }
    let position = 0;
    const siblings = el.parentNode.childNodes;
    for (let i = 0; i < siblings.length; i++) {
        const sibling = siblings[i];
        if (sibling === el) {
            return `${getXpath(el.parentNode)}/${el.tagName}[${position + 1}]`;
        }
        if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === el.tagName) {
            position++;
        }
    }
    return '';
}

/** @type {string} */
return getXpath(element);
