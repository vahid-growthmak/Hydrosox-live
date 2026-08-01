# HydroSox — Shopify theme

A Shopify Online Store 2.0 theme replicating the approved HydroSox homepage design
([mockup](https://hydrosox-website.vercel.app/)) as editable sections and blocks.

Built for `hydrosox-rib9km9j.myshopify.com`. Passes `shopify theme check` with no offenses.

## Principles this theme is built to

**Nothing is hardcoded.** Every colour, font size, spacing step, easing curve, corner
radius, string, image, link and list is a theme setting or a block. There are no literal
colours or sizes in any `.css` or `.liquid` file — they all resolve to CSS custom
properties emitted from `config/settings_schema.json` by `snippets/hs-tokens.liquid`.

**The defaults are the design.** Out of the box the theme renders the approved design
exactly. The fluid type scale is generated from editable min/max sizes and reproduces the
mockup's compiled `clamp()` values character-for-character.

**No JavaScript libraries.** The mockup uses none, and neither does this. Interactivity is
six small native web components. Total added JS is a few kilobytes, unminified.

**Mobile first.** Every section is laid out for small screens and enhanced upward through
the design's own breakpoints (640 / 768 / 1024 / 1280 px).

## Structure

```
assets/
  hs-base.css        Reset, type roles, buttons, schemes, keyframes
  hs-chrome.css      Announcement bar, header, drawer, footer, sticky buy bar
  hs-home.css        Homepage sections
  hs-pages.css       Product, collection, cart, blog, search, account
  hs-nav.js          <hs-nav>       drawer, focus trap, mega menu
  hs-buy.js          <hs-buy>       colour/size/tier selection, live totals
  hs-layers.js       <hs-layers>    sticky scroll-scrub
  hs-accordion.js    <hs-accordion> FAQ height transitions
  hs-film.js         <hs-film>      film chapter switching
  hs-buybar.js       <hs-buybar>    sticky bar show/hide
  hs-reveal.js                      scroll-reveal fallback

sections/            15 homepage + chrome sections, 9 supporting page sections
snippets/            hs-tokens, hs-fluid, hs-image, hs-button, hs-icon,
                     hs-section-head, hs-index-number, hs-social,
                     hs-pagination, hs-product-card, hs-meta-social
config/              settings_schema.json (the design system), settings_data.json
locales/             en.default.json, en.default.schema.json
templates/           index.json plus the full required template set
```

## Homepage sections, in order

| Section | File | Repeating content |
| --- | --- | --- |
| Hero | `hero-split.liquid` | Spec strip rows |
| Buy widget | `buy-widget.liquid` | Colours, sizes, quantity tiers, detail rows, links, size-guide rows and notes |
| Comparison table | `comparison-table.liquid` | Criteria |
| Honest limits | `honest-limits.liquid` | Limitations (each with its own width and tint) |
| Product film | `product-film.liquid` | Chapters |
| Construction | `construction-layers.liquid` | Layers |
| Shop by activity | `activity-grid.liquid` | Activities |
| Feature band (wudu) | `feature-band.liquid` | — |
| Questions | `faq-accordion.liquid` | Questions |
| Company details | `company-details.liquid` | Detail rows |
| Newsletter offer | `newsletter-offer.liquid` | — |

Chrome lives in two section groups: `header-group.json` (announcement bar, header) and
`footer-group.json` (footer, sticky buy bar).

## How the buy widget is wired

Colours and sizes are read from the **product's own options** — the blocks only add
presentation (a swatch colour, a UK shoe range). Rename a value in Shopify and the widget
still renders it; the block simply stops decorating it.

Quantity tiers state a **discount**, not a finished price. The price shown is worked out
from the live variant price minus that discount, so it follows a price change automatically
and cannot drift from the matching automatic discount in Shopify.

Current ladder, at a £20.00 unit price:

| Tier | Discount | Total | Per pair |
| --- | --- | --- | --- |
| 1 pair | — | £20.00 | £20.00 |
| 2 pairs | £3.01 | £36.99 | £18.50 |
| 3 pairs | £7.01 | £52.99 | £17.66 |
| 4 pairs | £12.01 | £67.99 | £17.00 |
| 5 pairs | £20.01 | £79.99 | £16.00 |

Each tier is backed by an **automatic discount** in Shopify with a matching minimum
quantity. Shopify applies the single best qualifying discount, so the ladder resolves
correctly at every quantity. If you change a tier here, change the automatic discount to
match — the amounts are deliberately the same number in both places.

## Accessibility and motion

Native `<details>` for the FAQ and a native `<dialog>` for the size guide, so both work
before JavaScript runs. The comparison table is a real `<table>` with a proper header row.
The drawer traps focus and restores it on close. All motion sits behind
`prefers-reduced-motion`, and there is a master switch in theme settings as well.

Scroll reveals use a native scroll-driven timeline (`animation-timeline: view()`) where the
browser supports one — as the mockup does — and fall back to a single
`IntersectionObserver` elsewhere.

## One deliberate deviation from the mockup

The construction section's left-hand visual is a procedurally drawn `<canvas>` in the
mockup, so its artwork could not be extracted. It is rebuilt here as a scroll-driven
layered visual: one plane per layer that separates, tilts and scales with scroll progress.
Separation and tilt are section settings, and each layer takes its own image, so dropping
in real layer photography needs no code change.

## Local development

```bash
shopify theme check
```

```bash
shopify theme dev --store hydrosox-rib9km9j.myshopify.com
```

`theme dev` needs an interactive login the first time (`shopify auth login`).
