#!/usr/bin/env python3
"""Applies the Phase 6 content to the three policy pages the theme owns.

Four of the seven policies are not theme pages at all — refund, shipping, terms
and privacy live in Shopify's Settings → Policies and render through
templates/policy.json. Their text is in docs/policies/ ready to paste, because
the connector does not hold write_legal_policies and cannot set them by API.

The three here are ordinary pages, so they are built from the site's own
components like everything else:

  * Warranty — twelve months against manufacturing defects, on top of statutory
    rights rather than instead of them. The statutory content was already good
    and is kept; what it lacked was anything to say to the reader who decides on
    this page, whose only real objection is that a cheap pair failed in three
    weeks.
  * Cookie policy — required by PECR 2003 and previously absent in substance.
    The page can describe the categories now; the actual cookie table cannot be
    written until the tags exist, and a consent banner is a build task this
    page does not substitute for.
  * Accessibility — not mandatory for a private retailer, but an hour's work
    and entirely consistent with a site whose proposition is that it tells you
    the truth about itself.

No clause on any of these reduces or appears to reduce a statutory right. Where
the policy is more generous than the law, it says which part is which.

Idempotent.
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"


def rich(*paras):
    return "".join("<p>%s</p>" % p.strip() for p in paras if p and p.strip())


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


def read(name):
    raw = (TPL / name).read_text()
    cut = _lead_comments(raw)
    header = raw[:cut]
    return header, json.loads(raw[cut:],
                              object_pairs_hook=collections.OrderedDict)


def write(name, header, data):
    (TPL / name).write_text(
        header + json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def cols(anchor, eyebrow, heading, lede, entries, scheme="paper", link=None,
         footnote=None, numbered=False):
    blocks, order = collections.OrderedDict(), []
    for n, (t, b) in enumerate(entries, 1):
        k = "i%d" % n
        blocks[k] = collections.OrderedDict([
            ("type", "item"),
            ("settings", collections.OrderedDict([
                ("title", t), ("body", rich(b))]))])
        order.append(k)
    st = collections.OrderedDict([
        ("color_scheme", scheme), ("layout", "list"), ("numbered", numbered),
        ("anchor_id", anchor), ("eyebrow", eyebrow), ("heading", heading)])
    if lede:
        st["lede"] = rich(lede)
    if footnote:
        st["footnote"] = footnote
    if link:
        st["link_label"], st["link_url"] = link
    return collections.OrderedDict([
        ("type", "content-columns"), ("settings", st),
        ("blocks", blocks), ("block_order", order)])


# ===========================================================================
def warranty():
    header, d = read("page.warranty.json")
    S = d["sections"]

    S["intro"]["settings"].update({
        "heading": "Twelve months, on top of what the law already gives you.",
        "body": rich(
            "A warranty is an addition, never a replacement. Your statutory "
            "rights under the Consumer Rights Act 2015 apply in full "
            "regardless of anything on this page, and where the two differ the "
            "more generous one applies."),
    })

    S["rights"] = cols(
        "statutory", "What you already have", "What you already have",
        "None of this depends on us offering anything. It is the law, and it "
        "applies whether or not a brand adds to it.",
        [("Satisfactory quality, fit for purpose, as described",
          "The Consumer Rights Act 2015 requires all three. A sock that is not "
          "waterproof is not as described, and that is a fault however long "
          "you have had it."),
         ("Thirty days to reject outright",
          "A full refund, with no repair attempt required first."),
         ("Six months where the fault is presumed ours",
          "Within six months of delivery a fault is assumed to have been there "
          "from the start unless we can show otherwise."),
         ("Up to six years to bring a claim",
          "In England and Wales you have up to six years from purchase to "
          "bring a claim for goods that were faulty when sold. That is a "
          "limitation period rather than a promise that goods last six years — "
          "but it is longer than most people assume, and worth knowing.")])

    # The addition. It costs little in practice: it only bites on genuine
    # faults, which the Act already presumes ours for the first six months.
    # What it buys is confidence at the point of decision, from a brand nobody
    # has heard of.
    S["cover"] = cols(
        "warranty", "Our warranty", "Twelve months against manufacturing defects.",
        "Registered from the delivery date. No registration to complete and no "
        "card to post — the order is the proof of purchase.",
        [("What it covers",
          "Manufacturing defects: delamination, a failed seam, a membrane that "
          "leaks through the body of the sock in normal use, or a knit that "
          "comes apart where it was joined."),
         ("What it does not cover",
          "Wear, which is a different thing and is set out below. Damage from "
          "misuse or from the wrong care — tumble drying, ironing, direct "
          "heat, bleach and fabric softener all shorten or end a membrane, and "
          "the care instructions are published in full."),
         ("What we do about it",
          "A replacement pair, or a refund where we cannot replace. We do not "
          "charge for returning faulty goods at any point, inside the warranty "
          "or under your statutory rights."),
         ("It is not transferable",
          "The warranty is with the person who bought the socks. Your "
          "statutory rights work the same way.")],
        scheme="wash")

    S["fault"] = cols(
        "fault-or-wear", "Fault or wear", "Fault or wear",
        "This is the distinction every warranty turns on, so here it is in "
        "plain terms rather than buried.",
        [("A fault",
          "Delamination, a seam that lets water through, or a membrane that "
          "leaks in the first weeks of normal use."),
         ("Wear",
          "Thinning at the heel or toe over months of use, abrasion inside a "
          "boot, damage from toenails, or the consequences of the wrong wash "
          "cycle."),
         ("The honest line between them",
          "Time and pattern. A leak in week two, in the body of the sock "
          "rather than over the cuff, is almost always a fault. A gradual loss "
          "of performance over a year of daily use on a building site is "
          "almost always wear. If it is genuinely unclear, we will treat it as "
          "a fault.")])

    d["order"] = ["crumb", "intro", "rights", "cover", "fault", "contact", "buy"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("warranty: orphaned %s" % orphans)
    write("page.warranty.json", header, d)
    return "warranty", len(d["order"])


# ===========================================================================
def cookies():
    header, d = read("page.cookie-policy.json")
    S = d["sections"]

    S["intro"]["settings"].update({
        "heading": "What we set, and how to turn it off.",
        "body": rich(
            "Only the cookies needed to make the site work run without your "
            "permission. Everything else waits until you say yes, and you can "
            "change your mind at any time."),
    })

    S["kinds"] = cols(
        "categories", "The categories", "Three categories, and which need asking.",
        "The Privacy and Electronic Communications Regulations 2003 require "
        "consent before anything that is not strictly necessary. That is the "
        "line the three categories below are drawn on.",
        [("Strictly necessary — always on",
          "These make the site function: keeping your basket, remembering your "
          "session, processing payment and keeping the site secure. They "
          "cannot be switched off and do not require consent, because the site "
          "does not work without them."),
         ("Analytics — off until you agree",
          "These tell us how the site is used: which pages are read, where "
          "people leave, what is not working. They help us improve it. They do "
          "not run unless you accept them."),
         ("Marketing and advertising — off until you agree",
          "These let us measure advertising and show relevant ads elsewhere, "
          "including on Meta and Google platforms. They do not run unless you "
          "accept them.")])

    S["control"]["settings"].update({
        "eyebrow": "Your choices",
        "heading": "Changing your mind is as easy as agreeing was.",
        "body": rich(
            "Use the cookie settings link in the footer, available on every "
            "page. Withdrawing consent is exactly as easy as giving it, which "
            "is what the regulations require.",
            "Every major browser also lets you block or delete cookies "
            "directly. Blocking the strictly necessary ones will stop parts of "
            "this site working, including checkout."),
    })

    d["order"] = ["crumb", "intro", "kinds", "control", "close"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("cookies: orphaned %s" % orphans)
    write("page.cookie-policy.json", header, d)
    return "cookie-policy", len(d["order"])


# ===========================================================================
def accessibility():
    header, d = read("page.accessibility.json")
    S = d["sections"]

    S["intro"]["settings"].update({
        "heading": "What works, what does not, and who to tell.",
        "body": rich(
            "We want this site to be usable by everyone. It is not perfect, "
            "and this page says where it falls short rather than claiming it "
            "does not."),
    })

    S["done"] = cols(
        "what-we-have-done", "Specifics", "What we have done.",
        "We aim to meet the Web Content Accessibility Guidelines 2.1 at level "
        "AA — the standard used across UK public sector sites, and a "
        "reasonable bar for a retailer.",
        [("Text resizes without breaking",
          "Every size on this site is set in relative units, so enlarging text "
          "in your browser reflows the page rather than clipping it."),
         ("Images carry alternative text",
          "Every photograph describes what it shows, including the colour "
          "swatches, rather than repeating the file name."),
         ("It works from the keyboard",
          "Every menu, drawer and accordion can be reached and operated "
          "without a mouse, and focus is visible and returns where you left "
          "it."),
         ("Forms have real labels",
          "Visible labels rather than placeholder text alone, which disappears "
          "the moment you start typing."),
         ("Motion can be turned off",
          "Every animation on this site is behind the reduced-motion setting "
          "your device already has, and there is a switch in the theme as "
          "well.")])

    # Deliberately not a claim of full compliance. A statement with no known
    # issues is rarely true and is trivially disproved by anyone who looks.
    S["gaps"]["settings"].update({
        "eyebrow": "Where it falls short",
        "heading": "What we know is not right yet.",
        "body": rich(
            "This site has not yet had a full independent accessibility audit, "
            "so this section is honest rather than complete: we are listing "
            "what we know, not everything there is.",
            "Some muted text sits close to the AA contrast threshold rather "
            "than comfortably above it. The scroll-driven sections have been "
            "tested with motion turned off but not with every assistive "
            "technology. When the audit is done, what it finds will be "
            "published here — including the parts that are awkward."),
    })

    # A reasonable adjustment under the Equality Act 2010 that costs nothing,
    # and converts readers who would otherwise abandon.
    S["close"]["settings"].update({
        "heading": "Found something that does not work?",
        "body": rich(
            "Email info@hydrosox.com or phone +44 7441 396244. Tell us what you "
            "were trying to do and what happened, and we will tell you "
            "honestly whether and when we can fix it.",
            "If you would rather not use the site at all, phone us and we will "
            "take the order over the phone. There is no charge for that."),
    })

    d["order"] = ["crumb", "intro", "done", "gaps", "close"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("accessibility: orphaned %s" % orphans)
    write("page.accessibility.json", header, d)
    return "accessibility", len(d["order"])


def main():
    for fn in (warranty, cookies, accessibility):
        name, n = fn()
        print("  %-18s %s sections" % (name, n))


if __name__ == "__main__":
    main()
