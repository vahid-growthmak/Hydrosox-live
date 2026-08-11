/**
 * Folds the footer's link columns on small screens.
 *
 * The columns are <details open> in the markup, because a closed <details>
 * hides its content regardless of any CSS applied to it — so the wide layout
 * cannot be recovered by a media query alone. Folding is therefore done here,
 * and only below the breakpoint. With the script absent the footer is long but
 * completely readable, which is the right way round for a failure.
 *
 * The breakpoint is 64rem, matching the width at which the CSS lays the four
 * columns out side by side. Tablets fold too: below that the columns cannot
 * all fit in a row, and half-open accordions in a two-up grid read worse than
 * a plain stacked list of headings.
 */
(() => {
  const BREAKPOINT = '(min-width: 64rem)';
  const wide = window.matchMedia(BREAKPOINT);

  const apply = () => {
    document.querySelectorAll('.hs-footer__col').forEach((col) => {
      // Never leave a column that the reader opened themselves closed on a
      // wide screen, and never leave all four open on a handset.
      col.open = wide.matches;
    });
  };

  const start = () => {
    apply();
    wide.addEventListener('change', apply);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }

  // Sections re-render as the merchant edits them in the theme editor.
  document.addEventListener('shopify:section:load', apply);
})();
