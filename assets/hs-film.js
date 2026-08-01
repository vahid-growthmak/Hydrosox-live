/**
 * <hs-film> — chapter switcher for the product film.
 *
 * Swaps which chapter is on the stage and pauses whatever was playing, so
 * changing chapter never leaves audio running behind the new slide.
 */
class HSFilm extends HTMLElement {
  connectedCallback() {
    this.slides = Array.from(this.querySelectorAll('[data-hs-slide]'));
    this.chapters = Array.from(this.querySelectorAll('[data-hs-chapter]'));

    this.chapters.forEach((button) =>
      button.addEventListener('click', () => this.select(parseInt(button.dataset.hsChapter, 10)))
    );

    // The play affordance only exists on chapters with no video of their own;
    // where there is a video the native controls handle playback.
    this.querySelectorAll('[data-hs-film-play]').forEach((button) =>
      button.addEventListener('click', () => {
        const slide = button.closest('[data-hs-slide]');
        const video = slide && slide.querySelector('video');
        if (video) {
          button.hidden = true;
          video.play();
        }
      })
    );
  }

  select(index) {
    if (Number.isNaN(index)) return;

    this.slides.forEach((slide, i) => {
      const on = i === index;
      slide.classList.toggle('is-active', on);
      if (on) slide.removeAttribute('aria-hidden');
      else slide.setAttribute('aria-hidden', 'true');

      // Stop playback on any slide leaving the stage.
      if (!on) {
        const video = slide.querySelector('video');
        if (video && !video.paused) video.pause();
      }
    });

    this.chapters.forEach((button, i) => {
      const on = i === index;
      button.classList.toggle('is-active', on);
      button.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }
}

if (!customElements.get('hs-film')) customElements.define('hs-film', HSFilm);
