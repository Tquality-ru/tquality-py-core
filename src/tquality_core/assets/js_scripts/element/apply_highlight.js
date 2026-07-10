/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];
/** @type {string} */
const outline = arguments[1] || '3px solid red';

// Пометить элемент маркером: снятие идёт document-wide по нему
// (см. clear_highlights.js), поэтому переживает навигацию/перерендер.
element.setAttribute('data-tq-highlight', '1');

// Сохранить прежний inline-`outline`, чтобы clear_highlights мог его вернуть.
element.__tqOutline = element.style.getPropertyValue('outline');
element.__tqOutlinePrio = element.style.getPropertyPriority('outline');
element.__tqOffset = element.style.getPropertyValue('outline-offset');
element.__tqOffsetPrio = element.style.getPropertyPriority('outline-offset');

// `!important`: сайты нередко задают собственный `outline` (в т.ч. с
// `!important`) на inputs и ссылках, и без приоритета рамка рендерится
// невидимой. `outline` (а не `border`) не влияет на layout элемента.
element.style.setProperty('outline', outline, 'important');
element.style.setProperty('outline-offset', '-1px', 'important');
