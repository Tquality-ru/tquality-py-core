/* global arguments */

/** @type {HTMLElement} */
const element = arguments[0];
/** @type {string} */
const value = arguments[1];

// Ищем нативный сеттер `value` ВВЕРХ по цепочке прототипов (а не на самом
// элементе): React/Vue переопределяют `value` на экземпляре, тогда как на
// прототипе (`HTMLInputElement`/`HTMLTextAreaElement`/`HTMLSelectElement`)
// остаётся родной браузерный сеттер. Берём его и зовём через `.call` - тип
// определяется по самому элементу, поэтому `element_type` снаружи не нужен.
function nativeValueSetter(el) {
    let proto = Object.getPrototypeOf(el);
    while (proto) {
        const descriptor = Object.getOwnPropertyDescriptor(proto, 'value');
        if (descriptor && descriptor.set) {
            return descriptor.set;
        }
        proto = Object.getPrototypeOf(proto);
    }
    return null;
}

const setter = nativeValueSetter(element);
if (setter) {
    setter.call(element, value);   // input / textarea / select - React/Vue-safe
} else if (element.isContentEditable) {
    element.textContent = value;   // contenteditable (div и т.п.)
} else {
    element.value = value;         // запасной вариант
}

// `input` + `change` со всплытием - чтобы и текстовые контролы, и select'ы,
// и слушатели/фреймворки отреагировали на изменение.
element.dispatchEvent(new Event('input', {bubbles: true}));
element.dispatchEvent(new Event('change', {bubbles: true}));
