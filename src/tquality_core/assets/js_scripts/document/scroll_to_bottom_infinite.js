/* global arguments */

/** @type {number} */
const quietPeriod = arguments[0];
/** @type {number | null} */
const timeoutMs = arguments[1];
/** @type {(result: {height: number, timedOut: boolean}) => void} */
const done = arguments[arguments.length - 1];

let quietTimer, deadlineTimer;
let timedOut = false;

const observer = new MutationObserver(() => {
  clearTimeout(quietTimer);
  window.scrollTo(0, document.body.scrollHeight);
  quietTimer = setTimeout(finish, quietPeriod);
});

function finish() {
  clearTimeout(quietTimer);
  clearTimeout(deadlineTimer);
  observer.disconnect();
  done({ height: document.body.scrollHeight, timedOut });
}

if (timeoutMs != null) {
  deadlineTimer = setTimeout(() => {
    timedOut = true;
    finish();
  }, timeoutMs);
}

observer.observe(document.body, { childList: true, subtree: true });
window.scrollTo(0, document.body.scrollHeight);
