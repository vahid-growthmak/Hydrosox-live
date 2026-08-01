/**
 * <hs-accordion> — height transition for native <details> panels.
 *
 * The markup works without this: <details> already opens and closes, and the
 * answers are findable by the browser's find-in-page. This only animates the
 * height and, when `data-single` is set, closes the other panels.
 */
class HSAccordion extends HTMLElement {
  connectedCallback() {
    this.single = this.hasAttribute('data-single');
    this.items = Array.from(this.querySelectorAll('details'));

    this.items.forEach((item) => {
      const summary = item.querySelector('summary');
      const wrap = item.querySelector('.hs-faq__answer-wrap');
      if (!summary || !wrap) return;

      summary.addEventListener('click', (event) => {
        // Let the browser handle it outright when motion is turned down.
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
          if (this.single && !item.open) this.closeOthers(item);
          return;
        }

        event.preventDefault();

        if (item.open) this.collapse(item, wrap);
        else {
          if (this.single) this.closeOthers(item);
          this.expand(item, wrap);
        }
      });
    });
  }

  expand(item, wrap) {
    item.open = true;
    const target = wrap.scrollHeight;
    wrap.style.height = '0px';
    // Next frame, so the browser has a start value to animate from.
    requestAnimationFrame(() => {
      wrap.style.height = `${target}px`;
    });

    const done = () => {
      wrap.style.height = '';
      wrap.removeEventListener('transitionend', done);
    };
    wrap.addEventListener('transitionend', done);
  }

  collapse(item, wrap) {
    const start = wrap.scrollHeight;
    wrap.style.height = `${start}px`;
    requestAnimationFrame(() => {
      wrap.style.height = '0px';
    });

    const done = (event) => {
      if (event.propertyName !== 'height') return;
      item.open = false;
      wrap.style.height = '';
      wrap.removeEventListener('transitionend', done);
    };
    wrap.addEventListener('transitionend', done);
  }

  closeOthers(current) {
    this.items.forEach((item) => {
      if (item === current || !item.open) return;
      const wrap = item.querySelector('.hs-faq__answer-wrap');
      if (wrap && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        this.collapse(item, wrap);
      } else {
        item.open = false;
      }
    });
  }
}

if (!customElements.get('hs-accordion')) customElements.define('hs-accordion', HSAccordion);
