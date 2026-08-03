/**
 * Scroll reveal fallback.
 *
 * Browsers that support scroll-driven animations run the reveal entirely in
 * CSS (see the animation-timeline rule in hs-base.css), so this script does
 * nothing there. Everywhere else it toggles `.is-revealed` as elements enter
 * the viewport, producing the same result with one observer for the page.
 */
(() => {
  const SELECTOR = '.hs-reveal';

  // Native scroll-driven timelines handle this without JavaScript.
  const hasNativeTimeline =
    typeof CSS !== 'undefined' &&
    CSS.supports &&
    CSS.supports('animation-timeline', 'view()');

  const prefersReducedMotion =
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (hasNativeTimeline) return;

  // Without an observer, or with motion turned down, show everything at once.
  if (prefersReducedMotion || !('IntersectionObserver' in window)) {
    const revealAll = () =>
      document.querySelectorAll(SELECTOR).forEach((el) => el.classList.add('is-revealed'));
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', revealAll, { once: true });
    } else {
      revealAll();
    }
    return;
  }

  let reported = false;

  const observer = new IntersectionObserver(
    (entries) => {
      reported = true;
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add('is-revealed');
        observer.unobserve(entry.target);
      }
    },
    { rootMargin: '0px 0px -12% 0px', threshold: 0.08 }
  );

  const observe = (root = document) => {
    root.querySelectorAll(SELECTOR).forEach((el) => {
      if (el.classList.contains('is-revealed')) return;
      observer.observe(el);
    });
  };

  /*
    Safety net for an observer that never reports at all — a broken or heavily
    throttled implementation. Content must not depend on an animation firing, so
    in that case everything is shown. It only trips when nothing has been
    reported by then, which leaves a working observer free to keep animating
    content the reader has not reached yet.
  */
  window.setTimeout(() => {
    if (reported) return;
    document.querySelectorAll(SELECTOR).forEach((el) => el.classList.add('is-revealed'));
  }, 3000);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => observe(), { once: true });
  } else {
    observe();
  }

  // Sections re-render as the merchant edits them in the theme editor.
  document.addEventListener('shopify:section:load', (event) => observe(event.target));
})();
