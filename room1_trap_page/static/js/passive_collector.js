/**
 * passive_collector.js
 * Collects mouse, keyboard, scroll, and click telemetry passively.
 *
 * Privacy rules:
 *   - keydown/keyup: NEVER store the actual key character (e.key)
 *   - Store only: code (physical key), key_category (what kind of key), timing
 *
 * Exposes: window.__tifPassive — array of timestamped events
 */
(function () {
  'use strict';

  const events = [];

  function stamp(type, payload) {
    events.push({ type, ts: performance.now(), ...payload });
  }

  // ── Key category classifier ───────────────────────────────────────────────
  // Groups physical key into category WITHOUT storing what was typed.

  function classifyKey(code, key) {
    if (code === 'Space')                          return 'space';
    if (code === 'Backspace')                      return 'backspace';
    if (code === 'Enter' || code === 'NumpadEnter') return 'enter';
    if (code === 'Tab')                            return 'tab';
    if (code.startsWith('Shift') ||
        code.startsWith('Control') ||
        code.startsWith('Alt') ||
        code.startsWith('Meta'))                   return 'modifier';
    if (code.startsWith('Arrow') ||
        code === 'Home' || code === 'End' ||
        code === 'PageUp' || code === 'PageDown')  return 'navigation';
    if (code.startsWith('F') && code.length <= 3) return 'function';
    if (code.startsWith('Digit') ||
        code.startsWith('Numpad'))                 return 'digit';
    if (code.startsWith('Key'))                    return 'character';
    return 'other';
  }

  // ── Mouse trajectory (throttled to ~60fps) ────────────────────────────────

  let lastMouse = 0;
  document.addEventListener('mousemove', (e) => {
    const now = performance.now();
    if (now - lastMouse < 16) return;
    lastMouse = now;
    stamp('mouse_move', { x: e.clientX, y: e.clientY });
  });

  // ── Keyboard timing ───────────────────────────────────────────────────────
  // code    = physical key position (KeyA, ShiftLeft, Digit1...)
  // key_category = what kind of key (character, digit, modifier...)
  // key     = NEVER stored

  document.addEventListener('keydown', (e) => {
    stamp('keydown', {
      code:         e.code,
      key_category: classifyKey(e.code, e.key),
    });
  });

  document.addEventListener('keyup', (e) => {
    stamp('keyup', {
      code:         e.code,
      key_category: classifyKey(e.code, e.key),
    });
  });

  // ── Scroll ────────────────────────────────────────────────────────────────

  let lastScrollY = window.scrollY;
  document.addEventListener('scroll', () => {
    const dy = window.scrollY - lastScrollY;
    lastScrollY = window.scrollY;
    stamp('scroll', { dy, scrollY: window.scrollY });
  });

  // ── Mouse clicks ──────────────────────────────────────────────────────────

  document.addEventListener('mousedown', (e) => stamp('mousedown', {
    x: e.clientX, y: e.clientY,
    target: e.target.tagName,
  }));

  document.addEventListener('mouseup', (e) => stamp('mouseup', {
    x: e.clientX, y: e.clientY,
  }));

  document.addEventListener('click', (e) => stamp('click', {
    x:      e.clientX,
    y:      e.clientY,
    target: e.target.tagName,
    target_id: e.target.id || null,
  }));

  // ── Focus / blur ──────────────────────────────────────────────────────────

  document.addEventListener('focusin', (e) => stamp('focus', {
    target:    e.target.tagName,
    target_id: e.target.id || null,
  }));

  document.addEventListener('focusout', (e) => stamp('blur', {
    target:    e.target.tagName,
    target_id: e.target.id || null,
  }));

  window.__tifPassive = events;
})();