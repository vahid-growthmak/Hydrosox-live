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
    "the warranty page": "/pages/warranty",
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


def load(path):
    raw = path.read_text()
    m = re.match(r"^\s*/\*[\s\S]*?\*/\s*", raw)
    header = raw[: m.end()] if m else ""
    return header, json.loads(raw[m.end():] if m else raw,
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

        # An in-page anchor is only offered where the page actually has one.
        buy_anchor = None
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
                if not label or st.get(url):
                    continue

                target = DESTINATIONS.get(str(label).strip().lower())
                if target is None:
                    unknown.append((path.name, key, lab, label))
                    continue
                if target == "#buy":
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
