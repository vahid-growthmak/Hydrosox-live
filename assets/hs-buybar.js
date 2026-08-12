/**
 * <hs-buybar> — sticky buy bar.
 *
 * Appears once the visitor has scrolled past a configurable fraction of the
 * viewport, and retracts while the main buy widget is on screen so there is
 * never a duplicate call to action competing with the real one.
 */
class HSBuyBar extends HTMLElement {
  connectedCallback() {
    const showAfter = parseFloat(this.dataset.showAfter || '80') / 100;
    this.threshold = () => window.innerHeight * showAfter;

    this.targetInView = false;
    this.scrolledEnough = false;

    this.watchTarget();
    this.mirrorWidget();

    this.onScroll = this.onScroll.bind(this);
    window.addEventListener('scroll', this.onScroll, { passive: true });
    window.addEventListener('resize', this.onScroll, { passive: true });
    this.onScroll();
  }

  disconnectedCallback() {
    window.removeEventListener('scroll', this.onScroll);
    window.removeEventListener('resize', this.onScroll);
    if (this.observer) this.observer.disconnect();
    if (this.mirror) this.mirror.disconnect();
  }

  /**
   * Keeps the bar's form in step with the buy widget.
   *
   * The bar posts a real add-to-cart, so it has to post the variant and the
   * quantity the visitor actually chose rather than the ones the page loaded
   * with. The widget owns that state in two hidden inputs; this copies them
   * across whenever they change, and turns the button off while the chosen
   * variant is unavailable so the bar cannot offer what the widget refuses.
   *
   * Absent widget, absent form, or no MutationObserver: the bar keeps whatever
   * the server rendered, which is the first available variant. Still a valid
   * add, just not a synced one.
   */
  mirrorWidget() {
    const variantOut = this.querySelector('[data-hs-bar-variant]');
    const qtyOut = this.querySelector('[data-hs-bar-quantity]');
    const addBtn = this.querySelector('[data-hs-bar-add]');
    if (!variantOut) return;

    const variantIn = document.querySelector('[data-hs-variant-id]');
    const qtyIn = document.querySelector('[data-hs-quantity]');
    const submitIn = document.querySelector('[data-hs-submit]');
    if (!variantIn) return;

    const buyNow = this.querySelector('[data-hs-bar-buy]');
    const sync = () => {
      if (variantIn.value) variantOut.value = variantIn.value;
      if (qtyOut && qtyIn && qtyIn.value) qtyOut.value = qtyIn.value;
      if (addBtn && submitIn) addBtn.disabled = submitIn.disabled;
      // Buy now is a cart permalink, so the URL *is* the order: it has to
      // carry the same variant and quantity the widget shows.
      if (buyNow && variantOut.value) {
        const qty = (qtyOut && qtyOut.value) || '1';
        buyNow.href = '/cart/' + variantOut.value + ':' + qty;
      }
    };
    sync();

    if (!('MutationObserver' in window)) return;
    this.mirror = new MutationObserver(sync);
    this.mirror.observe(variantIn, { attributes: true, attributeFilter: ['value'] });
    if (qtyIn) this.mirror.observe(qtyIn, { attributes: true, attributeFilter: ['value'] });
    if (submitIn) this.mirror.observe(submitIn, { attributes: true, attributeFilter: ['disabled'] });

    // The widget sets .value in script, which does not fire a mutation for the
    // attribute on every browser — a cheap input/change listener covers it.
    ['input', 'change'].forEach((evt) => {
      variantIn.addEventListener(evt, sync);
      if (qtyIn) qtyIn.addEventListener(evt, sync);
    });
    // And the widget's own controls, whose clicks precede the value write.
    document.addEventListener('click', (e) => {
      if (e.target.closest('[data-hs-tier], [data-hs-option]')) {
        requestAnimationFrame(sync);
      }
    });
  }

  // Watches the buy widget, if the merchant pointed at one.
  watchTarget() {
    const selector = (this.dataset.hideNear || '').trim();
    if (!selector || !('IntersectionObserver' in window)) return;

    let target = null;
    try {
      target = document.querySelector(selector);
    } catch {
      // An invalid selector should not break the bar.
      return;
    }
    if (!target) return;

    this.observer = new IntersectionObserver(
      (entries) => {
        this.targetInView = entries.some((entry) => entry.isIntersecting);
        this.apply();
      },
      { threshold: 0 }
    );
    this.observer.observe(target);
  }

  onScroll() {
    if (this.frame) return;
    this.frame = requestAnimationFrame(() => {
      this.frame = null;
      this.scrolledEnough = window.scrollY > this.threshold();
      this.apply();
    });
  }

  apply() {
    const visible = this.scrolledEnough && !this.targetInView;
    this.classList.toggle('is-visible', visible);
    // Keep the offscreen bar out of the tab order.
    this.querySelectorAll('a, button').forEach((el) => {
      if (visible) el.removeAttribute('tabindex');
      else el.setAttribute('tabindex', '-1');
    });
  }
}

if (!customElements.get('hs-buybar')) customElements.define('hs-buybar', HSBuyBar);
