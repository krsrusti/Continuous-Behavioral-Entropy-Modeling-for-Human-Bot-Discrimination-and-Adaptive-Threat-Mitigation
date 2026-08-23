/**
 * micro_probe.js — THE NOVEL PART: Active Micro-Probe System.
 *
 * Behaviour:
 *   - If probeEnabled = false: does nothing. No DOM mutations. No probes recorded.
 *   - If probeEnabled = true:
 *       Every 3-7s fires an imperceptible DOM mutation (1px shift of hidden div).
 *       Records T1 (probe fired).
 *       Waits for next user interaction to record T2.
 *       If no T2 within 5s: marks probe as abandoned.
 *
 * Each probe record contains:
 *   probeId          — sequential ID
 *   t1               — timestamp when probe fired (performance.now())
 *   t2               — timestamp of next interaction (null if abandoned)
 *   delta            — T2 - T1 in ms (null if abandoned)
 *   source           — event type that triggered T2 (click/keydown/mousemove/etc)
 *   response_target  — element ID or tag that was interacted with
 *   pre_probe_n      — passive events in 2s before T1
 *   post_probe_n     — passive events in 2s after T2 (filled after T2 + 2s)
 *   behavioral_change — post_probe_n - pre_probe_n
 *   idle_before      — true if no passive events in 3s before T1
 *   abandoned        — true if no T2 recorded within 5s
 *
 * Exposes: window.__tifProbes
 * Reads:   window.__tifPassive (must be loaded before this script)
 */
(function () {
  'use strict';

  // ── Config ────────────────────────────────────────────────────────────────
  // probeEnabled is set by TIFSession.init() via window.__tifProbeEnabled.
  // Default false — probe does nothing until explicitly enabled.

  let probeEnabled  = false;
  const probes      = [];
  let probeCounter  = 0;
  let pendingProbe  = null;
  let abandonTimer  = null;

  // ── Ghost element ─────────────────────────────────────────────────────────

  const ghost = document.createElement('div');
  Object.assign(ghost.style, {
    position:      'fixed',
    width:         '1px',
    height:        '1px',
    opacity:       '0',
    pointerEvents: 'none',
    top:           '-9999px',
    left:          '-9999px',
    zIndex:        '-1',
  });
  ghost.setAttribute('aria-hidden', 'true');
  document.body.appendChild(ghost);

  // ── Helpers ───────────────────────────────────────────────────────────────

  function getPassiveEvents() {
    return window.__tifPassive || [];
  }

  function countEventsInWindow(centerTs, windowMs) {
    const events = getPassiveEvents();
    const from   = centerTs - windowMs;
    const to     = centerTs + windowMs;
    return events.filter(e => e.ts >= from && e.ts <= to).length;
  }

  function wasIdleBefore(t1, idleWindowMs) {
    const events = getPassiveEvents();
    const from   = t1 - idleWindowMs;
    return !events.some(e => e.ts >= from && e.ts < t1);
  }

  function getResponseTarget(event) {
    if (!event || !event.target) return null;
    const el = event.target;
    // Prefer ID, then name, then tag
    if (el.id)   return el.id;
    if (el.name) return el.name;
    return el.tagName ? el.tagName.toLowerCase() : null;
  }

  // ── Probe lifecycle ───────────────────────────────────────────────────────

  function fireProbe() {
    if (!probeEnabled) {
      scheduleNext();
      return;
    }

    const probeId = ++probeCounter;
    const t1      = performance.now();

    // Close any previously abandoned probe
    if (pendingProbe && pendingProbe.t2 === null) {
      pendingProbe.abandoned = true;
      pendingProbe.delta     = null;
      pendingProbe = null;
    }

    // Clear any existing abandon timer
    if (abandonTimer) {
      clearTimeout(abandonTimer);
      abandonTimer = null;
    }

    // Imperceptible DOM mutation — alternates top by 1px
    ghost.style.top = (probeCounter % 2 === 0) ? '-9999px' : '-9998px';

    // Count passive events in 2s before T1
    const pre_probe_n = countEventsInWindow(t1, 2000);

    // Was user idle in 3s before probe?
    const idle_before = wasIdleBefore(t1, 3000);

    const probe = {
      probeId,
      t1,
      t2:                null,
      delta:             null,
      source:            null,
      response_target:   null,
      pre_probe_n,
      post_probe_n:      null,   // filled 2s after T2
      behavioral_change: null,   // filled 2s after T2
      idle_before,
      abandoned:         false,
    };

    probes.push(probe);
    pendingProbe = probe;

    // Abandon timer — if no T2 within 5s, mark abandoned
    abandonTimer = setTimeout(() => {
      if (pendingProbe && pendingProbe.t2 === null) {
        pendingProbe.abandoned = true;
        pendingProbe.delta     = null;
        pendingProbe           = null;
      }
      abandonTimer = null;
    }, 5000);

    scheduleNext();
  }

  function recordT2(event) {
    if (!pendingProbe || pendingProbe.t2 !== null) return;

    const now   = performance.now();
    const delta = now - pendingProbe.t1;

    // Ignore suspiciously fast responses — same-tick noise
    if (delta < 50) return;

    // Clear abandon timer — T2 was recorded in time
    if (abandonTimer) {
      clearTimeout(abandonTimer);
      abandonTimer = null;
    }

    pendingProbe.t2             = now;
    pendingProbe.delta          = delta;
    pendingProbe.source         = event.type || 'unknown';
    pendingProbe.response_target = getResponseTarget(event);

    // Capture reference before async delay
    const completedProbe = pendingProbe;
    pendingProbe = null;

    // Fill post_probe_n and behavioral_change 2s after T2
    setTimeout(() => {
      const post_probe_n = countEventsInWindow(completedProbe.t2, 2000);
      completedProbe.post_probe_n      = post_probe_n;
      completedProbe.behavioral_change = post_probe_n - completedProbe.pre_probe_n;
    }, 2000);
  }

  // ── Event listeners ───────────────────────────────────────────────────────
  // Use capture=false, passive=true — don't interfere with page behaviour.
  // Pass the full event so we can extract response_target.

  ['mousemove', 'keydown', 'click', 'scroll',
   'touchstart', 'mousedown', 'input', 'focusin']
    .forEach(evt => {
      document.addEventListener(evt, recordT2, { passive: true });
    });

  // MutationObserver — catches selenium/LLM agent DOM changes
  // that don't fire standard input events
  const observer = new MutationObserver((mutations) => {
    if (!pendingProbe || pendingProbe.t2 !== null) return;
    const now   = performance.now();
    const delta = now - pendingProbe.t1;
    if (delta < 50) return;

    if (abandonTimer) {
      clearTimeout(abandonTimer);
      abandonTimer = null;
    }

    pendingProbe.t2              = now;
    pendingProbe.delta           = delta;
    pendingProbe.source          = 'mutation';
    pendingProbe.response_target = mutations[0]?.target?.id
                                || mutations[0]?.target?.tagName?.toLowerCase()
                                || 'dom';

    const completedProbe = pendingProbe;
    pendingProbe = null;

    setTimeout(() => {
      const post_probe_n = countEventsInWindow(completedProbe.t2, 2000);
      completedProbe.post_probe_n      = post_probe_n;
      completedProbe.behavioral_change = post_probe_n - completedProbe.pre_probe_n;
    }, 2000);
  });

  observer.observe(document.body, {
    childList:     true,
    subtree:       true,
    attributes:    true,
    characterData: true,
  });

  // ── Scheduling ────────────────────────────────────────────────────────────

  function scheduleNext() {
    const delay = 3000 + Math.random() * 4000;
    setTimeout(fireProbe, delay);
  }

  // ── Public API ────────────────────────────────────────────────────────────

  window.__tifProbes = probes;

  // Called by session_transmitter.js after init()
  window.__tifProbeSetEnabled = function (enabled) {
    probeEnabled = !!enabled;
  };

  // Kick off scheduling — probe won't actually fire if probeEnabled = false
  setTimeout(fireProbe, 1000);

})();