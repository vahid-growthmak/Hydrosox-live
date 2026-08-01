/**
 * <hs-layers> — scroll-scrub for the construction section.
 *
 * Maps scroll progress through the tall track onto a 0..1 value, then uses it
 * to separate the layer planes, cross-fade the matching description, and fill
 * the progress rail. Reads on scroll are throttled to one per frame and only
 * write when the active step actually changes.
 */
class HSLayers extends HTMLElement {
  connectedCallback() {
    this.count = Math.max(1, parseInt(this.dataset.count || '1', 10));
    this.planes = Array.from(this.querySelectorAll('[data-hs-plane]'));
    this.panels = Array.from(this.querySelectorAll('[data-hs-panel]'));
    this.rails = Array.from(this.querySelectorAll('[data-hs-rail]'));

    this.active = -1;
    this.progress = -1;

    this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    this.onScroll = this.onScroll.bind(this);
    this.onMotionChange = this.onMotionChange.bind(this);

    window.addEventListener('scroll', this.onScroll, { passive: true });
    window.addEventListener('resize', this.onScroll, { passive: true });
    this.reducedMotion.addEventListener('change', this.onMotionChange);

    this.measure();
  }

  disconnectedCallback() {
    window.removeEventListener('scroll', this.onScroll);
    window.removeEventListener('resize', this.onScroll);
    this.reducedMotion.removeEventListener('change', this.onMotionChange);
  }

  onMotionChange() {
    this.measure();
  }

  onScroll() {
    if (this.frame) return;
    this.frame = requestAnimationFrame(() => {
      this.frame = null;
      this.measure();
    });
  }

  measure() {
    const rect = this.getBoundingClientRect();
    // Distance the track can travel before its pinned panel is released.
    const travel = rect.height - window.innerHeight;

    let progress = travel > 0 ? -rect.top / travel : 0;
    progress = Math.min(1, Math.max(0, progress));

    // Motion off: show the fully separated state and the first description.
    if (this.reducedMotion.matches) {
      this.paint(1, 0);
      return;
    }

    // Spread the steps evenly across the track.
    const step = Math.min(this.count - 1, Math.floor(progress * this.count));
    this.paint(progress, step);
  }

  paint(progress, step) {
    if (progress !== this.progress) {
      this.progress = progress;
      this.style.setProperty('--hs-progress', progress.toFixed(4));

      // Per-step fill for the rail, each segment filling across its own third.
      this.rails.forEach((rail, index) => {
        const start = index / this.count;
        const local = Math.min(1, Math.max(0, (progress - start) * this.count));
        rail.style.setProperty('--hs-rail-progress', local.toFixed(4));
      });
    }

    if (step === this.active) return;
    this.active = step;

    this.panels.forEach((panel, index) => {
      const on = index === step;
      panel.classList.toggle('is-active', on);
      if (on) panel.removeAttribute('aria-hidden');
      else panel.setAttribute('aria-hidden', 'true');
    });

    this.planes.forEach((plane, index) =>
      plane.classList.toggle('is-active', index === step)
    );

    this.rails.forEach((rail, index) =>
      rail.classList.toggle('is-active', index === step)
    );
  }
}

if (!customElements.get('hs-layers')) customElements.define('hs-layers', HSLayers);
