/* global document */

// Снятие идёт document-wide по маркеру `data-tq-highlight`, а не по
// конкретной ссылке на элемент: устаревший после навигации/перерендера
// элемент просто не находится, а не роняет ошибку.
const marked = document.querySelectorAll('[data-tq-highlight]');
for (let i = 0; i < marked.length; i++) {
    /** @type {HTMLElement} */
    const element = marked[i];
    element.style.removeProperty('outline');
    element.style.removeProperty('outline-offset');
    if (element.__tqOutline) {
        element.style.setProperty('outline', element.__tqOutline, element.__tqOutlinePrio || '');
    }
    if (element.__tqOffset) {
        element.style.setProperty('outline-offset', element.__tqOffset, element.__tqOffsetPrio || '');
    }
    delete element.__tqOutline;
    delete element.__tqOutlinePrio;
    delete element.__tqOffset;
    delete element.__tqOffsetPrio;
    element.removeAttribute('data-tq-highlight');
}
