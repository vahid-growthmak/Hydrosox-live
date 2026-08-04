/**
 * Filters the review feed.
 *
 * Filtering is done by hiding rows rather than by re-fetching, because every
 * review is already in the document — the feed is authored in the section, not
 * paginated. With the script absent every review is visible and the chips do
 * nothing, which is the right way round for a failure.
 */
class HSReviews extends HTMLElement {
  connectedCallback() {
    this.list = this.querySelector('[data-hs-review-list]');
    this.empty = this.querySelector('[data-hs-review-empty]');
    this.chips = [...this.querySelectorAll('[data-hs-review-filter]')];
    if (!this.list || !this.chips.length) return;

    this.items = [...this.list.children];
    this.chips.forEach((chip) =>
      chip.addEventListener('click', () => this.apply(chip.dataset.hsReviewFilter, chip))
    );
  }

  apply(filter, chip) {
    this.chips.forEach((c) => c.classList.toggle('is-active', c === chip));

    const [kind, value] = filter.split(':');
    let shown = 0;

    this.items.forEach((item) => {
      let match = true;
      if (kind === 'rating') match = item.dataset.rating === value;
      else if (kind === 'tag') match = item.dataset.tag === value;

      item.hidden = !match;
      if (match) shown += 1;
    });

    if (this.empty) this.empty.hidden = shown > 0;
  }
}

if (!customElements.get('hs-reviews')) customElements.define('hs-reviews', HSReviews);
