/**
 * Cart drawer.
 *
 * Every mutation goes through Shopify's cart AJAX endpoints and asks for the
 * drawer section back in the same round trip, so the markup that lands is the
 * markup Liquid would have rendered on a full page load. The script therefore
 * never computes a price, a total, a discount or a progress percentage — it
 * only swaps in what the server said. That is what stops a drawer drifting
 * away from the checkout.
 *
 * The bag icon stays a real link to /cart and every control is inside a real
 * form, so with this file absent the cart still works, one page load at a time.
 */

const SECTION_ID = 'cart-drawer';

class HSCartDrawer extends HTMLElement {
  connectedCallback() {
    this.panel = this.querySelector('.hs-cartd__panel');
    this.status = this.querySelector('[data-hs-cart-status]');
    this.isOpen = false;
    this.pending = 0;

    this.onKeydown = this.onKeydown.bind(this);
    this.onFocusIn = this.onFocusIn.bind(this);

    this.bind();
    this.interceptAddToCart();
    this.interceptBagLinks();
  }

  /* ------------------------------------------------------------------ wiring */

  // Re-bound after every swap, because the nodes are replaced wholesale.
  bind() {
    this.querySelectorAll('[data-hs-cart-close]').forEach((el) =>
      el.addEventListener('click', (e) => {
        e.preventDefault();
        this.close();
      })
    );

    this.querySelectorAll('[data-hs-cart-step]').forEach((btn) =>
      btn.addEventListener('click', () => {
        const stepper = btn.closest('[data-hs-cart-stepper]');
        const input = stepper && stepper.querySelector('[data-hs-cart-qty]');
        if (!input) return;
        const next = Math.max(0, (parseInt(input.value, 10) || 0) + Number(btn.dataset.hsCartStep));
        this.change(input.dataset.line, next);
      })
    );

    this.querySelectorAll('[data-hs-cart-qty]').forEach((input) =>
      input.addEventListener('change', () => {
        const next = Math.max(0, parseInt(input.value, 10) || 0);
        this.change(input.dataset.line, next);
      })
    );

    this.querySelectorAll('[data-hs-cart-remove]').forEach((link) =>
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.change(link.dataset.line, 0);
      })
    );

    const note = this.querySelector('[data-hs-cart-note]');
    if (note) {
      note.addEventListener('change', () => {
        this.post(`${window.Shopify?.routes?.root || '/'}cart/update.js`, { note: note.value });
      });
    }

    // The updates form only exists for the no-JS path.
    const form = this.querySelector('[data-hs-cart-form]');
    if (form) form.addEventListener('submit', (e) => e.preventDefault());
  }

  /*
    Any add-to-cart form on the page opens the drawer instead of navigating.
    Delegated from the document so a form rendered later — a quick-add, a
    section the merchant just edited — is covered without re-binding.
  */
  interceptAddToCart() {
    document.addEventListener('submit', async (e) => {
      const form = e.target;
      if (!(form instanceof HTMLFormElement)) return;
      if (!/\/cart\/add/.test(form.getAttribute('action') || '')) return;

      e.preventDefault();
      const submit = form.querySelector('[type="submit"]');
      if (submit) submit.classList.add('is-busy');

      const body = new FormData(form);
      body.append('sections', SECTION_ID);

      try {
        const res = await fetch(`${this.root()}cart/add.js`, {
          method: 'POST',
          headers: { Accept: 'application/json' },
          body,
        });
        const data = await res.json();

        if (!res.ok) {
          // Shopify returns a human-readable description for a real refusal —
          // sold out, or more than the stock allows. Show it, do not swallow it.
          this.showFormError(form, data.description || data.message);
          return;
        }

        this.clearFormError(form);
        this.swap(data.sections);
        this.open();
        this.announce(data.product_title);
      } catch {
        // The network failed, so fall back to the page Shopify would have
        // served anyway rather than leaving the button spinning.
        form.submit();
      } finally {
        if (submit) submit.classList.remove('is-busy');
      }
    });
  }

  // The bag icon opens the drawer, unless the merchant chose the cart page.
  interceptBagLinks() {
    if (this.dataset.cartType === 'page') return;
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href$="/cart"], a[href*="/cart?"]');
      if (!link || link.hasAttribute('data-hs-cart-bypass')) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      this.open();
    });
  }

  /* ------------------------------------------------------------- mutations */

  root() {
    return window.Shopify?.routes?.root || '/';
  }

  async change(line, quantity) {
    if (!line) return;
    await this.post(`${this.root()}cart/change.js`, { line: Number(line), quantity });
  }

  async post(url, payload) {
    this.setBusy(true);
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ ...payload, sections: SECTION_ID }),
      });
      const data = await res.json();
      if (data.sections) this.swap(data.sections);
      this.announce();
    } catch {
      // Reload rather than leave stale numbers on screen; the server is the
      // only thing that knows what the cart now contains.
      window.location.reload();
    } finally {
      this.setBusy(false);
    }
  }

  /*
    Replace the panel's contents with the server-rendered section, then put the
    listeners back. The outer custom element survives so the drawer stays open
    across the swap.
  */
  swap(sections) {
    const html = sections && sections[SECTION_ID];
    if (!html) return;

    const doc = new DOMParser().parseFromString(html, 'text/html');
    const fresh = doc.querySelector('.hs-cartd__panel');
    if (!fresh || !this.panel) return;

    this.panel.innerHTML = fresh.innerHTML;
    const count = doc.querySelector('hs-cart-drawer')?.dataset.cartCount;
    if (count !== undefined) {
      this.dataset.cartCount = count;
      this.paintBadge(Number(count));
    }

    this.status = this.querySelector('[data-hs-cart-status]');
    this.bind();
  }

  // The header is outside this section, so its badge is updated by hand.
  paintBadge(count) {
    document.querySelectorAll('[data-hs-cart-count]').forEach((el) => {
      el.textContent = count;
      el.hidden = count === 0;
    });
  }

  setBusy(busy) {
    this.pending += busy ? 1 : -1;
    this.classList.toggle('is-busy', this.pending > 0);
  }

  announce(productTitle) {
    if (!this.status) return;
    const added = this.dataset.addedLabel || 'Added to cart';
    const updated = this.dataset.updatedLabel || 'Cart updated';
    this.status.textContent = productTitle ? `${productTitle} — ${added}` : updated;
  }

  showFormError(form, message) {
    if (!message) return;
    let box = form.querySelector('[data-hs-cart-error]');
    if (!box) {
      box = document.createElement('p');
      box.className = 'hs-caption hs-form-error';
      box.setAttribute('data-hs-cart-error', '');
      box.setAttribute('role', 'alert');
      form.appendChild(box);
    }
    box.textContent = message;
  }

  clearFormError(form) {
    const box = form.querySelector('[data-hs-cart-error]');
    if (box) box.remove();
  }

  /* ------------------------------------------------------------- open/close */

  open() {
    if (this.isOpen) return;
    this.removeAttribute('hidden');

    // Flush layout so the transition has a closed state to run from, then set
    // the class synchronously — waiting a frame means the drawer never opens
    // anywhere requestAnimationFrame is throttled.
    void this.offsetWidth;
    this.classList.add('is-open');
    this.isOpen = true;

    this.lockScroll();
    document.addEventListener('keydown', this.onKeydown);
    document.addEventListener('focusin', this.onFocusIn);

    const focusable = this.panel && this.panel.querySelector('[data-hs-cart-close]');
    if (focusable) focusable.focus();
  }

  close() {
    if (!this.isOpen) return;
    this.classList.remove('is-open');
    this.isOpen = false;

    this.unlockScroll();
    document.removeEventListener('keydown', this.onKeydown);
    document.removeEventListener('focusin', this.onFocusIn);

    // Hide only once the panel has slid away, so it does not vanish mid-slide.
    const done = () => this.setAttribute('hidden', '');
    if (this.panel) {
      let settled = false;
      const once = () => {
        if (settled) return;
        settled = true;
        done();
      };
      this.panel.addEventListener('transitionend', once, { once: true });
      // A missing transitionend must not leave the scrim over the page.
      setTimeout(once, 500);
    } else {
      done();
    }
  }

  onKeydown(e) {
    if (e.key === 'Escape') this.close();
  }

  // Keeps focus inside the dialog without cataloguing every focusable node.
  onFocusIn(e) {
    if (!this.isOpen || this.contains(e.target)) return;
    const first = this.panel && this.panel.querySelector('[data-hs-cart-close]');
    if (first) first.focus();
  }

  lockScroll() {
    this.scrollY = window.scrollY;
    document.body.style.overflow = 'hidden';

    /*
      Compensate for a classic scrollbar so the page does not shift sideways.
      Measured from the body, not the window: window.innerWidth and
      documentElement.clientWidth disagree wildly under device emulation, and
      the difference was being applied as a very large padding.
    */
    const bar = document.documentElement.clientWidth - document.body.clientWidth;
    if (bar > 0 && bar < 40) document.body.style.paddingRight = `${bar}px`;
  }

  unlockScroll() {
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
  }
}

if (!customElements.get('hs-cart-drawer')) customElements.define('hs-cart-drawer', HSCartDrawer);

/*
 * Cart page steppers.
 *
 * The − and + on /cart are real submit buttons in real forms, so the page
 * works with no script at all — one reload per change. This upgrade keeps
 * those forms exactly as they are and intercepts the submit: the same
 * change goes to Shopify's cart endpoint with the page's own cart section
 * requested back in the round trip, and the server-rendered result is
 * swapped in place. Same rule as the drawer: the script never computes a
 * price — it only moves HTML the server wrote.
 *
 * The section id is read from the wrapper Shopify renders around the
 * template section, so this needs no configuration and survives the
 * template id changing.
 */
(function enhanceCartPage() {
  const layout = document.querySelector('.hs-cart__layout');
  if (!layout) return;
  const wrapper = layout.closest('[id^="shopify-section-"]');
  if (!wrapper) return;
  const sectionId = wrapper.id.replace('shopify-section-', '');
  const root = window.Shopify?.routes?.root || '/';

  document.addEventListener('submit', async (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (!form.classList.contains('hs-cart__stepper')) return;

    const line = form.querySelector('[name="line"]')?.value;
    const quantity = e.submitter?.value;
    if (line === undefined || quantity === undefined) return; // no-JS path

    e.preventDefault();
    wrapper.classList.add('is-busy');
    try {
      const res = await fetch(`${root}cart/change.js`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          line: Number(line),
          quantity: Number(quantity),
          sections: sectionId,
        }),
      });
      const data = await res.json();
      const html = data.sections && data.sections[sectionId];
      if (!html) throw new Error('no section in response');

      const doc = new DOMParser().parseFromString(html, 'text/html');
      const fresh = doc.body.firstElementChild;
      wrapper.innerHTML = fresh ? fresh.innerHTML : html;

      document.querySelectorAll('[data-hs-cart-count]').forEach((el) => {
        el.textContent = data.item_count;
        el.hidden = data.item_count === 0;
      });
    } catch {
      // The server is the only thing that knows the cart now; fall back to
      // the full page the form would have produced anyway.
      form.submit();
    } finally {
      wrapper.classList.remove('is-busy');
    }
  });
})();
