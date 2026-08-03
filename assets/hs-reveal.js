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

  const observer = new IntersectionObserver(
    (entries) => {
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
    Safety net. Content must never depend on an animation firing: if the
    observer has not reported anything in a few seconds — a broken or throttled
    implementation, a background tab that never composites — everything is shown
    regardless. Losing the entrance animation is fine; losing the page is not.
  */
  window.setTimeout(() => {
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
