/**
 * <hs-nav> — header navigation.
 *
 * Owns the mobile drawer (open, close, focus trap, scroll lock) and makes the
 * desktop dropdown usable by keyboard and touch, not hover alone.
 */
class HSNav extends HTMLElement {
  connectedCallback() {
    this.openButton = this.querySelector('[data-hs-nav-open]');

    /*
      The drawer is a sibling rather than a child: the header carries a
      backdrop-filter, which makes it the containing block for any fixed
      descendant. It is found through the burger's aria-controls, falling back
      to a search inside the component for anyone who nests it.
    */
    const drawerId = this.openButton && this.openButton.getAttribute('aria-controls');
    this.drawer =
      (drawerId && document.getElementById(drawerId)) || this.querySelector('.hs-drawer');
    this.panel = this.drawer && this.drawer.querySelector('.hs-drawer__panel');

    this.onKeydown = this.onKeydown.bind(this);
    this.onFocusIn = this.onFocusIn.bind(this);

    this.querySelectorAll('[data-hs-nav-open]').forEach((el) =>
      el.addEventListener('click', () => this.open())
    );
    const closers = this.drawer
      ? this.drawer.querySelectorAll('[data-hs-nav-close]')
      : this.querySelectorAll('[data-hs-nav-close]');
    closers.forEach((el) => el.addEventListener('click', () => this.close()));

    // Any link inside the drawer closes it, including same-page anchors that
    // would otherwise leave the drawer covering the target.
    if (this.drawer) {
      this.drawer
        .querySelectorAll('a')
        .forEach((link) => link.addEventListener('click', () => this.close()));
    }

    this.setupDropdowns();
  }

  disconnectedCallback() {
    document.removeEventListener('keydown', this.onKeydown);
    document.removeEventListener('focusin', this.onFocusIn);
    this.unlockScroll();
  }

  /* ---------------------------------------------------------------- drawer */

  get isOpen() {
    return this.drawer && !this.drawer.hasAttribute('hidden');
  }

  open() {
    if (!this.drawer || this.isOpen) return;

    this.drawer.removeAttribute('hidden');

    /*
      Flush layout so the transition has a closed state to run from, then open
      synchronously. This used to wait a frame, which meant the drawer never
      opened anywhere requestAnimationFrame is throttled or never fires — a
      background tab, some in-app webviews. Whether the panel slides is
      cosmetic; whether the menu opens is not.
    */
    void this.drawer.offsetWidth;
    this.drawer.classList.add('is-open');

    if (this.openButton) this.openButton.setAttribute('aria-expanded', 'true');
    this.lockScroll();

    document.addEventListener('keydown', this.onKeydown);
    document.addEventListener('focusin', this.onFocusIn);

    const first = this.focusable()[0];
    if (first) first.focus();
  }

  close() {
    if (!this.drawer || !this.isOpen) return;

    this.drawer.classList.remove('is-open');
    if (this.openButton) {
      this.openButton.setAttribute('aria-expanded', 'false');
      this.openButton.focus();
    }
    this.unlockScroll();

    document.removeEventListener('keydown', this.onKeydown);
    document.removeEventListener('focusin', this.onFocusIn);

    const finish = () => this.drawer.setAttribute('hidden', '');
    const motionOk = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (motionOk && this.panel) {
      let settled = false;
      const once = () => {
        if (settled) return;
        settled = true;
        finish();
      };
      this.panel.addEventListener('transitionend', once, { once: true });
      // Guard against a missed transitionend leaving the drawer stuck open.
      setTimeout(once, 500);
    } else {
      finish();
    }
  }

  onKeydown(event) {
    if (event.key === 'Escape') {
      event.preventDefault();
      this.close();
      return;
    }
    if (event.key !== 'Tab') return;

    const items = this.focusable();
    if (!items.length) return;

    const first = items[0];
    const last = items[items.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  // Keeps focus inside the dialog even if something outside steals it.
  onFocusIn(event) {
    if (!this.isOpen || !this.panel) return;
    if (this.panel.contains(event.target)) return;
    const first = this.focusable()[0];
    if (first) first.focus();
  }

  focusable() {
    if (!this.panel) return [];
    return Array.from(
      this.panel.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])'
      )
    ).filter((el) => el.offsetParent !== null);
  }

  lockScroll() {
    this.scrollY = window.scrollY;
    document.body.style.overflow = 'hidden';

    /*
      Compensate for a classic scrollbar so the page does not shift sideways as
      it locks. The width has to be sanity-checked rather than trusted: inside
      a device-emulation frame, or on a zoomed mobile viewport, innerWidth and
      clientWidth describe different things and the difference can come out in
      the hundreds — which would pad the body far enough to crush the layout
      into a strip. No real scrollbar is wider than about 24px.
    */
    const bar = window.innerWidth - document.documentElement.clientWidth;
    if (bar > 0 && bar <= 24) document.body.style.paddingRight = `${bar}px`;
  }

  unlockScroll() {
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
  }

  /* -------------------------------------------------------------- dropdown */

  setupDropdowns() {
    this.querySelectorAll('.hs-header__group').forEach((group) => {
      const trigger = group.querySelector('[data-hs-dropdown-trigger]');
      if (!trigger) return;

      const setState = (open) => {
        group.classList.toggle('is-open', open);
        trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
      };

      // On touch, the first tap opens the panel rather than following the link.
      trigger.addEventListener('click', (event) => {
        const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
        if (finePointer) return;
        if (!group.classList.contains('is-open')) {
          event.preventDefault();
          setState(true);
        }
      });

      group.addEventListener('mouseenter', () => setState(true));
      group.addEventListener('mouseleave', () => setState(false));
      group.addEventListener('focusin', () => setState(true));
      group.addEventListener('focusout', (event) => {
        if (!group.contains(event.relatedTarget)) setState(false);
      });
      group.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && group.classList.contains('is-open')) {
          setState(false);
          trigger.focus();
        }
      });
    });
  }
}

if (!customElements.get('hs-nav')) customElements.define('hs-nav', HSNav);
