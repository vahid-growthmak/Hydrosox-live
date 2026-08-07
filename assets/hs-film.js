/**
 * <hs-film> — chapter switcher for the product film.
 *
 * The stage holds one stacked layer per chapter; choosing a chapter
 * cross-fades to its layer and moves the progress rule. The play control
 * drives whichever chapter is on the stage: play/pause when that chapter has
 * a video, and nothing at all when it only has a poster.
 *
 * Chapters with a video play themselves. Muted and inline, because every
 * browser blocks autoplay with sound and silently leaves the frame frozen
 * rather than telling you why. Only the chapter on the stage plays, and only
 * while the section is on screen — four clips looping behind a footer nobody
 * has scrolled to is bandwidth spent on nothing.
 */
class HSFilm extends HTMLElement {
  connectedCallback() {
    this.layers = Array.from(this.querySelectorAll('[data-hs-slide]'));
    this.chapters = Array.from(this.querySelectorAll('[data-hs-chapter]'));
    this.playButton = this.querySelector('[data-hs-film-play]');
    this.active = 0;

    // Hover is the primary way in on a precise pointer — moving across the
    // chapter list swaps the stage as you go. Click and keyboard focus stay
    // wired up so touch and keyboard reach every chapter too.
    this.finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');

    this.chapters.forEach((button) => {
      const index = () => parseInt(button.dataset.hsChapter, 10);

      button.addEventListener('click', () => this.select(index()));
      button.addEventListener('focus', () => this.select(index()));
      button.addEventListener('pointerenter', (event) => {
        if (event.pointerType === 'touch' || !this.finePointer.matches) return;
        this.select(index());
      });
    });

    if (this.playButton) {
      this.playButton.addEventListener('click', () => this.togglePlayback());
    }

    this.autoplay = this.hasAttribute('data-autoplay')
      && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (this.autoplay) this.watch();
  }

  /*
    Play only while the section is actually on screen. Without the observer a
    clip starts on page load and loops for as long as the tab is open, which
    costs the visitor data for something they may never scroll to.
  */
  watch() {
    if (!('IntersectionObserver' in window)) {
      this.resume();
      return;
    }
    this.observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) this.resume();
        else this.suspend();
      }
    }, { threshold: 0.25 });
    this.observer.observe(this);
  }

  resume() {
    this.onScreen = true;
    const video = this.activeVideo();
    // play() rejects when the browser declines; nothing to recover, and an
    // unhandled rejection in the console is worse than a still frame.
    if (video) video.play().catch(() => {});
  }

  suspend() {
    this.onScreen = false;
    this.layers.forEach((layer) => {
      const video = layer.querySelector('video');
      if (video && !video.paused) video.pause();
    });
  }

  activeVideo() {
    const layer = this.layers[this.active];
    return layer ? layer.querySelector('video') : null;
  }

  select(index) {
    if (Number.isNaN(index) || index === this.active) return;

    // Whatever was playing stops before the stage changes.
    const previous = this.activeVideo();
    if (previous && !previous.paused) previous.pause();

    this.active = index;

    this.layers.forEach((layer, i) => {
      const on = i === index;
      layer.classList.toggle('is-active', on);
      if (on) layer.removeAttribute('aria-hidden');
      else layer.setAttribute('aria-hidden', 'true');
    });

    this.chapters.forEach((button, i) => {
      const on = i === index;
      button.classList.toggle('is-active', on);
      button.setAttribute('aria-pressed', on ? 'true' : 'false');
    });

    // The chapter that just arrived takes over, so switching never leaves the
    // stage on a frozen frame.
    if (this.autoplay && this.onScreen !== false) this.resume();
  }

  togglePlayback() {
    const video = this.activeVideo();
    if (!video) return;
    if (video.paused) video.play();
    else video.pause();
  }
}

if (!customElements.get('hs-film')) customElements.define('hs-film', HSFilm);
