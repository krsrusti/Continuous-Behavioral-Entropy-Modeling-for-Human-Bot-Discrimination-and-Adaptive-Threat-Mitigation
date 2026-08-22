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
 * Exposes: window.__tifProbes — array of { probeId, t1, t2, delta, source }
 */
(function () {
  'use strict';

  const probes = [];
  let probeCounter = 0;
  let pendingProbe = null;

  // Invisible 1x1 probe element
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

    // Close any uncompleted probe — mark as invalid
    if (pendingProbe && pendingProbe.t2 === null) {
      pendingProbe.delta = null;
      pendingProbe = null;
    }

    // Imperceptible DOM mutation — alternates top by 1px
    ghost.style.top = (probeCounter % 2 === 0) ? '-9999px' : '-9998px';

    pendingProbe = { probeId, t1, t2: null, delta: null, source: null };
    probes.push(pendingProbe);

    scheduleNext();
  }

  function recordT2(source) {
    if (!pendingProbe || pendingProbe.t2 !== null) return;

    const now   = performance.now();
    const delta = now - pendingProbe.t1;

    // Ignore suspiciously fast responses — likely same-tick mutation noise
    if (delta < 50) return;

    pendingProbe.t2     = now;
    pendingProbe.delta  = delta;
    pendingProbe.source = source || 'unknown';
    pendingProbe = null;
  }

  // Standard user interaction events
  ['mousemove', 'keydown', 'click', 'scroll',
   'touchstart', 'mousedown', 'input', 'focusin', 'focusout']
    .forEach(evt => {
      document.addEventListener(evt, () => recordT2(evt), { passive: true });
    });

  // MutationObserver — catches DOM changes made by selenium / LLM agents
  // when they type into fields, click buttons or modify the page
  const observer = new MutationObserver(() => recordT2('mutation'));
  observer.observe(document.body, {
    childList:     true,
    subtree:       true,
    attributes:    true,
    characterData: true,
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