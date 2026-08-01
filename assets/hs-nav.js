/**
 * <hs-nav> — header navigation.
 *
 * Owns the mobile drawer (open, close, focus trap, scroll lock) and makes the
 * desktop dropdown usable by keyboard and touch, not hover alone.
 */
class HSNav extends HTMLElement {
  connectedCallback() {
    this.drawer = this.querySelector('.hs-drawer');
    this.panel = this.querySelector('.hs-drawer__panel');
    this.openButton = this.querySelector('[data-hs-nav-open]');

    this.onKeydown = this.onKeydown.bind(this);
    this.onFocusIn = this.onFocusIn.bind(this);

    this.querySelectorAll('[data-hs-nav-open]').forEach((el) =>
      el.addEventListener('click', () => this.open())
    );
    this.querySelectorAll('[data-hs-nav-close]').forEach((el) =>
      el.addEventListener('click', () => this.close())
    );

    // Any link inside the drawer closes it, including same-page anchors that
    // would otherwise leave the drawer covering the target.
    this.querySelectorAll('.hs-drawer a').forEach((link) =>
      link.addEventListener('click', () => this.close())
    );

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
    // Force a frame so the transition runs from the closed state.
    requestAnimationFrame(() => this.drawer.classList.add('is-open'));

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
    const bar = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.overflow = 'hidden';
    // Compensate for the scrollbar so the page does not shift sideways.
    if (bar > 0) document.body.style.paddingRight = `${bar}px`;
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
