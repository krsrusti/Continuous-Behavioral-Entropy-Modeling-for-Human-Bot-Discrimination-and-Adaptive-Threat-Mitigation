/**
 * passive_collector.js
 *
 * Collects passive behavioural telemetry.
 *
 * Privacy:
 *   - NEVER stores e.key
 *   - NEVER stores actual typed characters
 *   - Stores only physical key code + key category
 *
 * Exposes:
 *   window.__tifPassive
 */

(function () {

  'use strict';


  // ─────────────────────────────────────────────────────────────────────────
  // Storage
  // ─────────────────────────────────────────────────────────────────────────

  const events = [];


  // ─────────────────────────────────────────────────────────────────────────
  // Timestamp helper
  // ─────────────────────────────────────────────────────────────────────────

  function stamp(type, payload = {}) {

    events.push({
      type: type,
      ts: performance.now(),
      ...payload
    });

  }


  // ─────────────────────────────────────────────────────────────────────────
  // Key classification
  // ─────────────────────────────────────────────────────────────────────────

  function classifyKey(code) {

    if (code === 'Space') {
      return 'space';
    }

    if (code === 'Backspace') {
      return 'backspace';
    }

    if (
      code === 'Enter' ||
      code === 'NumpadEnter'
    ) {
      return 'enter';
    }

    if (code === 'Tab') {
      return 'tab';
    }

    if (
      code.startsWith('Shift') ||
      code.startsWith('Control') ||
      code.startsWith('Alt') ||
      code.startsWith('Meta')
    ) {
      return 'modifier';
    }

    if (
      code.startsWith('Arrow') ||
      code === 'Home' ||
      code === 'End' ||
      code === 'PageUp' ||
      code === 'PageDown'
    ) {
      return 'navigation';
    }

    if (
      code.startsWith('F') &&
      code.length <= 3
    ) {
      return 'function';
    }

    if (
      code.startsWith('Digit') ||
      code.startsWith('Numpad')
    ) {
      return 'digit';
    }

    if (code.startsWith('Key')) {
      return 'character';
    }

    return 'other';
  }


  // ─────────────────────────────────────────────────────────────────────────
  // Mouse movement
  //
  // Approximately 60 FPS maximum.
  // ─────────────────────────────────────────────────────────────────────────

  let lastMouseTime = 0;


  document.addEventListener(
    'mousemove',
    (e) => {

      const now = performance.now();

      if (
        now - lastMouseTime <
        16
      ) {
        return;
      }

      lastMouseTime = now;


      stamp(
        'mouse_move',
        {
          x: e.clientX,
          y: e.clientY
        }
      );

    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Keyboard
  //
  // IMPORTANT:
  // e.key is NOT stored.
  // ─────────────────────────────────────────────────────────────────────────

  document.addEventListener(
    'keydown',
    (e) => {

      stamp(
        'keydown',
        {
          code: e.code,

          key_category:
            classifyKey(e.code)
        }
      );

    }
  );


  document.addEventListener(
    'keyup',
    (e) => {

      stamp(
        'keyup',
        {
          code: e.code,

          key_category:
            classifyKey(e.code)
        }
      );

    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Scroll
  // ─────────────────────────────────────────────────────────────────────────

  let lastScrollY =
    window.scrollY;


  document.addEventListener(
    'scroll',
    () => {

      const currentY =
        window.scrollY;

      const dy =
        currentY -
        lastScrollY;

      lastScrollY =
        currentY;


      stamp(
        'scroll',
        {
          dy: dy,
          scrollY: currentY
        }
      );

    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Mouse down
  // ─────────────────────────────────────────────────────────────────────────

  document.addEventListener(
    'mousedown',
    (e) => {

      stamp(
        'mousedown',
        {
          x: e.clientX,
          y: e.clientY,

          target:
            e.target?.tagName ||
            null
        }
      );

    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Mouse up
  // ─────────────────────────────────────────────────────────────────────────

  document.addEventListener(
    'mouseup',
    (e) => {

      stamp(
        'mouseup',
        {
          x: e.clientX,
          y: e.clientY
        }
      );

    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Click
  // ─────────────────────────────────────────────────────────────────────────

  document.addEventListener(
    'click',
    (e) => {

      stamp(
        'click',
        {
          x: e.clientX,

          y: e.clientY,

          target:
            e.target?.tagName ||
            null,

          target_id:
            e.target?.id ||
            null
        }
      );

    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Focus
  // ─────────────────────────────────────────────────────────────────────────

  document.addEventListener(
    'focusin',
    (e) => {

      stamp(
        'focus',
        {
          target:
            e.target?.tagName ||
            null,

          target_id:
            e.target?.id ||
            null
        }
      );

    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Blur
  // ─────────────────────────────────────────────────────────────────────────

  document.addEventListener(
    'focusout',
    (e) => {

      stamp(
        'blur',
        {
          target:
            e.target?.tagName ||
            null,

          target_id:
            e.target?.id ||
            null
        }
      );

    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Input
  //
  // We record that an input event happened,
  // but NEVER record the input value.
  // ─────────────────────────────────────────────────────────────────────────

  document.addEventListener(
    'input',
    (e) => {

      stamp(
        'input',
        {
          target:
            e.target?.tagName ||
            null,

          target_id:
            e.target?.id ||
            null
        }
      );

    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Public API
  // ─────────────────────────────────────────────────────────────────────────

  window.__tifPassive = events;


  console.log(
    '[TIF Passive] Collector loaded.'
  );

})();