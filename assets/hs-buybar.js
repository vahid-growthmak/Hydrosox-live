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

    this.onScroll = this.onScroll.bind(this);
    window.addEventListener('scroll', this.onScroll, { passive: true });
    window.addEventListener('resize', this.onScroll, { passive: true });
    this.onScroll();
  }

  disconnectedCallback() {
    window.removeEventListener('scroll', this.onScroll);
    window.removeEventListener('resize', this.onScroll);
    if (this.observer) this.observer.disconnect();
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
