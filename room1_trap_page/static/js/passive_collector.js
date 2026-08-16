/**
 * passive_collector.js
 * Collects mouse, keyboard, scroll, and click telemetry passively.
 * Exposes: window.__tifPassive — array of timestamped events.
 */
(function () {
  'use strict';

  const events = [];

  function stamp(type, payload) {
    events.push({ type, ts: performance.now(), ...payload });
  }

  // Mouse trajectory (throttled to ~60fps)
  let lastMouse = 0;
  document.addEventListener('mousemove', (e) => {
    const now = performance.now();
    if (now - lastMouse < 16) return;
    lastMouse = now;
    stamp('mouse_move', { x: e.clientX, y: e.clientY });
  });

  // Keystroke timing
  document.addEventListener('keydown', (e) => stamp('keydown', { key: e.key, code: e.code }));
  document.addEventListener('keyup',   (e) => stamp('keyup',   { key: e.key, code: e.code }));

  // Scroll velocity
  let lastScrollY = window.scrollY;
  document.addEventListener('scroll', () => {
    const dy = window.scrollY - lastScrollY;
    lastScrollY = window.scrollY;
    stamp('scroll', { dy, scrollY: window.scrollY });
  });

  // Click timing
  document.addEventListener('mousedown', (e) => stamp('mousedown', { x: e.clientX, y: e.clientY, target: e.target.tagName }));
  document.addEventListener('mouseup',   (e) => stamp('mouseup',   { x: e.clientX, y: e.clientY }));
  document.addEventListener('click',     (e) => stamp('click',     { x: e.clientX, y: e.clientY, target: e.target.tagName }));

  // Focus / blur on inputs (hesitation signals)
  document.addEventListener('focusin',  (e) => stamp('focus', { target: e.target.id || e.target.tagName }));
  document.addEventListener('focusout', (e) => stamp('blur',  { target: e.target.id || e.target.tagName }));

  window.__tifPassive = events;
})();