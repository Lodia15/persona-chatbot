import { TEXTAREA_MAX_HEIGHT_PX } from "./config.js";

/**
 * Grow textarea with content up to maxHeightPx.
 * @param {HTMLTextAreaElement} textarea
 */
export function bindAutoResize(textarea, maxHeightPx = TEXTAREA_MAX_HEIGHT_PX) {
  const resize = () => {
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeightPx)}px`;
  };
  textarea.addEventListener("input", resize);
  return resize;
}

/**
 * Enter submits form; Shift+Enter newline.
 * @param {HTMLTextAreaElement} textarea
 * @param {HTMLFormElement} form
 */
export function bindEnterSubmit(textarea, form) {
  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });
}
