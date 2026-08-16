/**
 * micro_probe.js — THE NOVEL PART: Active Micro-Probe System.
 *
 * Every 3-7 seconds fires an imperceptible DOM micro-event (invisible
 * element shift). Records T1 (probe fired). Waits for the next user
 * interaction to record T2. Delta (T2-T1) = Inference Latency Signal.
 *
 * LLM agents that re-evaluate the DOM after each mutation exhibit a
 * characteristic latency spike reflecting their inference time.
 *
 * Exposes: window.__tifProbes — array of { probeId, t1, t2, delta }
 */
(function () {
  'use strict';

  const probes = [];
  let probeCounter = 0;
  let pendingProbe = null;

  // Create the invisible probe element — 1x1px, off-screen, aria-hidden
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

  function fireProbe() {
    const probeId = ++probeCounter;
    const t1 = performance.now();

    // Imperceptible DOM mutation — alternates top by 1px
    ghost.style.top = (probeCounter % 2 === 0) ? '-9999px' : '-9998px';

    pendingProbe = { probeId, t1, t2: null, delta: null };
    probes.push(pendingProbe);

    scheduleNext();
  }

  function recordT2() {
    if (!pendingProbe || pendingProbe.t2 !== null) return;
    pendingProbe.t2    = performance.now();
    pendingProbe.delta = pendingProbe.t2 - pendingProbe.t1;
    pendingProbe = null;
  }

  // Capture the NEXT user action after each probe fires
  ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach((evt) => {
    document.addEventListener(evt, recordT2, { passive: true });
  });

  function scheduleNext() {
    // Random interval 3000-7000ms to prevent rhythm detection
    const delay = 3000 + Math.random() * 4000;
    setTimeout(fireProbe, delay);
  }

  // First probe fires after 1 second (give page time to settle)
  setTimeout(fireProbe, 1000);

  window.__tifProbes = probes;
})();