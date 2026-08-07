#!/usr/bin/env python3
"""Applies the brief's structural changes 3.2, 3.5 and 3.6 across the theme.

Idempotent: running it twice changes nothing the second time.

3.2 The buy widget moves below the argument on every page except the product
    page, and comes off two pages entirely. Its position was the problem, not
    the widget — at the top it interrupts the persuasion and buries the copy the
    page was written to rank for.
3.5 Wudu joins the header menu, and the menu is renamed to match: it lists a use
    that is not a sport, so "Shop by Activity" was the wrong label for it.
3.6 The footer's legal bar gets the links that were written but unreachable.
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"


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


def read(path):
    raw = path.read_text()
    cut = _lead_comments(raw)
    header = raw[:cut]
    body = raw[cut:]
    return header, json.loads(body, object_pairs_hook=collections.OrderedDict)


def write(path, header, data):
    path.write_text(header + json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def rich(*paras):
    return "".join(f"<p>{p.strip()}</p>" for p in paras if p and p.strip())


def move_before(order, keys, anchor):
    """Moves `keys` (in order) to sit immediately before `anchor`."""
    rest = [k for k in order if k not in keys]
    if anchor not in rest:
        return order
    at = rest.index(anchor)
    return rest[:at] + list(keys) + rest[at:]


def log(msg):
    print(f"  {msg}")


# --------------------------------------------------------------------- 3.5 nav
def nav_and_label():
    path = ROOT / "sections/header-group.json"
    header, d = read(path)
    for sec in d["sections"].values():
        if sec.get("type") != "header":
            continue
        blocks, order = sec["blocks"], sec["block_order"]

        for b in blocks.values():
            if b.get("type") == "dropdown" and "Activity" in (b["settings"].get("label") or ""):
                b["settings"]["label"] = "Shop by Use"

        # Wudu leads the panel: it is the one use no competitor covers, and until
        # now it could only be reached from the footer.
        if "act_wudu" not in blocks:
            blocks["act_wudu"] = collections.OrderedDict([
                ("type", "dropdown_item"),
                ("settings", collections.OrderedDict([
                    ("label", "Wudu & Masah"),
                    ("description", "Wudu at work, five times a day, without taking your socks off."),
                    ("link", "/pages/wudu-socks"),
                    ("image_fallback", "activity-wudu-masah.webp"),
                    ("image_alt", "Pulling on a pair of white HydroSox while seated"),
                    ("focal_point", "50% 70%"),
                    ("image_zoom", 100),
                    ("full_width", True),
                ])),
            ])
            # Directly after the dropdown it belongs to, so it renders first.
            trigger = next(k for k in order if blocks[k].get("type") == "dropdown")
            order.insert(order.index(trigger) + 1, "act_wudu")
            log("nav: added Wudu & Masah as the leading dropdown item")
        log("nav: dropdown renamed to Shop by Use")
    write(path, header, d)


def homepage_label():
    path = TPL / "index.json"
    header, d = read(path)
    act = d["sections"]["activity"]["settings"]
    act["eyebrow"] = "Shop by use"
    act["footnote"] = (
        "Same sock either way — the use only changes which pair you reach for. "
        "No certificate has been issued for the wudu claim, and the wudu page "
        "says so on its face."
    )
    write(path, header, d)
    log("homepage: section eyebrow back to Shop by use, footnote follows it")


# --------------------------------------------------------------------- 3.2 buy
ACTIVITY_PAGES = ["hiking-and-walking", "all-day-in-boots",
                  "running-and-trail", "cycling-and-commuting"]


def activity_buy_position():
    """Buy and reviews drop below the argument, immediately before the FAQ.

    The reader arriving on "waterproof walking socks" met a headline, a spec bar
    and then a purchase widget for a product nobody had given them a reason to
    trust. Now the problem, the answer, the use and the limits come first.
    """
    for handle in ACTIVITY_PAGES:
        path = TPL / f"page.{handle}.json"
        header, d = read(path)
        order = d["order"]
        if "buy" not in order or "faq" not in order:
            continue
        d["order"] = move_before(order, ["reviews", "buy"], "faq")
        write(path, header, d)
    log(f"activity pages: buy + reviews moved below the argument ({len(ACTIVITY_PAGES)} pages)")


def guides_remove_buy():
    """A content hub links to content. It does not sell."""
    path = TPL / "templates" if False else TPL / "blog.guides.json"
    header, d = read(path)
    if "buy" in d["sections"]:
        del d["sections"]["buy"]
        d["order"] = [k for k in d["order"] if k != "buy"]
        log("guides: buy widget removed")
    if "close" not in d["sections"]:
        d["sections"]["close"] = collections.OrderedDict([
            ("type", "closing-cta"),
            ("settings", collections.OrderedDict([
                ("color_scheme", "paper"),
                ("show_rule", False),
                ("eyebrow", "When you have read enough"),
                ("heading", "The socks these guides are about."),
                ("body", rich("One product, four sizes, from £20 a pair.")),
                ("cta_label", "See the socks"),
                ("cta_url", "/products/hydrosox-waterproof-socks"),
                ("alt_label", "How they are built"),
                ("alt_url", "/pages/technology"),
            ])),
        ])
        d["order"].append("close")
        log("guides: one closing text CTA added in its place")
    write(path, header, d)


def care_remove_buy():
    """This page serves people who already own a pair."""
    path = TPL / "page.care-and-washing.json"
    header, d = read(path)
    if "buy" in d["sections"]:
        del d["sections"]["buy"]
        d["order"] = [k for k in d["order"] if k != "buy"]
        log("care-and-washing: buy widget removed")
    if "tail" not in d["sections"]:
        d["sections"]["tail"] = collections.OrderedDict([
            ("type", "centre-note"),
            ("settings", collections.OrderedDict([
                ("color_scheme", "wash"),
                ("hide_rule", True),
                ("max_width", 44),
                ("heading_size", "h3"),
                ("heading", "Worn one out?"),
                ("body", rich(
                    "A membrane does not last forever, and washing it wrongly ends it "
                    "sooner. If yours has reached the end, the replacement is the same "
                    "sock at the same price."
                )),
                ("link_label", "HydroSox Waterproof Socks"),
                ("link_url", "/products/hydrosox-waterproof-socks"),
            ])),
        ])
        d["order"].append("tail")
        log("care-and-washing: replaced with a text link to the product")
    write(path, header, d)


def masah_quiet_cta():
    """A single quiet strip. A purchase widget under scholarly reporting reads
    as though the reporting were the sales pitch, which is the one impression
    this page cannot afford."""
    path = TPL / "page.how-to-make-masah.json"
    header, d = read(path)
    if "buy" in d["sections"]:
        del d["sections"]["buy"]
        d["order"] = [k for k in d["order"] if k != "buy"]
        log("masah: buy widget removed")
    if "quiet" not in d["sections"]:
        d["sections"]["quiet"] = collections.OrderedDict([
            ("type", "centre-note"),
            ("settings", collections.OrderedDict([
                ("color_scheme", "paper"),
                ("hide_rule", True),
                ("max_width", 44),
                ("heading_size", "h3"),
                ("eyebrow", "The socks"),
                ("heading", "Three physical properties, stated as product facts."),
                ("body", rich(
                    "Waterproof, holding their shape, and staying on the foot. Whether "
                    "that satisfies the conditions above is a question for your own "
                    "scholar, not for us."
                )),
                ("cta_label", "Wudu socks"),
                ("cta_url", "/pages/wudu-socks"),
                ("link_label", "How they are built"),
                ("link_url", "/pages/technology"),
            ])),
        ])
        d["order"].append("quiet")
        log("masah: reduced to one quiet CTA strip")
    write(path, header, d)


# ------------------------------------------------------------------ 3.6 footer
def footer_legal():
    path = ROOT / "sections/footer-group.json"
    header, d = read(path)
    for sec in d["sections"].values():
        if sec.get("type") != "footer":
            continue
        blocks, order = sec["blocks"], sec["block_order"]
        existing = {(b["settings"].get("label") or "") for b in blocks.values()
                    if b.get("type") == "legal_link"}
        # Terms, refund and shipping are already wired to the real Shopify
        # policies and appear the moment those policies have text. These two have
        # no Shopify policy type, so they are pages.
        additions = [
            ("legal_cookies", "Cookie Policy", "/pages/cookie-policy"),
            ("legal_accessibility", "Accessibility", "/pages/accessibility"),
        ]
        added = []
        for key, label, url in additions:
            if label in existing:
                continue
            blocks[key] = collections.OrderedDict([
                ("type", "legal_link"),
                ("settings", collections.OrderedDict([
                    ("policy", "custom"), ("label", label), ("link", url)])),
            ])
            order.append(key)
            added.append(label)
        if added:
            log(f"footer: added legal links — {', '.join(added)}")
    write(path, header, d)


# --------------------------------------------------------- the two new pages
def new_pages():
    def note(**s):
        base = {"color_scheme": "paper"}
        base.update(s)
        return {"type": "centre-note", "settings": base}

    def items(pairs, **s):
        blocks, order = collections.OrderedDict(), []
        for i, (t, b) in enumerate(pairs, 1):
            blocks[f"i{i}"] = {"type": "item", "settings": {"title": t, "body": rich(b)}}
            order.append(f"i{i}")
        base = {"color_scheme": "paper", "layout": "list", "numbered": False}
        base.update(s)
        return {"type": "content-columns", "settings": base,
                "blocks": blocks, "block_order": order}

    def crumb(current, parent=None):
        s = {"color_scheme": "paper", "home_label": "Home", "current_label": current}
        if parent:
            s["parent_label"], s["parent_url"] = parent
        return {"type": "breadcrumb", "settings": s}

    # ------------------------------------------------------------ cookies
    path = TPL / "page.cookie-policy.json"
    if not path.exists():
        d = collections.OrderedDict([
            ("sections", collections.OrderedDict([
                ("crumb", crumb("Cookie policy")),
                ("intro", note(
                    heading_tag="h1", heading_size="h2", hide_rule=True, max_width=46,
                    eyebrow="Cookie policy",
                    heading="What this site stores on your device.",
                    body=rich(
                        "A cookie is a small file a website asks your browser to keep. "
                        "This store runs on Shopify, which sets the cookies that make a "
                        "cart and a checkout work at all, and we add nothing that is not "
                        "described below.",
                        "You can delete cookies or block them in your browser settings "
                        "at any time. Blocking the essential ones will stop the cart and "
                        "checkout working, because they are the mechanism by which those "
                        "remember what you are doing."
                    ))),
                ("kinds", items([
                    ("Strictly necessary",
                     "Set by Shopify so the basket remembers what is in it, the checkout "
                     "can carry you through payment, and the site can tell one visitor "
                     "from another for security. These cannot be turned off without "
                     "breaking the shop, and they are not used for advertising."),
                    ("Preferences",
                     "Remember choices you have made, such as accepting this notice, so "
                     "you are not asked again on every page."),
                    ("Analytics",
                     "Count visits and show which pages are read, in aggregate. We use "
                     "these to decide what to write next, not to identify anyone."),
                    ("Advertising",
                     "Used to measure or target advertising. If any are ever set on this "
                     "site, they will be named here first and asked for separately."),
                ], eyebrow="The kinds", heading="Four categories, and which we use.",
                   lede=rich(
                       "Grouped the way the regulations group them, so this can be "
                       "checked against them rather than taken on trust."))),
                ("control", note(
                    color_scheme="wash", heading_size="h3", max_width=44,
                    eyebrow="Your choices",
                    heading="How to see and change what is stored.",
                    body=rich(
                        "Every current browser lists the cookies a site has set and lets "
                        "you delete them, under privacy or site settings. Where consent "
                        "is required for a category, this site asks before setting it, "
                        "and a refusal is remembered."
                    ),
                    link_label="How we handle personal data",
                    link_url="/policies/privacy-policy")),
                ("close", note(
                    color_scheme="paper", hide_rule=True, max_width=44,
                    heading_size="h3",
                    heading="Questions about any of this reach a person.",
                    body=rich(
                        "Cookies are the least interesting thing on this site and the "
                        "easiest to get vague about, so if anything here is unclear, ask."
                    ),
                    cta_label="Contact us", cta_url="/pages/contact")),
            ])),
            ("order", ["crumb", "intro", "kinds", "control", "close"]),
        ])
        write(path, "/* Cookie policy, composed by scripts/apply-spec-structural.py. */\n", d)
        log("created page.cookie-policy")

    # ------------------------------------------------------ accessibility
    path = TPL / "page.accessibility.json"
    if not path.exists():
        d = collections.OrderedDict([
            ("sections", collections.OrderedDict([
                ("crumb", crumb("Accessibility")),
                ("intro", note(
                    heading_tag="h1", heading_size="h2", hide_rule=True, max_width=46,
                    eyebrow="Accessibility",
                    heading="What we have done, and what we have not.",
                    body=rich(
                        "This site was built to be usable with a keyboard, with a screen "
                        "reader, and at a text size you choose. That is a standard to be "
                        "held to rather than a badge, so what follows is specific enough "
                        "to check and it says where we fall short.",
                        "We aim at WCAG 2.2 level AA. We have not commissioned an "
                        "independent audit, so nothing here is a certification — it is a "
                        "description of decisions taken, and it will be corrected as "
                        "things are found."
                    ))),
                ("done", items([
                    ("Keyboard and focus",
                     "Every control can be reached and operated with a keyboard, focus "
                     "is always visible, and the menu and cart return focus to where you "
                     "left it when they close. There is a skip link to the main content."),
                    ("Text and zoom",
                     "Type is set in relative units, so the site follows your browser's "
                     "text size and reflows to 400% zoom without content being lost or "
                     "needing sideways scrolling."),
                    ("Colour and contrast",
                     "Body text and controls are checked against the AA contrast "
                     "threshold. Colour is never the only thing carrying meaning."),
                    ("Motion",
                     "Scroll-driven animation and the frame sequence stop when your "
                     "system asks for reduced motion. Nothing on the site moves or "
                     "autoplays without being asked."),
                    ("Structure and images",
                     "Headings are ordered rather than chosen for size, tables carry real "
                     "headers, forms have real labels, and images that carry meaning have "
                     "text alternatives."),
                ], eyebrow="Specifics", heading="Five things you can verify.",
                   lede=rich(
                       "Each of these is testable in a browser in a couple of minutes, "
                       "which is the point of listing them."))),
                ("gaps", note(
                    color_scheme="wash", heading_size="h3", max_width=46,
                    eyebrow="Where it falls short",
                    heading="Known gaps, stated rather than hidden.",
                    body=rich(
                        "The product film has no captions yet, because the films are not "
                        "finished. No independent audit has been carried out. And no "
                        "amount of care replaces testing with people who rely on assistive "
                        "technology, which we have not yet done."
                    ))),
                ("close", note(
                    color_scheme="paper", hide_rule=True, max_width=44,
                    heading_size="h3",
                    heading="Found something that does not work?",
                    body=rich(
                        "Tell us what you were trying to do and what happened, and we will "
                        "fix it and say when. A phone number and an email reach a person."
                    ),
                    cta_label="Contact us", cta_url="/pages/contact",
                    link_label="Company details", link_url="/pages/about")),
            ])),
            ("order", ["crumb", "intro", "done", "gaps", "close"]),
        ])
        write(path, "/* Accessibility statement, composed by scripts/apply-spec-structural.py. */\n", d)
        log("created page.accessibility")


def main():
    print("3.5 navigation and label")
    nav_and_label()
    homepage_label()
    print("3.2 buy widget position")
    activity_buy_position()
    guides_remove_buy()
    care_remove_buy()
    masah_quiet_cta()
    print("3.6 footer and new pages")
    footer_legal()
    new_pages()


if __name__ == "__main__":
    main()
