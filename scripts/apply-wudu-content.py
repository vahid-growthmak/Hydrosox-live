#!/usr/bin/env python3
"""Applies the Phase 3 content to the Wudu Socks page.

Five things the page as built was missing, all of them named in the brief:

  * Four section eyebrows. The design labelled four separate sections "The
    problem" — a copy-paste error — and the build carried the error forward as
    four blank eyebrows. Each one is restored to the label the brief gives it.

  * The "Everyday wudu" section. The brief calls this "the single biggest gap
    in the page as drawn": the page covered Hajj and Umrah, a few weeks of a
    lifetime, and said nothing about wudu at work five times a day, which is
    the actual purchase trigger.

  * Two section ledes that were written but never placed.

  * The question list. It carried four questions copied verbatim from the
    homepage. The brief is explicit that identical Q&A across two URLs competes
    for the same rich result, and supplies eight wudu-specific replacements.

  * The quantity default. Wudu is a daily, five-times-a-day use with a
    wash-and-air-dry cycle, so three pairs is the honest minimum for a rotation.

The boundary this page is written to — the site may state what the sock is and
does, and may report established scholarship with attribution, but may never
state that a person's wudu or prayer is valid — governs every string below.
The word "certified" does not appear, because no certificate exists.

Idempotent: running it twice changes nothing the second time.
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates" / "page.wudu-socks.json"


def rich(text):
    return text if text.strip().startswith("<") else "<p>%s</p>" % text.strip()


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


def read():
    raw = TPL.read_text()
    cut = _lead_comments(raw)
    header = raw[:cut]
    body = raw[cut:]
    return header, json.loads(body, object_pairs_hook=collections.OrderedDict)


def nth(sections, key, position):
    """Settings of the position-th block of a section, 1-indexed.

    Addressed by position rather than by block key: these blocks were written
    by an earlier generator and their keys are an implementation detail, so a
    hardcoded key here would break silently the next time one is regenerated.
    """
    sec = sections[key]
    order = sec.get("block_order") or list(sec["blocks"])
    return sec["blocks"][order[position - 1]]["settings"]


def item(title, body):
    return collections.OrderedDict([
        ("type", "item"),
        ("settings", collections.OrderedDict([
            ("title", title), ("body", rich(body))])),
    ])


def main():
    header, d = read()
    S = d["sections"]

    # ------------------------------------------------------------------- hero
    # The photograph a wudu reader recognises: someone pulling a pair on while
    # seated, which is the moment the product exists for.
    #
    # 2026-08-07, per the client: the hero becomes the split hero — copy left,
    # the photograph standing whole on the right — replacing the full-bleed
    # page-hero. The mockup carries the three property names as text in that
    # right column; the client asked for the image there INSTEAD of that text,
    # so no spec blocks are set. Same words throughout; the heading's line
    # breaks follow the mockup's three-line setting (presentation, not copy).
    # The photo is 4:5, so the plate takes its native aspect uncropped.
    S["hero"] = collections.OrderedDict([
        ("type", "hero-split"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "ink"),
            ("full_height", False),
            ("eyebrow", "Designed with wudu in mind"),
            ("heading", "Built for the\nthree conditions\nmasah turns on."),
            ("body", rich(
                "Waterproof, structured to hold its shape, shaped to stay on "
                "the foot. Those are physical properties we can state plainly. "
                "What they mean for you is yours to judge.")),
            ("cta_label", "Buy a pair"),
            ("cta_link", "/products/hydrosox-waterproof-socks"),
            ("link_label", "How it is built"),
            ("link_url", "/pages/technology"),
            ("image_fallback", "wudu-pulling-on.webp"),
            ("image_alt", "Pulling on a pair of white HydroSox while seated, "
                          "before wudu"),
            ("image_aspect", "4 / 5"),
            ("image_position", "50% 50%"),
        ])),
    ])

    # ---------------------------------------------------------------- eyebrows
    for key, eyebrow in (
        ("certificate", "On certification"),
        ("conditions", "The three properties"),
        ("credentials", "The difference"),
        ("travel", "Travel"),
    ):
        S[key]["settings"]["eyebrow"] = eyebrow

    # ------------------------------------------------------- the JKN ruling
    # Reported as a source, NOT as an endorsement, and the distinction is the
    # whole point.
    #
    # "Wiping over Durable Wudhu Socks" is a real, public, citable ruling about
    # durable wudhu socks as a category. It predates this product by years and
    # says nothing about it. Presenting it as "verified by" would convert a
    # general fatwa into a product endorsement that nobody gave — which
    # misrepresents two named living scholars, contradicts the sentence
    # directly above it on this same page, and is the exact claim the client's
    # own research says needs written permission first.
    #
    # So it is cited the way the masah page cites Nadwi: named, linked, and
    # explicitly bounded. A "Verified by" badge needs written approval from JKN
    # for both the wording and any logo use — info@jkn.org.uk, +44 1274 308456
    # — and this item is where it goes once that exists.
    S["certificate"]["blocks"]["i3"] = collections.OrderedDict([
        ("type", "item"),
        ("settings", collections.OrderedDict([
            ("title", "The ruling this question turns on"),
            ("body", rich(
                "The JKN Fatawa Department in Bradford published "
                "<a href=\"https://jknfatawa.co.uk/wiping-over-durable-wudhu-socks/\" "
                "rel=\"noopener\">Wiping over Durable Wudhu Socks</a> on 25 April "
                "2018, written by Mufti Abdul Waheed and attested by Shaykh "
                "Mufti Saiful Islam. It sets out the criteria commonly "
                "stipulated — covering the ankles, staying up without tying, "
                "durable enough to walk in, water-impermeable, not torn, and "
                "put on after wudhu — and concludes that socks meeting them "
                "may be wiped over. It is a ruling about durable wudhu socks "
                "as a category. It is not a ruling about HydroSox, and we do "
                "not ask you to read it as one.")),
        ])),
    ])
    order = S["certificate"].get("block_order") or list(S["certificate"]["blocks"])
    if "i3" not in order:
        order.append("i3")
    S["certificate"]["block_order"] = order

    # ------------------------------------------------------------------ ledes
    S["certificate"]["settings"]["lede"] = rich(
        "The most important thing on this page, so it comes first.")
    S["credentials"]["settings"]["lede"] = rich(
        "The differentiator is the named membrane. Everything else in this "
        "category tends to be asserted rather than evidenced.")

    # The upright-unworn form is the physical property the masah conditions
    # rest on, and it is the one thing no competitor photograph in the mapped
    # set demonstrates. The sentence and the photograph ship together.
    holds_shape = nth(S, "conditions", 2)
    holds_shape["body"] = rich(
        "Structured so it stays a covering over the foot rather than "
        "collapsing flat against it. It stands upright when it is not being "
        "worn, and you can see that in the photographs on this page.")
    # That sentence has to be able to point at something. The studio shot of the
    # pair standing unsupported is the evidence for the claim, and it is the one
    # visual no competitor in the mapped set publishes. `image` stays empty and
    # overrides this from the theme editor.
    holds_shape["image_fallback"] = "colour-black.webp"
    holds_shape["image_alt"] = (
        "A pair of black HydroSox standing upright unworn, holding their shape")

    nth(S, "travel", 2)["body"] = rich(
        "Most people buying for travel buy more than one pair. The quantity "
        "ladder on this page prices that rather than treating it as a bulk "
        "request.")

    # ------------------------------------------------------- everyday wudu (new)
    everyday = collections.OrderedDict()
    everyday_order = []
    for n, (title, body) in enumerate([
        ("The washroom that was not designed for it",
         "Washing your feet in a shared sink at work is awkward, cold and "
         "slow, and you go back to your desk in wet socks. This is the problem "
         "the sock exists for."),
        ("Ten minutes back, three times a day",
         "The time is not the headline reason people buy, but it is the reason "
         "they buy a second pair."),
        ("Winter, travel, and everywhere in between",
         "Service stations, airports, sites, university prayer rooms. The "
         "places wudu actually happens are rarely the places designed for it."),
    ], 1):
        k = "e%d" % n
        everyday[k] = item(title, body)
        everyday_order.append(k)

    S["everyday"] = collections.OrderedDict([
        ("type", "content-columns"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "wash"),
            ("layout", "list"),
            ("numbered", False),
            ("anchor_id", "every-day"),
            ("eyebrow", "Every day"),
            ("heading", "Wudu at work, five times a day."),
            ("lede", rich(
                "Hajj is a few weeks. The reason most people buy waterproof "
                "wudhu socks is the other fifty-one weeks.")),
            # The highest-value internal link on the site: commercial intent
            # handing off to informational intent, and back again.
            ("link_label", "How masah is performed"),
            ("link_url", "/pages/how-to-make-masah"),
        ])),
        ("blocks", everyday),
        ("block_order", everyday_order),
    ])

    # ------------------------------------------------------------------- FAQ
    questions = [
        ("What are wudhu socks?",
         "Waterproof socks built to the physical properties the masah "
         "conditions rest on: water does not pass through them, they hold "
         "their shape rather than collapsing against the foot, and they stay "
         "in place through normal wear. HydroSox states those properties. It "
         "does not issue rulings on them."),
        ("Are HydroSox certified for wudu?",
         "No. No certificate has been issued, by us or by anyone else. A brand "
         "cannot award itself one. What we publish is what the sock is made of "
         "and how it behaves, so that you — or the scholar you follow — can "
         "judge it."),
        ("What is the difference between these and ordinary waterproof socks?",
         "Nothing in the membrane, and everything in the structure. It is the "
         "same Porelle® laminate in every HydroSox pair. What matters for "
         "masah is that the sock holds its shape as a covering over the foot, "
         "and that is built into the construction rather than added for this "
         "page."),
        ("Are these the same as leather socks or khuffs?",
         "Not the same material, and the same intent. Khuffain are the leather "
         "footwear the classical rulings were written about. These are a "
         "modern waterproof construction aimed at the same physical "
         "properties. Whether that equivalence holds is a question for "
         "scholarship, and the masah page sets out how it is discussed."),
        ("Can women wear these?",
         "Yes. The sock is unisex and the bands start at UK 3. Size on foot "
         "length rather than on the label you are used to."),
        ("How many pairs do I need for daily use?",
         "Most people performing wudu daily keep three. They are washed cool "
         "and air-dried, which takes longer than a tumble dryer would, so a "
         "rotation of three keeps a dry pair available every day."),
        ("Can I wash them without damaging the waterproofing?",
         "Cool wash, inside out, no fabric softener, no bleach, then air dry "
         "away from any heat source. Heat and softener end a membrane far "
         "faster than wearing it does."),
        ("Where can I read about the masah conditions themselves?",
         "On the masah page, which sets out the conditions, how masah is "
         "performed, how long it lasts, and where the schools differ — with "
         "every source named. We report that scholarship. We do not add to it."),
    ]
    blocks, order = collections.OrderedDict(), []
    for n, (q, a) in enumerate(questions, 1):
        k = "q%d" % n
        blocks[k] = collections.OrderedDict([
            ("type", "question"),
            ("settings", collections.OrderedDict([
                ("question", q), ("answer", rich(a))])),
        ])
        order.append(k)
    S["faq"]["blocks"] = blocks
    S["faq"]["block_order"] = order
    # These eight are wudu-specific and share no wording with any other URL, so
    # the page can claim FAQPage for them. It could not while it carried the
    # homepage's four verbatim.
    S["faq"]["settings"]["emit_schema"] = True

    # --------------------------------------------------------------- quantity
    S["buy"]["settings"]["default_quantity"] = 3

    # ------------------------------------------------- presentation (2026-08-07)
    # The client's wudu mockup, layout only — not a word moves. The rhythm rule
    # holds: no two adjacent sections share more than one of layout, scheme and
    # heading side.
    S["conditions"]["settings"].update({
        "layout": "steps", "color_scheme": "paper", "numbered": True})
    S["credentials"]["settings"].update({
        "layout": "split", "color_scheme": "wash"})
    # Band on ink: full-width header, the three everyday cases as outlined
    # cards on the dark ground — the page's turn from argument to reality.
    S["everyday"]["settings"].update({
        "layout": "band", "color_scheme": "ink"})
    S["travel"]["settings"].update({
        "layout": "band", "color_scheme": "paper"})

    # ------------------------------------------------------------------ order
    order = ["crumb", "hero", "certificate", "conditions", "credentials",
             "everyday", "travel", "buy", "reviews", "faq", "scholarly", "close"]
    missing = [k for k in order if k not in S]
    orphans = [k for k in S if k not in order]
    if missing or orphans:
        raise SystemExit("wudu: missing %s orphans %s" % (missing, orphans))
    d["order"] = order

    TPL.write_text(header + json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    print("wrote templates/page.wudu-socks.json  (%d sections, %d questions)"
          % (len(order), len(questions)))


if __name__ == "__main__":
    main()
