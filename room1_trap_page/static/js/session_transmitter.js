/**
 * session_transmitter.js
 * Bundles passive telemetry + probe data into a session object
 * and POSTs to the Room 2 Flask API.
 *
 * Usage (after including all three JS files):
 *   TIFSession.init({ pageType: 'login', apiBase: 'http://localhost:5000' });
 */
const TIFSession = (function () {
  'use strict';

  let config = {};
  const sessionId = crypto.randomUUID();
  const startTime = performance.now();

  function buildPayload() {
    return {
      session_id:     sessionId,
      page_type:      config.pageType || 'unknown',
      start_time:     startTime,
      end_time:       performance.now(),
      passive_events: window.__tifPassive || [],
      probes:         window.__tifProbes  || [],
      label:          null,
      user_agent:     navigator.userAgent,
    };
  }

  async function transmit() {
    const payload = buildPayload();
    try {
      await fetch(`${config.apiBase}/api/session`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
    } catch (err) {
      console.warn('[TIF] Transmit failed:', err);
    }
  }

  // Send on form submit
  function attachFormListeners() {
    document.querySelectorAll('form').forEach((form) => {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        transmit();
      });
    });
  }

  // Best-effort send on page unload
  window.addEventListener('beforeunload', () => {
    const payload = JSON.stringify(buildPayload());
    navigator.sendBeacon(`${config.apiBase}/api/session`, payload);
  });

  function init(cfg) {
    config = cfg || {};
    attachFormListeners();
  }

  return { init, transmit, buildPayload };
})();