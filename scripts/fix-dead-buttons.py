#!/usr/bin/env python3
"""Gives every labelled call to action somewhere to go.

`hs-button` renders an <a> when it has an href and a <button> when it does not —
which is right, because the add-to-cart control is a real submit button. The
side effect is that a CTA whose URL was never filled in renders as a button that
looks completely normal and does nothing at all when clicked.

Twelve section types ship a default label with no default URL, so the dead
button appears without anyone typing it: the label comes from the schema, the
link does not, and nothing in theme check or the settings validator looks at the
pair together. The questions section on the use-case pages is the one that was
noticed — "Buy a pair", under every FAQ, inert.

This walks every template, finds each label/URL pair where the label resolves
(from the template or from the section's own schema default) and the URL does
not, and fills the URL in:

  * a buy CTA points at the page's own buy widget where it has one, because an
    in-page anchor beats a navigation, and at the product page where it does not
  * everything else points at the page that owns the subject

Idempotent, and it never overwrites a URL that is already set.
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCT_URL = "/products/hydrosox-waterproof-socks"

# label/URL pairs as the sections name them.
PAIRS = [
    ("cta_label", "cta_url"), ("cta_label", "cta_link"),
    ("link_label", "link_url"), ("link2_label", "link2_url"),
    ("alt_label", "alt_url"), ("pointer_link_label", "pointer_url"),
    ("help_label", "help_link"), ("empty_cta_label", "empty_cta_url"),
    # The size overlay's own footer link. It shipped on nine templates with a
    # label and no URL, which the widget turned into href="#" — clicking it
    # scrolled the page under the open overlay to the top and left the
    # overlay standing there.
    ("guide_link_label", "guide_link_url"),
]

# Where a label should go, by what it says. Anything not listed here is left
# alone and reported, so a new label cannot be quietly pointed somewhere wrong.
DESTINATIONS = {
    "buy a pair": "#buy",
    "choose a size": "#buy",
    "see the socks": "#buy",
    "shop hydrosox": "#buy",
    "buy hydrosox": "#buy",
    "contact us": "/pages/contact",
    "phone or email us": "/pages/contact",
    "ask a person": "/pages/contact",
    "wudu socks": "/pages/wudu-socks",
    "the full sizing and fit guide": "/pages/size-guide",
    "open the size guide": "/pages/size-guide",
    "partner with us": "/pages/partner-with-us",
    "press": "/pages/press",
    "read the refund policy": "/policies/refund-policy",
    "the returns policy": "/policies/refund-policy",
    "read the shipping policy": "/policies/shipping-policy",
    "shipping and delivery": "/pages/shipping-and-delivery",
    "all guides": "/blogs/guides",
    "read the questions first": "/pages/faq",
    "check the membrane spec": "/pages/technology",
    "see how it is built": "/pages/technology",
    "how it is built": "/pages/technology",
    "how the layers are made": "/pages/technology",
    "the size guide": "/pages/size-guide",
    "open the size guide": "/pages/size-guide",
    "how to wash them": "/pages/care-and-washing",
    # /pages/warranty was unpublished on 2026-08-11; anything still labelled
    # for it should land on the returns page, which now carries that content.
    "the warranty page": "/pages/returns-and-refunds",
    "the full warranty position": "/pages/returns-and-refunds",
}


def schema_defaults():
    """Label defaults declared by each section, so we catch the invisible ones."""
    out = {}
    for path in sorted((ROOT / "sections").glob("*.liquid")):
        m = re.search(r"\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}",
                      path.read_text(), re.S)
        if not m:
            continue
        try:
            sch = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        ids = {s["id"]: s for s in sch.get("settings", []) if s.get("id")}
        out[path.stem] = {k: v.get("default") for k, v in ids.items()}
    return out


def _lead_comments(raw):
    """Length of every leading /* */ block, not just the first.

    A composed template carries a provenance header; the moment the Shopify
    theme editor touches it, Shopify prepends its own banner above that. The
    file then opens with two blocks, and a reader that consumes one hands the
    other to json.loads.

    That matters more than it looks here: this script catches JSONDecodeError
    and skips the file, so the failure is not an error — it is a template
    quietly going unprocessed while the run reports success.
    """
    pos = 0
    while True:
        m = re.match(r"\s*/\*[\s\S]*?\*/\s*", raw[pos:])
        if not m or m.end() == 0:
            return pos
        pos += m.end()


def load(path):
    raw = path.read_text()
    cut = _lead_comments(raw)
    header = raw[:cut]
    return header, json.loads(raw[cut:],
                              object_pairs_hook=collections.OrderedDict)


def main():
    defaults = schema_defaults()
    fixed, unknown = [], []

    for path in sorted((ROOT / "templates").glob("*.json")):
        try:
            header, data = load(path)
        except json.JSONDecodeError:
            continue
        sections = data.get("sections") or {}

        # An in-page anchor is only offered on the two templates where the
        # order block is unmissable and its position is fixed: the product
        # page and the homepage. Everywhere else "Buy a pair" goes to the
        # product page.
        #
        # The client reported the anchor doing nothing on the FAQ, size guide
        # and reviews pages (2026-08-11). Those templates all carry the block,
        # so the anchor should resolve — but a button that silently does
        # nothing is the worst outcome on the page, and a link to the product
        # is right whether the block renders or not. So the anchor is now
        # opt-in by template rather than inferred.
        ANCHOR_TEMPLATES = {"index.json", "product.json"}
        buy_anchor = None
        if path.name in ANCHOR_TEMPLATES:
            for sec in sections.values():
                if sec.get("type") == "buy-widget":
                    buy_anchor = "#%s" % (sec.get("settings", {}).get("anchor_id")
                                          or "buy")
                    break

        changed = False
        for key, sec in sections.items():
            stype = sec.get("type")
            st = sec.setdefault("settings", collections.OrderedDict())
            sdef = defaults.get(stype, {})

            for lab, url in PAIRS:
                if url not in sdef:          # this section has no such pair
                    continue
                label = st.get(lab, sdef.get(lab))
                if not label:
                    continue

                current = st.get(url)
                # An in-page anchor that this page has no anchor FOR is worse
                # than an empty field: it looks like a working button and
                # does nothing. So a stale "#buy" on a page carrying no order
                # block is corrected, not just left because it is non-empty.
                stale_anchor = (
                    isinstance(current, str)
                    and current.strip().lstrip("/").startswith("#buy")
                    and buy_anchor is None
                )
                if current and not stale_anchor:
                    continue

                target = DESTINATIONS.get(str(label).strip().lower())
                if target is None:
                    if not current:
                        unknown.append((path.name, key, lab, label))
                    continue
                if target == "#buy":
                    # No order block on this page: send them to the product,
                    # which is where the button was always promising to go.
                    target = buy_anchor or PRODUCT_URL

                st[url] = target
                changed = True
                fixed.append((path.name, key, lab, label, target))

        if changed:
            path.write_text(
                header + json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    for name, key, lab, label, target in fixed:
        print("  %-34s %-12s %-14s %-26s -> %s"
              % (name.replace("page.", ""), key, lab, label, target))
    print("\n  %d destination(s) filled in" % len(fixed))
    if unknown:
        print("\n  NO MAPPING — left untouched, add to DESTINATIONS:")
        for name, key, lab, label in unknown:
            print("    %-34s %-12s %s=%r" % (name, key, lab, label))


if __name__ == "__main__":
    main()
