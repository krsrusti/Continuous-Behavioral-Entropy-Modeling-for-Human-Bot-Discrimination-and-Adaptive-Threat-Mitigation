/**
 * micro_probe.js
 *
 * Active Micro-Probe System
 *
 * Behaviour:
 *   - probeEnabled = false:
 *       No probes are fired.
 *
 *   - probeEnabled = true:
 *       A small hidden DOM mutation is made every 3–7 seconds.
 *       T1 = probe fired.
 *       T2 = next meaningful user/agent interaction.
 *       delta = T2 - T1.
 *
 * Important:
 *   - The probe's own DOM mutation must NOT count as the response.
 *   - Only meaningful interaction events should complete a probe.
 *   - If nothing happens within 5 seconds, the probe is abandoned.
 *
 * Exposes:
 *   window.__tifProbes
 *   window.__tifProbeSetEnabled()
 */

(function () {
  'use strict';

  // ─────────────────────────────────────────────────────────────────────────
  // Configuration
  // ─────────────────────────────────────────────────────────────────────────

  let probeEnabled = false;

  const probes = [];

  let probeCounter = 0;

  let pendingProbe = null;

  let abandonTimer = null;

  let nextProbeTimer = null;


  // ─────────────────────────────────────────────────────────────────────────
  // Hidden ghost element
  // ─────────────────────────────────────────────────────────────────────────

  const ghost = document.createElement('div');

  Object.assign(ghost.style, {
    position: 'fixed',
    width: '1px',
    height: '1px',
    opacity: '0',
    pointerEvents: 'none',
    top: '-9999px',
    left: '-9999px',
    zIndex: '-1',
  });

  ghost.setAttribute('aria-hidden', 'true');

  document.body.appendChild(ghost);


  // ─────────────────────────────────────────────────────────────────────────
  // Helpers
  // ─────────────────────────────────────────────────────────────────────────

  function getPassiveEvents() {
    return window.__tifPassive || [];
  }


  function countEventsBefore(centerTs, windowMs) {
    const events = getPassiveEvents();

    const from = centerTs - windowMs;
    const to = centerTs;

    return events.filter(
      e => e.ts >= from && e.ts <= to
    ).length;
  }


  function countEventsAfter(centerTs, windowMs) {
    const events = getPassiveEvents();

    const from = centerTs;
    const to = centerTs + windowMs;

    return events.filter(
      e => e.ts >= from && e.ts <= to
    ).length;
  }


  function wasIdleBefore(t1, idleWindowMs) {
    const events = getPassiveEvents();

    const from = t1 - idleWindowMs;

    return !events.some(
      e => e.ts >= from && e.ts < t1
    );
  }


  function getResponseTarget(event) {
    if (!event || !event.target) {
      return null;
    }

    const el = event.target;

    if (el.id) {
      return el.id;
    }

    if (el.name) {
      return el.name;
    }

    if (el.tagName) {
      return el.tagName.toLowerCase();
    }

    return null;
  }


  // ─────────────────────────────────────────────────────────────────────────
  // Finish probe
  // ─────────────────────────────────────────────────────────────────────────

  function completeProbe(event, sourceOverride = null) {

    if (!pendingProbe) {
      return;
    }

    if (pendingProbe.t2 !== null) {
      return;
    }

    const now = performance.now();

    const delta = now - pendingProbe.t1;

    // Ignore same-tick events.
    if (delta < 50) {
      return;
    }

    // Stop abandonment timer.
    if (abandonTimer) {
      clearTimeout(abandonTimer);
      abandonTimer = null;
    }

    pendingProbe.t2 = now;

    pendingProbe.delta = delta;

    pendingProbe.source =
      sourceOverride ||
      event?.type ||
      'unknown';

    pendingProbe.response_target =
      getResponseTarget(event);

    const completedProbe = pendingProbe;

    pendingProbe = null;


    // Wait 2 seconds before calculating post-probe behaviour.
    setTimeout(() => {

      const postProbeCount =
        countEventsAfter(
          completedProbe.t2,
          2000
        );

      completedProbe.post_probe_n =
        postProbeCount;

      completedProbe.behavioral_change =
        postProbeCount -
        completedProbe.pre_probe_n;

    }, 2000);
  }


  // ─────────────────────────────────────────────────────────────────────────
  // Fire probe
  // ─────────────────────────────────────────────────────────────────────────

  function fireProbe() {

    if (!probeEnabled) {
      scheduleNext();
      return;
    }


    // If a previous probe is still waiting,
    // abandon it before starting another.
    if (pendingProbe && pendingProbe.t2 === null) {

      pendingProbe.abandoned = true;

      pendingProbe.delta = null;

      pendingProbe = null;
    }


    if (abandonTimer) {

      clearTimeout(abandonTimer);

      abandonTimer = null;
    }


    probeCounter += 1;

    const probeId = probeCounter;

    const t1 = performance.now();


    // ───────────────────────────────────────────────────────────────────────
    // Measure behaviour BEFORE probe
    // ───────────────────────────────────────────────────────────────────────

    const preProbeCount =
      countEventsBefore(
        t1,
        2000
      );

    const idleBefore =
      wasIdleBefore(
        t1,
        3000
      );


    // ───────────────────────────────────────────────────────────────────────
    // Create probe record
    // ───────────────────────────────────────────────────────────────────────

    const probe = {

      probeId,

      t1,

      t2: null,

      delta: null,

      source: null,

      response_target: null,

      pre_probe_n:
        preProbeCount,

      post_probe_n: null,

      behavioral_change: null,

      idle_before:
        idleBefore,

      abandoned: false,
    };


    probes.push(probe);

    pendingProbe = probe;


    // ───────────────────────────────────────────────────────────────────────
    // DOM mutation
    //
    // IMPORTANT:
    // This mutation happens immediately after T1.
    // The MutationObserver below ignores mutations caused by the ghost.
    // ───────────────────────────────────────────────────────────────────────

    ghost.style.top =
      (probeCounter % 2 === 0)
        ? '-9999px'
        : '-9998px';


    // ───────────────────────────────────────────────────────────────────────
    // Abandon after 5 seconds
    // ───────────────────────────────────────────────────────────────────────

    abandonTimer = setTimeout(() => {

      if (
        pendingProbe &&
        pendingProbe.probeId === probeId &&
        pendingProbe.t2 === null
      ) {

        pendingProbe.abandoned = true;

        pendingProbe.delta = null;

        pendingProbe = null;
      }

      abandonTimer = null;

    }, 5000);


    scheduleNext();
  }


  // ─────────────────────────────────────────────────────────────────────────
  // Schedule next probe
  // ─────────────────────────────────────────────────────────────────────────

  function scheduleNext() {

    if (nextProbeTimer) {
      clearTimeout(nextProbeTimer);
    }

    const delay =
      3000 +
      Math.random() * 4000;

    nextProbeTimer =
      setTimeout(
        fireProbe,
        delay
      );
  }


  // ─────────────────────────────────────────────────────────────────────────
  // User / agent interaction events
  // ─────────────────────────────────────────────────────────────────────────

  [
    'mousemove',
    'keydown',
    'click',
    'scroll',
    'touchstart',
    'mousedown',
    'input',
    'focusin'
  ].forEach(evt => {

    document.addEventListener(
      evt,
      function (event) {

        if (!probeEnabled) {
          return;
        }

        completeProbe(event);

      },
      {
        passive: true
      }
    );

  });


  // ─────────────────────────────────────────────────────────────────────────
  // MutationObserver
  //
  // We DO NOT let arbitrary DOM mutations immediately become probe
  // responses. The main signal should come from actual interaction.
  //
  // This prevents the page itself / Selenium / framework DOM updates
  // from creating lots of false probe responses.
  // ─────────────────────────────────────────────────────────────────────────

  const observer =
    new MutationObserver(() => {

      // Intentionally ignored.
      //
      // The probe's own DOM mutation must not complete the probe.
      //
      // We still observe mutations here so the system can be extended later,
      // but mutations are not currently used as T2.
    });


  observer.observe(
    document.body,
    {
      childList: true,
      subtree: true,
      attributes: true,
      characterData: true
    }
  );


  // ─────────────────────────────────────────────────────────────────────────
  // Public API
  // ─────────────────────────────────────────────────────────────────────────

  window.__tifProbes = probes;


  window.__tifProbeSetEnabled =
    function (enabled) {

      probeEnabled = !!enabled;

      console.log(
        '[TIF Probe] Enabled:',
        probeEnabled
      );

      // If disabled, cancel future scheduling.
      if (!probeEnabled) {

        if (nextProbeTimer) {
          clearTimeout(nextProbeTimer);
          nextProbeTimer = null;
        }

        if (abandonTimer) {
          clearTimeout(abandonTimer);
          abandonTimer = null;
        }

        pendingProbe = null;

        return;
      }

      // If enabled, start the probe cycle.
      if (!nextProbeTimer) {
        scheduleNext();
      }
    };


  // ─────────────────────────────────────────────────────────────────────────
  // Initial state
  // ─────────────────────────────────────────────────────────────────────────

  console.log(
    '[TIF Probe] Loaded. Waiting for TIFSession.init().'
  );

})();