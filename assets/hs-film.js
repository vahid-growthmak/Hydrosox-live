/**
 * <hs-film> — chapter switcher for the product film.
 *
 * The stage holds one stacked layer per chapter; choosing a chapter
 * cross-fades to its layer and moves the progress rule. The play control
 * drives whichever chapter is on the stage: play/pause when that chapter has
 * a video, and nothing at all when it only has a poster.
 */
class HSFilm extends HTMLElement {
  connectedCallback() {
    this.layers = Array.from(this.querySelectorAll('[data-hs-slide]'));
    this.chapters = Array.from(this.querySelectorAll('[data-hs-chapter]'));
    this.playButton = this.querySelector('[data-hs-film-play]');
    this.active = 0;

    this.chapters.forEach((button) =>
      button.addEventListener('click', () => this.select(parseInt(button.dataset.hsChapter, 10)))
    );

    if (this.playButton) {
      this.playButton.addEventListener('click', () => this.togglePlayback());
    }
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
  }

  togglePlayback() {
    const video = this.activeVideo();
    if (!video) return;
    if (video.paused) video.play();
    else video.pause();
  }
}

if (!customElements.get('hs-film')) customElements.define('hs-film', HSFilm);
