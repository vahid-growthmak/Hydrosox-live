/**
 * <hs-layers> — scroll-scrub for the construction section.
 *
 * Maps scroll progress through the tall track onto a 0..1 value, then uses it
 * to pick a frame from the exploded sequence, cross-fade the matching
 * description, and fill the progress rail. Reads on scroll are throttled to
 * one per frame and only write when something has actually changed.
 *
 * Frames are decoded once and cached. The nearest already-decoded frame is
 * drawn while the exact one is still loading, so the scrub never stalls.
 */
class HSLayers extends HTMLElement {
  connectedCallback() {
    this.count = Math.max(1, parseInt(this.dataset.count || '1', 10));
    this.panels = Array.from(this.querySelectorAll('[data-hs-panel]'));
    this.rails = Array.from(this.querySelectorAll('[data-hs-rail]'));

    this.canvas = this.querySelector('[data-hs-canvas]');
    this.first = this.querySelector('[data-hs-first]');

    this.active = -1;
    this.progress = -1;
    this.drawn = -1;
    this.painted = false;

    this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    this.onScroll = this.onScroll.bind(this);
    this.onMotionChange = this.onMotionChange.bind(this);

    this.setUpFrames();

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

  /* ---------------------------------------------------------------- frames */

  setUpFrames() {
    this.frames = [];
    this.images = [];
    if (!this.canvas) return;

    const source = this.querySelector('[data-hs-frames]');
    if (!source) return;

    try {
      this.frames = JSON.parse(source.textContent) || [];
    } catch {
      this.frames = [];
    }
    if (!this.frames.length) return;

    this.ctx = this.canvas.getContext('2d', { alpha: false });
    this.images = new Array(this.frames.length).fill(null);

    // The first frame decides when the canvas can take over from the <img>.
    this.load(0, () => this.paintFrame(0));

    // Everything else streams in behind it, a few at a time, so the sequence
    // does not compete with the rest of the page for bandwidth. The queue stays
    // shut until the section is within a screen of the viewport — a couple of
    // megabytes of frames should not be on the critical path for a visitor who
    // never scrolls this far. measure() opens it, so this rides on the scroll
    // handler that is running anyway rather than a second observer.
    this.queue = [];
    for (let i = 1; i < this.frames.length; i += 1) this.queue.push(i);
    this.inFlight = 0;
    this.queueOpen = false;
  }

  /** Opens the preload queue once the section is one screen away. */
  maybeOpenQueue(rect) {
    if (this.queueOpen || !this.frames.length) return;
    const near = rect.top < window.innerHeight * 2 && rect.bottom > -window.innerHeight;
    if (!near) return;
    this.queueOpen = true;
    this.pump();
  }

  pump() {
    const CONCURRENCY = 6;
    while (this.inFlight < CONCURRENCY && this.queue.length) {
      const index = this.queue.shift();
      this.inFlight += 1;
      this.load(index, () => {
        this.inFlight -= 1;
        // A newly arrived frame may be the one the current scroll position
        // wants, so redraw if it beats what is on screen.
        if (index === this.wanted) this.paintFrame(index);
        this.pump();
      });
    }
  }

  load(index, done) {
    if (this.images[index]) {
      done();
      return;
    }
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => {
      this.images[index] = img;
      done();
    };
    img.onerror = done;
    img.src = this.frames[index];
  }

  /** Draws `index`, or the closest decoded neighbour if it is not ready yet. */
  paintFrame(index) {
    if (!this.ctx || !this.images.length) return;

    let use = index;
    if (!this.images[use]) {
      use = -1;
      for (let step = 1; step < this.images.length; step += 1) {
        if (this.images[index - step]) {
          use = index - step;
          break;
        }
        if (this.images[index + step]) {
          use = index + step;
          break;
        }
      }
    }
    if (use < 0 || use === this.drawn) return;

    const img = this.images[use];
    if (this.canvas.width !== img.naturalWidth) {
      this.canvas.width = img.naturalWidth;
      this.canvas.height = img.naturalHeight;
    }
    this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
    this.drawn = use;

    if (!this.painted) {
      this.painted = true;
      this.classList.add('is-painted');
    }
  }

  /* ---------------------------------------------------------------- scroll */

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
    this.maybeOpenQueue(rect);

    // Distance the track can travel before its pinned panel is released.
    const travel = rect.height - window.innerHeight;

    let progress = travel > 0 ? -rect.top / travel : 0;
    progress = Math.min(1, Math.max(0, progress));

    // Motion off: hold the fully separated state and the first description.
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

      if (this.frames.length) {
        const last = this.frames.length - 1;
        this.wanted = Math.min(last, Math.max(0, Math.round(progress * last)));
        this.paintFrame(this.wanted);

        // The frame under the cursor jumps the queue, so a fast scroll into the
        // middle of the sequence resolves there rather than loading up to it.
        if (this.queue && !this.images[this.wanted]) {
          const at = this.queue.indexOf(this.wanted);
          if (at > 0) {
            this.queue.splice(at, 1);
            this.queue.unshift(this.wanted);
          }
        }
      }
    }

    if (step === this.active) return;
    this.active = step;

    this.panels.forEach((panel, index) => {
      const on = index === step;
      panel.classList.toggle('is-active', on);
      if (on) panel.removeAttribute('aria-hidden');
      else panel.setAttribute('aria-hidden', 'true');
    });

    this.rails.forEach((rail, index) =>
      rail.classList.toggle('is-active', index === step)
    );
  }
}

if (!customElements.get('hs-layers')) customElements.define('hs-layers', HSLayers);
