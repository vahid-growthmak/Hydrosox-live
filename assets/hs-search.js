/**
 * Predictive search.
 *
 * Suggestions come from Shopify's /search/suggest endpoint rendered through the
 * predictive-search section, so every title, price and URL on screen was
 * produced by Liquid. The script's only jobs are to debounce typing, abort a
 * request that a newer keystroke has already made stale, and move focus.
 *
 * The form underneath is a real GET to /search. With this file absent the
 * search icon still navigates and Enter still searches.
 */

const DEBOUNCE_MS = 220;
const MIN_CHARS = 2;

class HSSearch extends HTMLElement {
  connectedCallback() {
    this.panel = this.querySelector('.hs-psearch__panel');
    this.input = this.querySelector('[data-hs-search-input]');
    this.body = this.querySelector('[data-hs-search-body]');
    this.clear = this.querySelector('[data-hs-search-clear]');
    this.isOpen = false;

    this.onKeydown = this.onKeydown.bind(this);

    this.querySelectorAll('[data-hs-search-close]').forEach((el) =>
      el.addEventListener('click', () => this.close())
    );

    if (this.clear) {
      this.clear.addEventListener('click', () => {
        this.input.value = '';
        this.reset();
        this.input.focus();
      });
    }

    if (this.input) {
      this.input.addEventListener('input', () => {
        if (this.clear) this.clear.hidden = this.input.value.length === 0;
        this.schedule(this.input.value.trim());
      });
    }

    // Any search trigger in the document opens this overlay.
    document.addEventListener('click', (e) => {
      const trigger = e.target.closest('[data-hs-search-open], a[href$="/search"]');
      if (!trigger) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      this.open();
    });
  }

  /* --------------------------------------------------------------- fetching */

  schedule(term) {
    clearTimeout(this.timer);
    if (term.length < MIN_CHARS) {
      this.reset();
      return;
    }
    this.timer = setTimeout(() => this.fetch(term), DEBOUNCE_MS);
  }

  async fetch(term) {
    // A newer keystroke invalidates an in-flight request; without this the
    // slower of two responses can land last and show results for old input.
    if (this.controller) this.controller.abort();
    this.controller = new AbortController();

    const root = window.Shopify?.routes?.root || '/';
    const params = new URLSearchParams({
      q: term,
      'resources[type]': 'product,page,article',
      'resources[limit]': '4',
      'resources[options][unavailable_products]': 'last',
      section_id: 'predictive-search',
    });

    this.classList.add('is-busy');
    try {
      const res = await fetch(`${root}search/suggest?${params}`, {
        signal: this.controller.signal,
      });
      if (!res.ok) throw new Error(res.status);

      const html = await res.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const results = doc.querySelector('[data-hs-psearch-results]');
      if (results && this.body) {
        this.body.innerHTML = results.innerHTML;
        this.setExpanded(true);
      }
    } catch (err) {
      // An abort is the expected path, not a failure. Anything else leaves the
      // previous suggestions in place — the form still works regardless.
      if (err.name !== 'AbortError') this.setExpanded(false);
    } finally {
      this.classList.remove('is-busy');
    }
  }

  reset() {
    if (this.body) this.body.innerHTML = '';
    this.setExpanded(false);
  }

  setExpanded(open) {
    if (this.input) this.input.setAttribute('aria-expanded', String(open));
  }

  /* ------------------------------------------------------------ open/close */

  open() {
    if (this.isOpen) return;
    this.removeAttribute('hidden');
    void this.offsetWidth;
    this.classList.add('is-open');
    this.isOpen = true;

    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', this.onKeydown);
    if (this.input) this.input.focus();
  }

  close() {
    if (!this.isOpen) return;
    this.classList.remove('is-open');
    this.isOpen = false;

    document.body.style.overflow = '';
    document.removeEventListener('keydown', this.onKeydown);

    const done = () => this.setAttribute('hidden', '');
    if (this.panel) {
      let settled = false;
      const once = () => {
        if (settled) return;
        settled = true;
        done();
      };
      this.panel.addEventListener('transitionend', once, { once: true });
      setTimeout(once, 400);
    } else {
      done();
    }
  }

  onKeydown(e) {
    if (e.key === 'Escape') {
      this.close();
      return;
    }

    // Down-arrow moves from the field into the first suggestion, so the list is
    // reachable without tabbing past the clear and close buttons.
    if (e.key === 'ArrowDown' && document.activeElement === this.input) {
      const first = this.body && this.body.querySelector('a');
      if (first) {
        e.preventDefault();
        first.focus();
      }
    }
  }
}

if (!customElements.get('hs-search')) customElements.define('hs-search', HSSearch);
