/**
 * <hs-accordion> — height transition for native <details> panels.
 *
 * The markup works without this: <details> already opens and closes, and the
 * answers are findable by the browser's find-in-page. This only animates the
 * height and, when `data-single` is set, closes the other panels.
 *
 * Every state change settles on a timer as well as on `transitionend`. A
 * transition that never runs — a tab sent to the background mid-tap, so
 * requestAnimationFrame is frozen; a `transitioncancel` from a second tap — must
 * not be able to strand a panel with `open` set and its wrap still clamped to
 * 0px, because from that state the next tap collapses again and the row never
 * reopens.
 */
class HSAccordion extends HTMLElement {
  connectedCallback() {
    this.single = this.hasAttribute('data-single');
    this.items = Array.from(this.querySelectorAll('details'));
    this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    this.items.forEach((item) => {
      const summary = item.querySelector('summary');
      const wrap = item.querySelector('.hs-faq__answer-wrap');
      if (!summary || !wrap) return;

      summary.addEventListener('click', (event) => {
        // Let the browser handle it outright when motion is turned down.
        if (this.reducedMotion.matches) {
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
    // Settle any pending collapse before opening, never after: its settle sets
    // `open` to false, which would undo the line below.
    this.cancel(wrap);
    item.open = true;
    // scrollHeight is the content height whatever the wrap is clamped to, so
    // this reads correctly even when a stranded panel left an inline 0px behind.
    const target = wrap.scrollHeight;
    // Always from zero. A closed panel shows nothing on screen, whatever its box
    // reports — Chrome gives the content of a closed <details> a full-height box.
    this.animate(wrap, 0, target, () => {
      wrap.style.height = '';
    });
  }

  collapse(item, wrap) {
    // Measured before cancelling, so a collapse interrupting a half-finished
    // expand carries on from the height on screen rather than jumping to full.
    const from = this.currentHeight(wrap);
    this.cancel(wrap);
    this.animate(wrap, from, 0, () => {
      item.open = false;
      wrap.style.height = '';
    });
  }

  /** Runs a pending settle early, so a new transition starts from a clean state. */
  cancel(wrap) {
    if (wrap.hsSettle) wrap.hsSettle();
  }

  /**
   * Transitions the wrap's height and runs `settle` once it is over, however it
   * ends — completed, cancelled, or never started at all.
   */
  animate(wrap, from, to, settle) {
    let done = false;
    // Transition events are only ours once the target is set. The transition we
    // just replaced fires `transitioncancel` at us, and acting on it would settle
    // this one before it had started — leaving the height we set behind for good.
    let armed = false;

    const finish = () => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      wrap.removeEventListener('transitionend', onEnd);
      wrap.removeEventListener('transitioncancel', onCancel);
      wrap.hsSettle = null;
      settle();
    };

    // Only this element's own height, not a child's transition bubbling up.
    const onEnd = (event) => {
      if (!armed) return;
      if (event.target === wrap && event.propertyName === 'height') finish();
    };
    const onCancel = () => {
      if (armed) finish();
    };

    wrap.style.height = `${from}px`;
    wrap.addEventListener('transitionend', onEnd);
    wrap.addEventListener('transitioncancel', onCancel);
    const timer = setTimeout(finish, this.duration(wrap) + 120);
    wrap.hsSettle = finish;

    // Next frame, so the browser has a start value to animate from.
    requestAnimationFrame(() => {
      wrap.style.height = `${to}px`;
      armed = true;
    });
  }

  /** The height the wrap is rendering at right now. */
  currentHeight(wrap) {
    return Math.round(wrap.getBoundingClientRect().height);
  }

  /** The wrap's own transition duration, in ms, so the fallback tracks the CSS. */
  duration(wrap) {
    const first = (getComputedStyle(wrap).transitionDuration || '0s').split(',')[0].trim();
    const value = parseFloat(first) || 0;
    return first.endsWith('ms') ? value : value * 1000;
  }

  closeOthers(current) {
    this.items.forEach((item) => {
      if (item === current || !item.open) return;
      const wrap = item.querySelector('.hs-faq__answer-wrap');
      if (wrap && !this.reducedMotion.matches) {
        this.collapse(item, wrap);
      } else {
        item.open = false;
      }
    });
  }
}

if (!customElements.get('hs-accordion')) customElements.define('hs-accordion', HSAccordion);
