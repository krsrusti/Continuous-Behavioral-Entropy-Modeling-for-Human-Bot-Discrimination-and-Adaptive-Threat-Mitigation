/**
 * session_transmitter.js
 * Bundles passive telemetry + probe data and POSTs to the Flask API.
 *
 * Usage:
 *   // Step 1 — researcher starts an experiment on the backend first:
 *   // POST /api/experiment/start → { experiment_id, participant_id, probe_enabled, task_id }
 *
 *   // Step 2 — init with the response:
 *   TIFSession.init({
 *     pageType:      'login',
 *     apiBase:       'http://localhost:5000',
 *     experimentId:  'exp_abc123',
 *     participantId: 'p_xyz789',
 *     taskId:        'login',
 *     probeEnabled:  true,    // from experiment/start response — NOT set by researcher here
 *   });
 *
 * What is sent to the backend:
 *   session_id, page_type, task_id, experiment_id, participant_id
 *   probe_enabled, start_time, end_time
 *   passive_events, probes
 *   user_agent  (metadata only — never used as ML feature)
 *
 * What is NEVER sent from the browser:
 *   agent_class  — always assigned server-side via experiment lookup
 *   label        — always assigned server-side
 *   actual key characters — stripped in passive_collector.js
 */
const TIFSession = (function () {
  'use strict';

  let config    = {};
  let sessionId = crypto.randomUUID();
  const startTime = performance.now();
  let transmitted = false;

  // ── Init ──────────────────────────────────────────────────────────────────

  function init(cfg) {
    config = cfg || {};

    // Tell micro_probe.js whether probes are enabled
    // probeEnabled comes from the experiment/start response — not hardcoded
    if (typeof window.__tifProbeSetEnabled === 'function') {
      window.__tifProbeSetEnabled(!!config.probeEnabled);
    }

    // Use server-assigned session_id if provided
    if (config.sessionId) {
      sessionId = config.sessionId;
    }

    attachFormListeners();
    attachUnloadListener();
  }

  // ── Payload builder ───────────────────────────────────────────────────────

  function buildPayload() {
    return {
      // ── Identity ──────────────────────────────────────────────────────────
      session_id:     sessionId,

      // ── Experiment metadata ───────────────────────────────────────────────
      experiment_id:  config.experimentId  || null,
      participant_id: config.participantId || null,
      task_id:        config.taskId        || config.pageType || 'unknown',
      probe_enabled:  !!config.probeEnabled,

      // ── Page info ─────────────────────────────────────────────────────────
      page_type:      config.pageType || 'unknown',

      // ── Timing ───────────────────────────────────────────────────────────
      start_time:     startTime,
      end_time:       performance.now(),

      // ── Telemetry ─────────────────────────────────────────────────────────
      passive_events: window.__tifPassive || [],
      probes:         window.__tifProbes  || [],

      // ── Metadata (never used as ML feature) ───────────────────────────────
      user_agent:     navigator.userAgent,

      // ── These are NEVER set from the browser ──────────────────────────────
      // agent_class: undefined   ← set server-side from experiment lookup
      // label:       undefined   ← set server-side from experiment lookup
    };
  }

  // ── Transmit ──────────────────────────────────────────────────────────────

  async function transmit() {
    const payload = buildPayload();

    try {
      const res = await fetch(`${config.apiBase}/api/session`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.warn('[TIF] Session rejected:', err);
        return null;
      }

      transmitted = true;
      const data = await res.json();
      return data;

    } catch (err) {
      console.warn('[TIF] Transmit failed:', err);
      return null;
    }
  }

  // ── Form listeners ────────────────────────────────────────────────────────

  function attachFormListeners() {
    document.querySelectorAll('form').forEach((form) => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await transmit();
      });
    });
  }

  // ── Unload listener ───────────────────────────────────────────────────────
  // sendBeacon is best-effort — fires even if page is closing.
  // Only fires if not already transmitted via form submit.

  function attachUnloadListener() {
    window.addEventListener('beforeunload', () => {
      if (transmitted) return;
      const payload = JSON.stringify(buildPayload());
      navigator.sendBeacon(
        `${config.apiBase}/api/session`,
        new Blob([payload], { type: 'application/json' })
      );
    });
  }

  // ── Public API ────────────────────────────────────────────────────────────

  return {
    init,
    transmit,
    buildPayload,
    getSessionId: () => sessionId,
  };

})();