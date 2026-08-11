#!/usr/bin/env python3
"""Applies the Phase 4 content to the four use-case pages.

As drawn, all four were the same page with a different photograph: hero, spec
bar, and the identical shared sections below. Each now carries its own argument
between the hero and the buy widget, written to its own reader — Helen's wet
boot, Tom's weight objection, Dan's overshoes, Mark's three-week failure.

The heroes are untouched: the brief is explicit that they are the best lines on
the site. The sitemap-mandated extras — breadcrumb, reviews, related guides,
the two sibling cards, the closing — are preserved from the existing files.

Idempotent. This script owns these four pages' content sections now; the old
build_activity() composition pass in build-sitemap-templates.py is retired,
because its reorder logic only knows the old section keys and would drop the
new ones.

One deliberate omission, per the brief's own rule: the Running page's weight
item contains placeholder figures ("[x] g"), and the brief says delete the item
rather than publish a placeholder or an adjective. It ships with the other two
items and returns when the client supplies the number.
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"

HUB = "/pages/waterproof-socks"


def rich(text):
    t = text.strip()
    return t if t.startswith("<") else f"<p>{t}</p>"


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


def read(handle):
    raw = (TPL / f"page.{handle}.json").read_text()
    cut = _lead_comments(raw)
    header = raw[:cut]
    return header, json.loads(raw[cut:],
                              object_pairs_hook=collections.OrderedDict)


def write(handle, header, data):
    (TPL / f"page.{handle}.json").write_text(
        header + json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def cols(eyebrow, heading, lede, entries, link=None, scheme="paper", numbered=False):
    blocks, order = collections.OrderedDict(), []
    for i, (title, body) in enumerate(entries, 1):
        blocks[f"i{i}"] = {"type": "item", "settings": {
            "title": title, "body": rich(body)}}
        order.append(f"i{i}")
    st = collections.OrderedDict([
        ("color_scheme", scheme), ("layout", "list"), ("numbered", numbered),
        ("eyebrow", eyebrow), ("heading", heading),
    ])
    if lede:
        st["lede"] = rich(lede)
    if link:
        st["link_label"], st["link_url"] = link
    return {"type": "content-columns", "settings": st,
            "blocks": blocks, "block_order": order}


def faq(entries, heading="The things people ask on this page."):
    blocks, order = collections.OrderedDict(), []
    for i, (q, a) in enumerate(entries, 1):
        blocks[f"q{i}"] = {"type": "question", "settings": {
            "question": q, "answer": rich(a)}}
        order.append(f"q{i}")
    return {"type": "faq-accordion", "settings": {
        "color_scheme": "paper", "anchor_id": "faq", "one_at_a_time": False,
        "emit_schema": True,
        "eyebrow": "Questions", "heading": heading,
        "help_prefix": "Something not here?",
        "help_label": "Phone or email us",
        "help_link": "/pages/contact",
        # Left empty on purpose: fix-dead-buttons.py resolves it, and it is
        # the only thing that knows whether this template may use an in-page
        # anchor or must send the reader to the product page. Hardcoding
        # "#buy" here put a dead anchor on every use-case page.
        "cta_link": "",
    }, "blocks": blocks, "block_order": order}


# ---------------------------------------------------------------- the rhythm
#
# content-columns is the right component for almost every section on these
# pages, and that is the problem: four of them in sequence is four identical
# 5/7 grids with a sticky heading left and a ruled list right, on the same white
# background. The writing is doing different work in each one and the page does
# not show it, so it reads as one slab and a reader skims all four.
#
# The fix is not less content — it is a different silhouette per section. Each
# entry below sets the layout, the background and which side the heading sits
# on. The rule the table is built to: no two adjacent sections may share more
# than one of those three.
#
# It lives here, in one table, rather than at each call site, because it is a
# single design decision about the shape of a page and should be reviewable as
# one. Sections not listed keep the plain list.
#
#   steps  a numbered route with a rail that fills as you scroll
#   cards  a grid, no shared left edge and no rules across it
#   ink    the dark band that marks the turn from problem to answer
#   mirror heading on the right, so even the skeleton differs
# (layout, colour scheme, heading mirrored, numerals shown). Numerals were
# removed site-wide once; the hiking mockups of 2026-08-07 bring them back on
# exactly two sections, as ghost figures inside the cards and boxes — so they
# are a per-section value here, never something a layout switches on.
RHYTHM = {
    # Hiking follows the client's section mockups: a full-width band of
    # numbered cards, a dark section of numbered boxes with the heading kept
    # left, the blisters as a centred statement over its cards, and the fit
    # checks as an ink panel with the size-guide button beside card rows.
    "hiking-and-walking": {
        "problem":    ("band",  "paper", False, True),
        "answers":    ("boxes", "ink",   False, True),
        "blisters":   ("stack", "paper", False, False),
        "fit":        ("panel", "wash",  False, False),
    },
    # 2026-08-08, the client: each page's dark emphasis section takes the
    # numbered-boxes treatment they screenshotted from the boots page's
    # "What answers it" — outlined boxes, ghost numerals, heading left.
    "running-and-trail": {
        "trade":      ("boxes", "ink",   False, True),    # the concession, up front
        # whennot is honest-limits and already a different shape
        "winter":     ("cards", "paper", False, False),
        "blisters":   ("split", "wash",  False, False),   # the same three causes
    },
    "cycling-and-commuting": {
        "problem":    ("steps", "paper", False, False),   # where the water comes from
        # overshoes is a comparison table and already a different shape
        "drying":     ("boxes", "ink",   False, True),    # the insight, dark
        "fit":        ("cards", "paper", False, False),
    },
    "all-day-in-boots": {
        "problem":    ("steps", "paper", False, False),
        "durability": ("boxes", "ink",   False, True),    # why the cheap pair failed
        "fit":        ("cards", "paper", False, False),
        "warranty":   ("split", "wash",  False, False),   # sits after the buy widget
    },
}

# NOTE: two sections (the in-use gallery and the blue limits band) were briefly
# restored here from history and then removed by the client in the theme editor
# — writeback 050bccc, 2026-08-07. They must NOT come back: the generator
# re-creating a section the client deleted by hand is the worst version of the
# generator-discards-edits trap. The old content remains reachable at commit
# a037122 if it is ever wanted again.


# Everything after the buy widget was four paper sections in a row — the same
# flat run the argument sections were fixed for, left in place on the last
# quarter of the page because nothing in the rhythm table reached it.
#
# These are not content-columns, so there is no layout to vary; the background
# is what there is. The page darkens as it ends, which hands off into the footer
# rather than stopping dead in front of it.
TAIL = {
    "hiking-and-walking": {
        "faq":      {"color_scheme": "wash"},    # off the buy widget above it
        "guides":   {"color_scheme": "paper", "pace": "tight"},
        "siblings": {"color_scheme": "wash", "card_fill": "solid"},
        "close":    {"color_scheme": "ink"},     # into the dark footer
    },
}


def apply(handle, current_label, new_sections, new_order_mid, faq_section,
          buy_overrides=None, after_buy=None, hero=None):
    header, d = read(handle)
    S = d["sections"]

    # v4 Document 2 (8 Aug 2026): each page's hero, and the spec bar the
    # documents set identically everywhere.
    if hero and "hero" in S:
        S["hero"]["settings"].update(hero)
    if "specs" in S:
        cells = [("Waterproof layer", "Porelle® membrane"),
                 ("Build", "Three layers"),
                 ("Sizes", "UK 3 to 14"),
                 ("Price", "From £20 a pair")]
        border = S["specs"].get("block_order") or list(S["specs"]["blocks"])
        for bk, cell in zip(border, cells):
            S["specs"]["blocks"][bk]["settings"].update(
                {"label": cell[0], "value": cell[1]})

    # Breadcrumbs nest under the category hub: a breadcrumb step has to point
    # somewhere, and "Shop by activity" was a navigation label, not a URL.
    for sec in S.values():
        if sec.get("type") == "breadcrumb":
            sec["settings"].update({
                "parent_label": "Waterproof socks", "parent_url": HUB,
                "current_label": current_label,
            })

    # The old shared mid-page sections go; each page argues its own case now.
    for old in ("problem", "answers", "inuse", "practice", "limits"):
        S.pop(old, None)
    for key, sec in new_sections.items():
        S[key] = sec
    S["faq"] = faq_section

    # The tail sections carry no layout of their own; the background is the
    # only thing that separates them.
    for key, settings in TAIL.get(handle, {}).items():
        if key in S:
            S[key]["settings"].update(settings)

    # Apply the page's rhythm, so no two adjacent sections share a silhouette.
    for key, (layout, scheme, mirror, numbered) in RHYTHM.get(handle, {}).items():
        if key not in S or S[key].get("type") != "content-columns":
            continue
        S[key]["settings"].update({
            "layout": layout, "color_scheme": scheme, "mirror": mirror,
            "numbered": numbered})


    if buy_overrides and "buy" in S:
        S["buy"]["settings"].update(buy_overrides)

    keep_tail = [k for k in ("guides", "siblings", "close") if k in S]
    order = ["breadcrumb", "hero", "specs"] + new_order_mid + ["reviews", "buy"]
    if after_buy:
        order += after_buy
    order += ["faq"] + keep_tail
    order = [k for k in order if k in S]
    orphans = [k for k in S if k not in order]
    if orphans:
        raise SystemExit(f"{handle}: orphaned sections {orphans}")
    d["order"] = order
    write(handle, header, d)
    print(f"  {handle}: {' '.join(order)}")


def main():
    # =================================================================
    # v4 Document 2 (8 Aug 2026), applied verbatim. Per-page red gates:
    # the running weight item is DELETED, not hedged — the document's own
    # instruction when no figure exists; the boots warranty section stays
    # three items until a warranty period beyond statutory rights exists.
    # ------------------------------------------------------------- HIKING
    apply(
        "hiking-and-walking", "Hiking and walking",
        collections.OrderedDict([
            ("problem", cols(
                "The problem", "Four ways a walk gets your feet wet",
                "Only one of these is the thing boots are designed to stop. "
                "That’s why good boots and wet feet aren’t a "
                "contradiction.",
                [("Over the top",
                  "Wet grass, bracken and heather put water onto the boot "
                  "from above, where the tongue and the laces are. Gaiters "
                  "help. They don’t seal."),
                 ("The boot soaks through",
                  "The outer fabric saturates, the boot stops breathing, and "
                  "everything your foot produces stays inside. It isn’t "
                  "leaking — it’s full. This is the four-hour "
                  "problem."),
                 ("Streams and bog",
                  "There’s a depth beyond which no footwear helps, and "
                  "on wet British ground you meet it more often than the "
                  "forecast suggests."),
                 ("From the inside",
                  "Eight hours of walking produces a lot of moisture. Plenty "
                  "of people with perfectly good boots finish the day damp "
                  "anyway.")])),
            ("answers", cols(
                "The answer", "What the socks do about it",
                "The waterproof layer sits inside the sock rather than "
                "inside the boot. That changes where the waterproof line is, "
                "and what happens when the boot gives up.",
                [("Your boot can be soaked and your foot dry",
                  "Once the waterproof layer is on your foot, a wet boot is "
                  "uncomfortable rather than a disaster. You stop planning "
                  "the route around the puddles."),
                 ("They work with any boot, including a leaky one",
                  "Most people find waterproof socks because their boots "
                  "have started letting water in. It’s the cheapest "
                  "useful thing to try before spending two hundred pounds."),
                 ("They aren’t a replacement for boots",
                  "Said plainly here as well as on the homepage. If your "
                  "footwear is wrong for the ground, this won’t fix it. "
                  "It solves wet, not grip or ankle support.")],
                link=("How the three layers work", "/pages/technology"))),
            ("blisters", cols(
                "Blisters", "What dry feet do and don’t prevent",
                "Waterproof socks help with blisters. They don’t "
                "prevent them, and anyone telling you otherwise is selling "
                "you something.",
                [("Wet skin blisters more easily",
                  "Soft, wet skin gives up under friction much faster than "
                  "dry skin. Keeping your feet dry removes one of the three "
                  "things a blister needs, and that’s a genuine help."),
                 ("Friction and fit still matter",
                  "The other two are pressure and movement. A boot that rubs "
                  "will still rub. A sock that’s too small will still "
                  "bunch up. No waterproof layer changes either."),
                 ("Grit is the one nobody mentions",
                  "On wet ground, fine grit washes in over the top and sits "
                  "under your foot. It’s abrasive against your skin and "
                  "against the sock. Rinse both at the end of a wet day.")])),
            ("fit", cols(
                "Fit", "Check the boot before you order",
                "This is the question most sellers skip and where most "
                "returns come from. Waterproof socks are thicker than the "
                "sock you’re used to.",
                [("About the same as a mid-weight sock",
                  "If your boots are already snug with a thick walking sock, "
                  "they’ll be tight with these. If you wear a thin liner "
                  "under a thick sock, these replace both."),
                 ("Between two sizes, go up",
                  "Going down grips your toes, which is uncomfortable over "
                  "eight hours and hard on the waterproof layer. Foot "
                  "length, not shoe size, sets the size."),
                 ("Your laces will need adjusting",
                  "A thicker sock changes where a boot loads over the "
                  "instep. Give the laces one honest adjustment on the first "
                  "walk rather than deciding the fit is wrong.")],
                link=("The sizes in centimetres", "/pages/size-guide"))),
        ]),
        ["problem", "answers", "blisters", "fit"],
        faq([
            ("Are waterproof socks good for hiking?",
             "Yes, especially on long days in the wet. They keep your feet "
             "dry once a boot has soaked through, which on British hills is "
             "usually a question of when rather than whether. They "
             "don’t replace a boot’s grip or ankle support."),
            ("Do waterproof socks stop blisters?",
             "They remove one of the three causes. Wet skin gives up under "
             "friction much faster than dry skin, so keeping your feet dry "
             "helps a lot. Fit and rubbing still cause blisters, and no "
             "sock fixes a boot that rubs."),
            ("Can you wear waterproof socks with walking boots?",
             "Yes, with one check. They’re about the bulk of a "
             "mid-weight walking sock, so if your boots are already tight "
             "with thick socks they’ll be tighter with these. They "
             "replace a liner-and-sock combination rather than going over "
             "it."),
            ("Are waterproof socks better than waterproof boots?",
             "They solve different halves of the same problem. A boot keeps "
             "water out until its outer soaks through. A waterproof sock "
             "carries on after that. Most people who walk regularly in the "
             "wet end up using both."),
            ("What socks should I wear for walking in the rain?",
             "Something still doing its job in hour six, not just hour one. "
             "That means either a boot that won’t soak through in the "
             "conditions you’re actually in, or a waterproof layer on "
             "your foot. On a full wet British day, usually the second."),
            ("Will my feet sweat on a long walk?",
             "Walking pace is well within what the waterproof layer can "
             "handle, so most people stay dry all day. On a steep climb in "
             "mild weather you’ll out-produce it for a while and then "
             "catch up on the way down."),
        ], heading="Common questions"),
        buy_overrides={
            "heading": "Choose your colour and size",
            "lede": rich("One price, whichever page you came in on."),
        },
        hero={
            "eyebrow": "Hiking & walking",
            "heading": "Waterproof socks for hiking and walking",
            "lede": rich(
                "Every waterproof boot soaks through eventually. This is "
                "the layer still working when yours does, four hours into a "
                "wet day with eleven miles to go."),
            "cta_label": "Buy a pair",
            "cta_url": "#buy",
            "link_label": "How they work",
            "link_url": "/pages/technology",
        })

    # ------------------------------------------------------------- BOOTS
    apply(
        "all-day-in-boots", "All day in boots",
        collections.OrderedDict([
            ("problem", cols(
                "The problem", "Ten hours in a boot",
                "A safety boot is built to keep water and everything else "
                "out. Nothing about it is built to let anything back out "
                "again.",
                [("Wet from the inside by lunchtime",
                  "Your foot produces a serious amount of moisture across a "
                  "ten-hour shift. In a sealed boot most of it stays there, "
                  "which is why your feet are wet on dry days too."),
                 ("Damp skin, all winter",
                  "Skin that stays damp for months softens, splits and stops "
                  "recovering overnight. That’s the real cost of this, "
                  "and it isn’t comfort."),
                 ("Rain and standing water on top of that",
                  "Sites flood, ditches fill and wellies get overtopped. The "
                  "boot handles some of it. The rest arrives anyway.")])),
            ("durability", cols(
                "Durability", "Why the cheap pair failed",
                "Most cheap waterproof socks don’t fail because the "
                "waterproof layer is bad. They fail for three reasons, and "
                "two of them are avoidable.",
                [("There was no waterproof layer",
                  "A lot of what’s sold as waterproof is a treated knit "
                  "that shrugs off light rain and then wets through. If a "
                  "listing doesn’t name a waterproof layer, that’s "
                  "usually why. Ours is Porelle®, named on every page."),
                 ("The outside wore through first",
                  "Inside a work boot the rubbing is constant. The outer "
                  "knit takes that, and a thin one wears through to the "
                  "waterproof layer in weeks. Three layers exist so the "
                  "middle one is never the wear surface."),
                 ("It went in the tumble dryer",
                  "The most common way a waterproof sock dies and the least "
                  "discussed. Heat and fabric softener finish one off far "
                  "faster than a building site does. Cool wash, no softener, "
                  "air dry.")],
                link=("What damages the waterproof layer",
                      "/pages/care-and-washing"))),
            ("fit", cols(
                "Fit", "Check the boot before you order",
                "Safety boots have a fixed toe cap with no give in it. "
                "That’s the one thing worth checking before you buy.",
                [("About the same as a thick work sock",
                  "If you already wear thick socks in your boots, these "
                  "replace them rather than going over them. If you wear "
                  "thin socks in a snug boot, allow for the difference."),
                 ("Between two sizes, go up",
                  "A sock that grips your toes inside a steel toe cap is "
                  "uncomfortable by hour three and hard on the waterproof "
                  "layer."),
                 ("Wellies",
                  "No fit problem at all. Wellies have room to spare, which "
                  "is why a waterproof sock inside a welly is one of the "
                  "more sensible things you can do with one.")],
                link=("The sizes in centimetres", "/pages/size-guide"))),
            ("warranty", cols(
                "If something goes wrong", "Where you stand",
                None,
                [("A fault isn’t the same as wear",
                  "A seam letting water through in the first few weeks of "
                  "normal use is a fault. Thinning at the heel after months "
                  "on site is wear. We don’t charge for returning "
                  "faulty goods."),
                 ("Thirty days to reject outright",
                  "Under the Consumer Rights Act 2015, goods have to be of "
                  "satisfactory quality, fit for purpose and as described. "
                  "Within thirty days of delivery you can reject them for a "
                  "full refund."),
                 ("Six months where we have to prove otherwise",
                  "Within six months of delivery a fault is assumed to have "
                  "been there from the start unless we can show it "
                  "wasn’t.")],
                link=("The full warranty position", "/pages/warranty"))),
        ]),
        ["problem", "durability", "fit"],
        faq([
            ("Are waterproof socks good for work boots?",
             "Yes, and mostly for a reason people don’t expect. A "
             "safety boot already keeps rain out. What it can’t do is "
             "let moisture from your foot escape across a ten-hour shift, "
             "and that’s the half these deal with."),
            ("What socks do you wear with wellies?",
             "A waterproof sock is a sensible choice, because wellies have "
             "plenty of room and no breathability at all. Feet get wet "
             "inside wellies from the inside far more often than from the "
             "outside."),
            ("Will they fit inside safety boots?",
             "They’re about the bulk of a thick work sock, so they "
             "replace one rather than going over it. Safety boots have a "
             "fixed toe cap with no give, so if you’re between two "
             "sizes take the bigger."),
            ("How long do they last on site?",
             "Longer than a cheap pair and shorter than a boot. Rubbing "
             "inside a boot and the wrong wash cycle finish a waterproof "
             "sock off long before age does — cool wash, no softener, "
             "air dry, and never a tumble dryer or a radiator."),
            ("What are the best socks for standing all day?",
             "Something that deals with moisture rather than just adding "
             "padding. Cushioning helps your joints. It does nothing about "
             "a sealed boot keeping a day’s worth of sweat against "
             "your skin."),
        ], heading="Common questions"),
        buy_overrides={
            "heading": "Choose your colour and size",
            "lede": rich(
                "Five pairs is a working week, which is why it’s the "
                "option most people on site end up taking."),
            # Mark needs a fresh pair every working day; the ladder is
            # framed as a week's worth, per the document's developer note.
            "default_quantity": 5,
        },
        after_buy=["warranty"],
        hero={
            "eyebrow": "All day in boots",
            "heading": "Waterproof socks for work boots and wellies",
            "lede": rich(
                "A good boot keeps the rain out. What it also does, across "
                "a ten-hour shift, is keep everything your foot produces on "
                "the inside."),
            "cta_label": "Buy a pair",
            "cta_url": "#buy",
            "link_label": "How they work",
            "link_url": "/pages/technology",
        })

    # ----------------------------------------------------------- CYCLING
    overshoe_rows = [
        ("Where the water gets in",
         "The waterproof line is on your foot, so ankle spray lands outside "
         "it rather than inside.",
         "Sealed over the shoe, open at the ankle — which is where the "
         "spray arrives."),
        ("Wind",
         "They keep your foot warmer but do nothing for the shoe. In "
         "properly cold wind that’s a real gap.",
         "Better. They block windchill across the whole shoe, which matters "
         "below about five degrees."),
        ("The shoe itself",
         "The shoe gets soaked. Your foot doesn’t.",
         "The shoe stays dry, which is the strongest argument for them on a "
         "commute with nowhere to dry anything."),
        ("Putting them on",
         "You put a sock on.",
         "Fiddly, especially in the dark with cold hands, and they tear at "
         "the heel where the cleat sits."),
        ("Cost and how long they last",
         "£20, and they fail from heat and washing rather than from cleat "
         "abrasion.",
         "Around £30–£40 and often a one-season item on a daily "
         "commute."),
        ("Both together",
         "Worth it when: properly cold, properly wet, properly long. The "
         "most effective and most expensive option.",
         "Not worth it when: anything milder. You’ll overheat."),
    ]
    ov_blocks, ov_order = collections.OrderedDict(), []
    for n, (label, ours, theirs) in enumerate(overshoe_rows, 1):
        k = f"r{n}"
        ov_blocks[k] = {"type": "criterion", "settings": {
            "label": label, "ours_value": ours, "theirs_value": theirs}}
        ov_order.append(k)
    overshoes = {
        "type": "comparison-table",
        "settings": collections.OrderedDict([
            ("color_scheme", "wash"),
            ("anchor_id", "vs-overshoes"),
            ("eyebrow", "Vs overshoes"),
            ("heading", "Compared with overshoes"),
            ("lede", rich(
                "Most people reading this already own a pair. This "
                "isn’t an argument that they’re useless — "
                "it’s what each one is actually good at.")),
            ("table_caption",
             "Waterproof socks and overshoes, and what each one is "
             "actually good at."),
            ("col_criterion", "What matters"),
            ("col_ours", "Waterproof socks"),
            ("col_theirs", "Overshoes"),
        ]),
        "blocks": ov_blocks, "block_order": ov_order}

    apply(
        "cycling-and-commuting", "Cycling and commuting",
        collections.OrderedDict([
            ("problem", cols(
                "The problem", "Where the water actually comes from",
                "Riding in the rain isn’t really a rain problem. "
                "It’s a spray problem, and spray behaves differently.",
                [("Off the front wheel, onto your ankle",
                  "The front wheel throws a constant fan of water backwards "
                  "onto the shoe and the ankle. That’s where an "
                  "overshoe stops, and where it’s open."),
                 ("Standing water, at speed",
                  "A puddle taken at twenty miles an hour goes into your "
                  "shoe through the vents in a way that rain simply "
                  "doesn’t."),
                 ("The road is dirtier than the rain",
                  "Road spray carries grit and oil. It stains, it wears "
                  "things out, and it’s why cycling kit gives up faster "
                  "than walking kit."),
                 ("And nothing dries at the office",
                  "A soaked cycling shoe doesn’t dry under a desk in "
                  "eight hours. The ride home starts wet whatever the "
                  "forecast says.")])),
            ("overshoes", overshoes),
            ("drying", cols(
                "The other half",
                "The ride home starts where the ride in finished",
                "Almost everything in this category is designed around the "
                "journey in. A commute has two halves, and only one of them "
                "ends near a radiator.",
                [("A shoe won’t dry in eight hours",
                  "Especially not under a desk in a building with the "
                  "heating on a timer. Overshoes protect the shoe on the "
                  "way in. They don’t dry it by five o’clock."),
                 ("A sock can be swapped",
                  "A second pair in your bag weighs almost nothing and "
                  "means the ride home starts dry even if the shoe "
                  "doesn’t. That’s the practical reason commuters "
                  "buy two pairs."),
                 ("Wash cool, air dry overnight",
                  "They’ll be ready for the morning. They won’t "
                  "be ready in two hours, and they must never go on a "
                  "radiator — direct heat is what finishes a waterproof "
                  "layer off.")],
                link=("How to wash them properly", "/pages/care-and-washing"))),
            ("fit", cols(
                "Fit", "Check the shoe before you order",
                "Cycling shoes have far less room than a walking boot, so "
                "this matters more here than anywhere else on the site.",
                [("About the same as a cushioned training sock",
                  "If your shoes are already snug in a thin summer sock "
                  "they’ll be tight in these. Winter and commuting "
                  "shoes usually have room. Race-fit road shoes often "
                  "don’t."),
                 ("Between two sizes, go up",
                  "A tight sock in a tight shoe creates a pressure point "
                  "across your toes that you’ll notice at about mile "
                  "four."),
                 ("If you size up for winter shoes",
                  "These fit that space exactly. If you don’t, try "
                  "them in the shoe before committing to a long ride.")],
                link=("The sizes in centimetres", "/pages/size-guide"))),
        ]),
        ["problem", "overshoes", "drying", "fit"],
        faq([
            ("Are waterproof socks good for cycling?",
             "Yes, especially commuting in the wet. Road spray arrives at "
             "the ankle, which is where an overshoe is open, and a "
             "waterproof sock puts the barrier below that line. "
             "They’re less useful in cold wind, where an overshoe "
             "also blocks windchill on the shoe."),
            ("Are waterproof socks better than overshoes?",
             "For keeping your foot dry, generally yes, because they seal "
             "where the spray actually arrives. For keeping the shoe dry "
             "and blocking wind, overshoes win. In cold, wet, long "
             "conditions a lot of people use both."),
            ("Will they fit inside cycling shoes?",
             "They’re about the bulk of a cushioned training sock. "
             "Winter and commuting shoes usually have the room. Snug "
             "race-fit road shoes often don’t. If you already size "
             "up for winter shoes, they fit that space."),
            ("What socks should I wear cycling to work in winter?",
             "Something still working on the ride home, when the shoe "
             "never dried. A waterproof sock plus a spare pair in your bag "
             "deals with both halves of the commute, which overshoes on "
             "their own don’t."),
            ("Do waterproof socks keep your feet warm on a bike?",
             "Much warmer than a wet sock, because they stop your foot "
             "cooling as water evaporates and they block the wind reaching "
             "it. They aren’t insulated though — below about five "
             "degrees you may still want an overshoe over the top."),
            ("How do I wash them after a wet commute?",
             "Rinse the road grit off first, then a cool wash inside out "
             "with no fabric softener, and air dry away from any heat. "
             "Never on a radiator, however tempting after a wet ride."),
        ], heading="Common questions"),
        buy_overrides={
            "heading": "Choose your colour and size",
            "lede": rich(
                "Two pairs is what most commuters take — one on, one "
                "drying."),
        },
        hero={
            "eyebrow": "Cycling & commuting",
            "heading": "Waterproof socks for cycling and commuting",
            "lede": rich(
                "On a wet road the water comes up, not down. Overshoes are "
                "sealed everywhere except the ankle, which is exactly where "
                "it arrives."),
            "cta_label": "Buy a pair",
            "cta_url": "#buy",
            "link_label": "How they work",
            "link_url": "/pages/technology",
        })

    # ----------------------------------------------------------- RUNNING
    # The weight item is deleted, not hedged: the document's own red block
    # forbids publishing its [x]/[y] placeholders and says to cut the item
    # entirely until the real per-pair weight exists.
    whennot = {
        "type": "honest-limits",
        "settings": collections.OrderedDict([
            ("color_scheme", "ink"),
            ("anchor_id", "when-not"),
            ("eyebrow", "When not to"),
            ("heading", "When these are the wrong sock"),
            ("lede", rich(
                "Every brand tells you when to wear their product. On a "
                "running page that’s close to useless, because the "
                "conditions these suit are narrower than the conditions "
                "people run in.")),
            ("footnote",
             "Cold and wet is where these earn their place. That’s "
             "most of a British winter. It isn’t July."),
            ("cta_link", "#buy"),
        ]),
        "blocks": collections.OrderedDict([
            ("m1", {"type": "limit", "settings": {
                "heading": "Warm and wet",
                "body": rich(
                    "Summer rain is the worst case. The air is already "
                    "saturated, you’re producing heat, and the sweat "
                    "has nowhere to go. Wear a thin sock and accept wet "
                    "feet.")}}),
            ("m2", {"type": "limit", "settings": {
                "heading": "Hard efforts in mild weather",
                "body": rich(
                    "Intervals, tempo, anything above steady in double "
                    "figures. You’ll out-produce the waterproof layer "
                    "within twenty minutes and finish damp from the "
                    "inside.")}}),
            ("m3", {"type": "limit", "settings": {
                "heading": "A race-fit shoe with no room",
                "body": rich(
                    "If your racing shoe is already snug in a thin sock, "
                    "don’t put a three-layer sock in it. This is a "
                    "training and long-run product first.")}}),
        ]),
        "block_order": ["m1", "m2", "m3"]}

    apply(
        "running-and-trail", "Running and trail",
        collections.OrderedDict([
            ("trade", cols(
                "The trade", "Weight and bulk, honestly",
                "A waterproof sock has three layers where a racing sock has "
                "one. There’s no version of this where the weight is "
                "the same, so here’s what the difference actually is.",
                [("Bulk is the more real objection",
                  "They’re about the volume of a cushioned training "
                  "sock. In a race-fit shoe with no room, that matters. In "
                  "a normal training shoe it doesn’t."),
                 ("What you’re trading it for",
                  "Dry feet at mile ten in December instead of soaked feet "
                  "at mile two. Whether that’s worth three layers is a "
                  "question only your local weather can answer.")])),
            ("whennot", whennot),
            ("winter", cols(
                "Winter", "The runs these are for",
                "Not performance. Consistency — the training block "
                "surviving the months when it usually doesn’t.",
                [("Wet feet get cold fast",
                  "A soaked foot at five degrees loses heat quickly, and "
                  "cold toes are why a lot of winter long runs get cut "
                  "short. Dry feet stay warm at temperatures where wet ones "
                  "don’t."),
                 ("Trail, crossings and standing water",
                  "On a wet trail you stop picking your line around the "
                  "puddles, which is faster and a good deal more "
                  "enjoyable."),
                 ("The pair waiting for tomorrow",
                  "They air dry rather than tumble dry, which takes longer. "
                  "If you run four mornings a week in winter you need more "
                  "than one pair — that’s the honest reason the "
                  "two-pair price exists.")])),
            ("blisters", cols(
                "Blisters", "Blisters at running pace",
                "Running compresses the same problem walkers have into a "
                "much shorter time, which is why runners feel it more "
                "sharply.",
                [("Wet skin is weaker skin",
                  "Soft, wet skin gives up under friction far faster. "
                  "Keeping your foot dry removes one of the three things a "
                  "blister needs, and at running cadence that’s the "
                  "one that changes quickest."),
                 ("Fit does the rest",
                  "A sock that bunches at the toe will blister you at any "
                  "moisture level. Take the bigger size if you’re "
                  "between two, and check for rucking before you set off."),
                 ("We don’t guarantee this",
                  "Some brands offer a blister-free guarantee. We "
                  "don’t, because blistering depends on your shoe, "
                  "your gait and your distance far more than on your "
                  "sock.")])),
        ]),
        ["trade", "whennot", "winter", "blisters"],
        faq([
            ("Are waterproof socks good for running?",
             "In cold, wet conditions, yes — they keep your feet dry "
             "and therefore warm on winter miles and wet trails. In warm "
             "rain, or on hard efforts in mild weather, they’re the "
             "wrong choice, and this page says which runs those are."),
            ("Are waterproof socks too hot for running?",
             "In summer, generally yes. The waterproof layer moves sweat "
             "out as vapour but it can’t keep up with a running foot "
             "in warm, humid air. In British winter conditions the balance "
             "goes the other way and they’re comfortable for hours."),
            ("Do waterproof socks feel bulky when running?",
             "They’re about the volume of a cushioned training sock. "
             "In a normal training shoe that’s unremarkable. In a "
             "snug race-fit shoe it’s noticeable, and we "
             "wouldn’t recommend them for that."),
            ("What socks should I wear for trail running in the rain?",
             "If it’s cold, a waterproof sock — wet feet lose "
             "heat quickly and that’s what ends winter runs. If "
             "it’s mild, a thin quick-draining sock and dry socks in "
             "the car. The temperature decides, not the rain."),
            ("Will waterproof socks stop blisters when running?",
             "They remove one of the three causes, and at running pace wet "
             "skin is the one that changes fastest. Fit and shoe friction "
             "still matter, and we don’t offer a blister-free "
             "guarantee because neither of those is ours to control."),
            ("How many pairs do runners need?",
             "Two or three if you run through winter. They air dry rather "
             "than tumble dry, so a single pair won’t be ready for "
             "tomorrow morning after a wet run today."),
        ], heading="Common questions"),
        buy_overrides={
            "heading": "Choose your colour and size",
            "lede": rich(
                "Two pairs is the usual choice for anyone running through "
                "winter — one on, one drying."),
        },
        hero={
            "eyebrow": "Running & trail",
            "heading": "Waterproof socks for running and trail",
            "lede": rich(
                "Runners ask about weight and bulk before anything else, "
                "and they’re right to. Here’s the honest answer, "
                "and the runs these are actually for."),
            "cta_label": "Buy a pair",
            "cta_url": "#buy",
            "link_label": "How they work",
            "link_url": "/pages/technology",
        })


if __name__ == "__main__":
    main()
