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


def read(handle):
    raw = (TPL / f"page.{handle}.json").read_text()
    m = re.match(r"^\s*/\*[\s\S]*?\*/\s*", raw)
    header = raw[: m.end()] if m else ""
    return header, json.loads(raw[m.end():] if m else raw,
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
        ("eyebrow", eyebrow), ("heading", heading), ("lede", rich(lede)),
    ])
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
        # The label is a schema default; the link is not, so a CTA built without
        # this line renders as a button that looks fine and does nothing.
        "cta_link": "#buy",
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
RHYTHM = {
    "hiking-and-walking": {
        "problem":    ("steps", "paper", False),   # four ways, enumerated
        "answers":    ("list",  "ink",   True),    # the turn — dark, flipped
        "blisters":   ("cards", "paper", False),   # does / does not, side by side
        "fit":        ("list",  "wash",  True),    # checks before ordering
    },
    "running-and-trail": {
        "trade":      ("list",  "ink",   True),    # the concession, up front
        # whennot is honest-limits and already a different shape
        "winter":     ("cards", "paper", False),
        "blisters":   ("steps", "wash",  False),   # the same three causes
    },
    "cycling-and-commuting": {
        "problem":    ("steps", "paper", False),   # where the water comes from
        # overshoes is a comparison table and already a different shape
        "drying":     ("list",  "ink",   True),    # the insight, dark
        "fit":        ("cards", "paper", False),
    },
    "all-day-in-boots": {
        "problem":    ("steps", "paper", False),
        "durability": ("list",  "ink",   True),    # why the cheap pair failed
        "fit":        ("cards", "paper", False),
        "warranty":   ("list",  "wash",  True),    # sits after the buy widget
    },
}


def apply(handle, current_label, new_sections, new_order_mid, faq_section,
          buy_overrides=None, after_buy=None):
    header, d = read(handle)
    S = d["sections"]

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

    # Apply the page's rhythm, so no two adjacent sections share a silhouette.
    for key, (layout, scheme, mirror) in RHYTHM.get(handle, {}).items():
        if key not in S or S[key].get("type") != "content-columns":
            continue
        S[key]["settings"].update({
            "layout": layout, "color_scheme": scheme, "mirror": mirror})

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
    # ------------------------------------------------------------- HIKING
    apply(
        "hiking-and-walking", "Hiking and walking",
        collections.OrderedDict([
            ("problem", cols(
                "The problem", "Four ways a walk gets your feet wet.",
                "Only one of these is the one boots are designed to stop, which is "
                "why good boots and wet feet are not a contradiction.",
                [("Over the top",
                  "Wet grass, bracken and heather put water onto the boot from above, "
                  "where the gusset and the laces are. Gaiters help. They do not seal."),
                 ("The boot wets out",
                  "The outer fabric saturates, the membrane can no longer pass vapour, "
                  "and the boot stops breathing. It is not leaking — it is full. This "
                  "is the four-hour problem."),
                 ("Stream crossings and bog",
                  "There is a depth beyond which no footwear helps, and on wet British "
                  "ground you meet it more often than the forecast suggests."),
                 ("From the inside",
                  "Eight hours of walking produces a lot of vapour. Some of it "
                  "condenses. By the afternoon, plenty of dry-footed walkers are damp "
                  "anyway.")])),
            ("answers", cols(
                "The answer", "A layer that does not wet out.",
                "The membrane sits inside the sock rather than inside the boot, which "
                "changes where the waterproof line is drawn — and what happens when "
                "the boot fails.",
                [("The boot can be soaked and the foot dry",
                  "Once the waterproof layer is on the foot, a saturated boot is "
                  "uncomfortable rather than decisive. You stop planning the route "
                  "around the puddles."),
                 ("It works with any boot, including the wrong one",
                  "Most people discover waterproof socks because their boots have "
                  "started leaking. It is the cheapest useful thing to try before "
                  "spending two hundred pounds."),
                 ("It is not a boot replacement",
                  "Said plainly here and on the homepage: if your footwear is wrong "
                  "for the ground, this will not fix it. It solves wetness, not "
                  "support, grip or ankle protection.")],
                link=("How the three layers work", "/pages/technology"))),
            ("blisters", cols(
                "Blisters", "What a dry foot does and does not prevent.",
                "Waterproof socks help with blisters. They do not prevent them, and "
                "any brand telling you otherwise is selling you something.",
                [("Wet skin blisters more easily",
                  "Saturated skin softens and its resistance to friction drops "
                  "sharply. Keeping the foot dry removes one of the three things a "
                  "blister needs. That is a real and significant help."),
                 ("Friction and fit still matter",
                  "The other two things are pressure and movement. A boot that rubs "
                  "will still rub. A sock that is too small will still bunch. No "
                  "membrane changes that."),
                 ("Grit is the one nobody mentions",
                  "On wet ground, fine grit washes in over the cuff and sits under "
                  "the foot. That is abrasive against skin and against the sock. "
                  "Rinse both at the end of a wet day.")])),
            ("fit", cols(
                "Fit", "Before you order, check the boot.",
                "This is the question most sellers skip and most returns come from. "
                "Waterproof socks are thicker than the sock you are used to.",
                [("Roughly a mid-weight sock",
                  "If your boots are already snug with a thick walking sock, they "
                  "will be tight with these. If you wear a liner and a thick sock "
                  "together, these replace both."),
                 ("Take the larger band if you are between two",
                  "A size down grips the toes, which is uncomfortable over eight "
                  "hours and shortens the life of the membrane. Foot length, not "
                  "shoe size, sets the band."),
                 ("Lace pressure over the instep",
                  "A thicker sock changes where a boot loads. Give the laces one "
                  "honest adjustment on the first walk rather than assuming the fit "
                  "is wrong.")],
                link=("The size bands in centimetres", "/pages/size-guide"))),
        ]),
        ["problem", "answers", "blisters", "fit"],
        faq([
            ("Are waterproof socks good for hiking?",
             "Yes, particularly on long days in wet conditions. They keep the foot "
             "dry once a boot has wet out, which on British hills is usually a "
             "question of when rather than whether. They do not replace a boot's "
             "support, grip or ankle protection."),
            ("Do waterproof socks stop blisters?",
             "They remove one of the three causes. Wet skin softens and blisters "
             "more readily, so keeping the foot dry helps considerably. Friction "
             "and poor fit still cause blisters, and no sock fixes a boot that rubs."),
            ("Can you wear waterproof socks with walking boots?",
             "Yes, with one check. They sit at roughly the bulk of a mid-weight "
             "walking sock, so if your boots are already tight with thick socks "
             "they will be tighter with these. They replace a liner-and-sock "
             "combination rather than adding to it."),
            ("Are waterproof socks better than waterproof boots?",
             "They solve different halves of the same problem. A boot keeps water "
             "out until its outer saturates; a waterproof sock keeps working after "
             "that. Most people who walk regularly in the wet end up using both."),
            ("What socks should I wear for hiking in the rain?",
             "Something that is still doing its job in hour six, not just hour one. "
             "That means either a boot that will not wet out in the conditions you "
             "are actually in, or a waterproof layer on the foot itself. On a full "
             "wet British day, usually the second."),
            ("Will my feet get sweaty on a long walk?",
             "Walking pace is well within what the membrane can move, so most "
             "people are dry all day. On a steep sustained climb in mild weather "
             "you will out-produce it for a while, then catch up on the descent."),
        ]))

    # ------------------------------------------------------------ RUNNING
    whennot = {
        "type": "honest-limits",
        "settings": {
            "color_scheme": "ink", "anchor_id": "when-not",
            "eyebrow": "When not to",
            "heading": "Three runs where you should not wear these.",
            "cta_link": "#buy",
            "link_url": "/pages/technology",
            "lede": rich(
                "Every brand tells you when to wear their product. On a running "
                "page that is close to useless, because the conditions that suit a "
                "waterproof sock are narrower than the conditions people run in."),
        },
        "blocks": collections.OrderedDict([
            ("w1", {"type": "limit", "settings": {
                "heading": "Warm and wet",
                "body": rich(
                    "Summer rain is the worst case. The air is already saturated, "
                    "you are producing heat, and the membrane has nowhere to send "
                    "the vapour. Wear a thin sock and accept wet feet."),
                "width": "1", "tone": "wash"}}),
            ("w2", {"type": "limit", "settings": {
                "heading": "Hard efforts in mild weather",
                "body": rich(
                    "Intervals, tempo, anything above steady in double figures. You "
                    "will out-produce the membrane inside twenty minutes and finish "
                    "damp from the inside."),
                "width": "1", "tone": "wash"}}),
            ("w3", {"type": "limit", "settings": {
                "heading": "A race-fit shoe with no volume",
                "body": rich(
                    "If your racing shoe is already snug in a thin sock, do not put "
                    "a three-layer sock in it. This is a training and long-run "
                    "product first."),
                "width": "2", "tone": "blue"}}),
            ("w4", {"type": "limit", "settings": {
                "heading": "",
                "body": rich(
                    "Cold and wet is where these earn their place. That is most of "
                    "a British winter, but it is not July."),
                "width": "4", "tone": "paper", "side_by_side": True}}),
        ]),
        "block_order": ["w1", "w2", "w3", "w4"],
    }
    apply(
        "running-and-trail", "Running and trail",
        collections.OrderedDict([
            ("trade", cols(
                "The trade", "Heavier than a racing sock. Lighter than a wet one.",
                "A waterproof sock has three layers where a racing sock has one. "
                "There is no version of this where the weight is the same. The "
                "measured weight per pair is being confirmed and will be published "
                "here as a number, not an adjective.",
                [("Bulk is the more real objection",
                  "They sit at about the volume of a cushioned training sock. In a "
                  "race-fit shoe with no room, that matters. In a normal training "
                  "shoe, it does not."),
                 ("What you are trading it for",
                  "A foot that is dry at mile ten in December rather than soaked at "
                  "mile two. Whether that is worth three layers is a question only "
                  "your local weather can answer.")])),
            ("whennot", whennot),
            ("winter", cols(
                "Winter", "The runs these are actually for.",
                "Not performance. Consistency — the training block staying intact "
                "through the months when it usually does not.",
                [("Wet feet get cold fast",
                  "A soaked foot in five degrees loses heat quickly, and cold toes "
                  "are the reason a lot of winter long runs get cut short. Dry feet "
                  "stay warm at temperatures where wet ones do not."),
                 ("Trail, water crossings and standing water",
                  "On a wet trail you stop choosing your line around the puddles, "
                  "which is faster and considerably more enjoyable."),
                 ("The pair waiting for tomorrow",
                  "They air dry rather than tumble dry, which takes longer. If you "
                  "run four mornings a week in winter, you need more than one pair "
                  "— that is the honest reason the two- and three-pair prices "
                  "exist.")])),
            ("blisters", cols(
                "Blisters", "Faster feet, the same three causes.",
                "Running compresses the same blister problem walkers have into a "
                "much shorter time, which is why runners feel it more sharply.",
                [("Wet skin is weaker skin",
                  "Saturated skin resists friction far less well. Keeping the foot "
                  "dry removes one of the three things a blister needs, and at "
                  "running cadence that is the one that changes fastest."),
                 ("Fit does the rest",
                  "A sock that bunches at the toe will blister you at any moisture "
                  "level. Take the larger band if you are between two, and check "
                  "for rucking before you set off."),
                 ("We do not guarantee this",
                  "Some brands offer a blister-free guarantee. We do not, because "
                  "blistering depends on your shoe, your gait and your distance far "
                  "more than on your sock.")])),
        ]),
        ["trade", "whennot", "winter", "blisters"],
        faq([
            ("Are waterproof socks good for running?",
             "In cold, wet conditions, yes — they keep the foot dry and therefore "
             "warm on winter miles and on wet trails. In warm rain or on hard "
             "efforts in mild weather they are the wrong choice, and this page "
             "says which runs those are."),
            ("Are waterproof socks too hot for running?",
             "In summer, generally yes. The membrane moves vapour but it cannot "
             "keep up with a running foot in warm, humid air. In British winter "
             "conditions the balance goes the other way and they are comfortable "
             "for hours."),
            ("Do waterproof socks feel bulky when running?",
             "They sit at about the volume of a cushioned training sock. In a "
             "normal training shoe that is unremarkable. In a snug race-fit shoe "
             "it is noticeable, and we would not recommend them for that."),
            ("What socks should I wear for trail running in the rain?",
             "If it is cold, a waterproof sock — wet feet lose heat quickly and "
             "that is what ends winter runs. If it is mild, a thin quick-draining "
             "sock and dry socks in the car. The temperature decides, not the "
             "rain."),
            ("Will waterproof socks stop blisters when running?",
             "They remove one of the three causes, and at running cadence wet skin "
             "is the one that changes fastest. Fit and shoe friction still matter, "
             "and we do not offer a blister-free guarantee because those are not "
             "ours to control."),
            ("How many pairs do runners usually need?",
             "Two or three if you run through winter. They air dry rather than "
             "tumble dry, so a single pair will not be ready for tomorrow morning "
             "after a wet run today."),
        ]),
        buy_overrides={"default_quantity": 2})

    # ------------------------------------------------------------ CYCLING
    overshoes = {
        "type": "comparison-table",
        "settings": {
            "color_scheme": "paper", "anchor_id": "overshoes",
            "eyebrow": "The comparison",
            "heading": "Against overshoes, including where they win.",
            "link_url": "/pages/technology",
            "lede": rich(
                "Most people reading this already own overshoes. This is not an "
                "argument that they are useless — it is a description of what each "
                "one is actually good at."),
            "table_caption": "Waterproof socks compared with overshoes, including "
                             "the rows where overshoes win.",
            "col_criterion": "What matters",
            "col_ours": "Waterproof socks",
            "col_theirs": "Overshoes",
        },
        "blocks": collections.OrderedDict([
            ("o1", {"type": "criterion", "settings": {
                "label": "Where the water gets in",
                "ours_value": "The waterproof line is on the foot, so ankle spray "
                              "lands on the outside of the barrier rather than "
                              "inside it.",
                "theirs_value": "Sealed over the shoe, open at the ankle — which is "
                                "exactly where the spray arrives."}}),
            ("o2", {"type": "criterion", "settings": {
                "label": "Wind",
                "ours_value": "They insulate the foot but do nothing for the shoe. "
                              "In genuinely cold wind, that is a real gap.",
                "theirs_value": "Better. A neoprene or softshell overshoe blocks "
                                "windchill across the whole shoe, which matters "
                                "below about five degrees."}}),
            ("o3", {"type": "criterion", "settings": {
                "label": "The shoe itself",
                "ours_value": "The shoe gets soaked. The foot does not. Whether "
                              "that matters depends on whether you can leave the "
                              "shoe somewhere warm.",
                "theirs_value": "The shoe stays dry, which is the strongest "
                                "argument for them on a commute with no drying "
                                "option."}}),
            ("o4", {"type": "criterion", "settings": {
                "label": "Getting them on",
                "ours_value": "You put a sock on.",
                "theirs_value": "Fiddly, especially in the dark with cold hands, "
                                "and they tear at the heel where they meet the "
                                "cleat."}}),
            ("o5", {"type": "criterion", "settings": {
                "label": "Durability and cost",
                "ours_value": "£20, and they fail from heat and washing rather "
                              "than from cleat abrasion.",
                "theirs_value": "Around £30–£40 and commonly a one-season item on "
                                "a daily commute."}}),
            ("o6", {"type": "criterion", "settings": {
                "label": "Both together",
                "ours_value": "Worth it when it is genuinely cold, genuinely wet "
                              "and genuinely long.",
                "theirs_value": "Anything milder and you will overheat."}}),
        ]),
        "block_order": ["o1", "o2", "o3", "o4", "o5", "o6"],
    }
    apply(
        "cycling-and-commuting", "Cycling and commuting",
        collections.OrderedDict([
            ("problem", cols(
                "The problem", "Upwards, mostly.",
                "Riding in the rain is not really a rain problem. It is a spray "
                "problem, and spray behaves differently.",
                [("Off the front wheel, onto the ankle",
                  "The front wheel throws a continuous fan of water backwards onto "
                  "the shoe and the ankle. That is where an overshoe is open, and "
                  "it is where an overshoe ends."),
                 ("Standing water, at speed",
                  "A puddle taken at twenty miles an hour goes into the shoe "
                  "through the vents in a way that rain simply does not."),
                 ("The road is dirtier than the rain",
                  "Road spray carries grit and oil. It stains, it abrades and it "
                  "is why cycling kit wears out faster than walking kit."),
                 ("And then there is nowhere to dry it",
                  "A soaked cycling shoe does not dry under an office desk in "
                  "eight hours. The evening ride starts wet regardless of the "
                  "forecast.")])),
            ("overshoes", overshoes),
            ("drying", cols(
                "The other end", "The ride home starts where the ride in finished.",
                "Almost every product in this category is designed around the "
                "outbound journey. The commute has two halves and only one of them "
                "has a radiator at the end.",
                [("A shoe does not dry in eight hours",
                  "Especially not under a desk, in a building with the heating on "
                  "a timer. Overshoes protect the shoe on the way in; they do not "
                  "dry it by five o'clock."),
                 ("A sock can be swapped",
                  "A second pair in a bag weighs almost nothing and means the "
                  "evening ride starts dry even if the shoe does not. This is the "
                  "practical reason commuters buy two pairs, not a sales "
                  "argument."),
                 ("Wash cool, air dry overnight",
                  "They will be ready for the morning. They will not be ready in "
                  "two hours, and they must never go on a radiator — direct heat "
                  "is what ends a membrane.")],
                link=("How to wash them properly", "/pages/care-and-washing"))),
            ("fit", cols(
                "Fit", "Check the shoe before you order.",
                "Cycling shoes are built with far less volume than a walking boot, "
                "so this matters more here than on any other page.",
                [("Roughly a cushioned training sock",
                  "If your shoes are already snug in a thin summer sock, they will "
                  "be tight in these. Winter shoes and commuting shoes usually "
                  "have room. Race-fit road shoes often do not."),
                 ("Take the larger band if you are between two",
                  "A tight sock in a tight shoe creates a pressure point across "
                  "the toes that you will notice at about mile four."),
                 ("Some people size the shoe up for winter",
                  "If you already run a half size up in winter shoes, these fit "
                  "that space exactly. If you do not, try them in the shoe before "
                  "committing to a long ride.")],
                link=("The size bands in centimetres", "/pages/size-guide"))),
        ]),
        ["problem", "overshoes", "drying", "fit"],
        faq([
            ("Are waterproof socks good for cycling?",
             "Yes, particularly for commuting in the wet. Road spray arrives at "
             "the ankle, which is where an overshoe is open, and a waterproof "
             "sock puts the barrier below that line. They are less useful in cold "
             "wind, where an overshoe also blocks windchill on the shoe."),
            ("Are waterproof socks better than overshoes?",
             "For keeping the foot dry, generally yes, because they seal where "
             "the spray actually arrives. For keeping the shoe dry and blocking "
             "wind, overshoes win. In cold, wet, long conditions many people use "
             "both."),
            ("Will they fit inside cycling shoes?",
             "They sit at about the volume of a cushioned training sock. Winter "
             "and commuting shoes usually have the room; snug race-fit road shoes "
             "often do not. If you already size up for winter shoes, they fit "
             "that space."),
            ("What socks should I wear cycling to work in winter?",
             "Something that is still working on the ride home, when the shoe "
             "never dried. A waterproof sock plus a spare pair in the bag solves "
             "both halves of the commute, which overshoes on their own do not."),
            ("Do waterproof socks keep your feet warm on a bike?",
             "Warmer than a wet sock by a long way, because they stop evaporative "
             "cooling and block the wind reaching the foot. They are not "
             "insulated, though — below about five degrees you may still want an "
             "overshoe over the top."),
            ("How do I wash them after a wet commute?",
             "Rinse the road grit off, then a cool wash inside out with no fabric "
             "softener, and air dry away from any heat. Never on a radiator, "
             "however tempting after a wet ride — direct heat is what kills a "
             "membrane."),
        ]))

    # -------------------------------------------------------------- BOOTS
    apply(
        "all-day-in-boots", "All day in boots",
        collections.OrderedDict([
            ("problem", cols(
                "The problem", "The boot is doing half the job.",
                "A safety boot is built to keep water and everything else out. "
                "Nothing about it is built to let anything back out again.",
                [("Wet from the inside by lunchtime",
                  "A foot produces a serious amount of moisture across a ten-hour "
                  "shift. In a sealed boot most of it stays there, which is why "
                  "feet are wet on dry days too."),
                 ("Wet skin, all winter",
                  "Skin that stays damp for months softens, splits and stops "
                  "recovering overnight. That is the actual cost of this, and it "
                  "is not comfort."),
                 ("Rain and standing water on top of that",
                  "Sites flood, ditches fill and wellies get overtopped. The boot "
                  "handles some of it. The rest arrives anyway.")])),
            ("durability", cols(
                "Durability", "Three weeks is not a membrane problem.",
                "Most cheap waterproof socks do not fail because the membrane is "
                "bad. They fail for three reasons, and two of them are fixable.",
                [("There was no membrane to begin with",
                  "A great deal of what is sold as waterproof is a treated knit "
                  "that sheds light rain and then wets through. If a listing does "
                  "not name a membrane, that is usually why. Ours is Porelle®, "
                  "licensed, and named on every page."),
                 ("The wear face gave out first",
                  "Inside a work boot the abrasion is constant. The outer knit is "
                  "what takes that, and a thin one wears through to the membrane "
                  "in weeks. Three layers exist so the middle one is never the "
                  "wear surface."),
                 ("It went in the tumble dryer",
                  "The most common way a waterproof sock dies, and the least "
                  "discussed. Heat and fabric softener end a laminate far faster "
                  "than a site does. Cool wash, no softener, air dry.")],
                link=("What actually damages a membrane", "/pages/care-and-washing"))),
            ("fit", cols(
                "Fit", "Check the boot before you order.",
                "Safety boots have a fixed toe cap and no give in it. This is the "
                "one thing worth checking before buying.",
                [("Roughly a thick work sock",
                  "If you already wear thick socks in your boots, these replace "
                  "them rather than going over them. If you wear thin socks in a "
                  "snug boot, allow for the difference."),
                 ("Take the larger band if you are between two",
                  "A sock that grips the toes inside a steel toe cap is "
                  "uncomfortable by hour three and shortens the life of the "
                  "membrane."),
                 ("Wellies",
                  "No fit problem at all — wellies have volume to spare, which is "
                  "why a waterproof sock inside a welly is one of the more "
                  "sensible things you can do with one.")],
                link=("The size bands in centimetres", "/pages/size-guide"))),
            ("warranty", cols(
                "If something goes wrong", "Where you stand.",
                "On every other page this sits in the footer links. It is here "
                "because this is where the decision gets made.",
                [("A fault is not the same as wear",
                  "A seam letting water through in the first weeks of normal use "
                  "is a fault. Thinning at the heel after months on site is wear. "
                  "We do not charge for returning faulty goods."),
                 ("Thirty days to reject outright",
                  "Under the Consumer Rights Act 2015 goods must be of "
                  "satisfactory quality, fit for purpose and as described. Within "
                  "thirty days of delivery you can reject them for a full refund."),
                 ("Six months where the fault is presumed ours",
                  "Within six months of delivery, a fault is assumed to have been "
                  "there from the start unless we can show otherwise.")],
                scheme="wash",
                link=("The full warranty position", "/pages/warranty"))),
        ]),
        ["problem", "durability", "fit"],
        faq([
            ("Are waterproof socks good for work boots?",
             "Yes, and mostly for a reason people do not expect. A safety boot "
             "already keeps rain out; what it cannot do is let moisture from the "
             "foot escape across a ten-hour shift. A waterproof breathable sock "
             "addresses the half the boot cannot."),
            ("What socks do you wear with wellies?",
             "A waterproof sock is a sensible choice, because wellies have plenty "
             "of volume and no breathability at all. Feet get wet inside wellies "
             "from the inside far more often than from the outside."),
            ("Will they fit inside safety boots?",
             "They sit at about the bulk of a thick work sock, so they replace "
             "one rather than going over it. Safety boots have a fixed toe cap "
             "with no give, so take the larger band if you are between two."),
            ("How long do they last on site?",
             "Longer than a cheap pair, and shorter than a boot. Abrasion inside "
             "a boot and the wrong wash cycle end a waterproof sock long before "
             "age does — cool wash, no softener, air dry, and never a tumble "
             "dryer or a radiator."),
            ("What are the best socks for standing all day?",
             "Something that manages moisture rather than just adding padding. "
             "Cushioning helps the joints; it does nothing about the fact that a "
             "sealed boot keeps a day's worth of moisture against the skin."),
        ], heading="Asked from site, mostly."),
        buy_overrides={
            "default_quantity": 5,
            "lede": rich(
                "Five pairs is a working week. That is why the five-pair price is "
                "the one most people on site end up taking."),
        },
        after_buy=["warranty"])


if __name__ == "__main__":
    main()
