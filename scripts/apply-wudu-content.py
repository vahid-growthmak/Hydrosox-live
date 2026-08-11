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
            # v4 (8 Aug 2026): the doc's H1 is the exact search phrase, and
            # the sub-headline names the scholars deliberately — the fact
            # that decides the sale, above the fold.
            ("eyebrow", "Wudu socks"),
            ("heading", "Waterproof socks made\nfor wudu and masah"),
            ("body", rich(
                "Wipe over them during wudu instead of taking them off and "
                "washing your feet. Examined by Shaykh Mufti Saiful Islam "
                "and Mufti Amjad Mohammed.")),
            ("cta_label", "Buy a pair"),
            ("cta_link", "/products/hydrosox-waterproof-socks"),
            ("link_label", "How masah works"),
            ("link_url", "/pages/how-to-make-masah"),
            ("image_fallback", "wudu-pulling-on.webp"),
            ("image_alt", "Pulling on a pair of white HydroSox while seated, "
                          "before wudu"),
            # The homepage hero's ratio, per the client ("the hero section is
            # too big"): the 4:5 source crops to 9:8, and the position rides
            # low so the crop spends itself on the empty top of the frame and
            # the socks stay whole. Nudgeable from the theme editor.
            ("image_aspect", "9 / 8"),
            ("image_position", "50% 85%"),
        ])),
        # The doc's S2 spec bar, rendered by the hero's own spec strip —
        # the fourth cell is the page's argument in two words.
        ("blocks", collections.OrderedDict([
            ("sp1", {"type": "spec", "settings": {
                "label": "Waterproof layer", "value": "Porelle® membrane"}}),
            ("sp2", {"type": "spec", "settings": {
                "label": "Build", "value": "Three layers"}}),
            ("sp3", {"type": "spec", "settings": {
                "label": "Sizes", "value": "UK 3 to 14"}}),
            ("sp4", {"type": "spec", "settings": {
                "label": "Examined by", "value": "Two UK scholars"}}),
        ])),
        ("block_order", ["sp1", "sp2", "sp3", "sp4"]),
    ])

    # ---------------------------------------------------------------- eyebrows
    for key, eyebrow in (
        ("conditions", "The conditions"),
        ("credentials", "Examined by"),
        ("travel", "Travelling"),
    ):
        S[key]["settings"]["eyebrow"] = eyebrow

    # ------------------------------------------------- what masah is (v4 S3)
    # The v4 document replaces the certification note with the plain-language
    # explainer, and moves the scholars to their own section below. The
    # "Verified by prominent scholars" note (client-ordered 2026-08-07) is
    # superseded by the same client's v4 document (8 Aug 2026), whose framing
    # is "examined by" — the wording their own research always required.
    S["certificate"] = collections.OrderedDict([
        ("type", "content-columns"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("layout", "prose"),
            ("anchor_id", "masah"),
            ("eyebrow", "If you’re new to this"),
            ("heading", "What masah is"),
            ("prose", (
                "<p>Masah means wiping over your socks during wudu instead of "
                "taking them off and washing your feet. It’s permitted on "
                "footwear that meets certain conditions, and scholars have "
                "written about those conditions for a very long time.</p>"
                "<p>In everyday terms, it means you can make wudu at your "
                "desk, at the mosque, or at a service station, without finding "
                "somewhere to wash your feet and without going back to your "
                "prayer in wet socks.</p>")),
            ("footnote", (
                "We make socks. We’re not scholars, and nothing on this "
                "page is a ruling. We’ll tell you what the socks are and "
                "what the conditions are, so you can decide — or ask "
                "someone qualified.")),
        ])),
    ])

    # ------------------------------------------------------------------ ledes
    # ------------------------------------------------- the conditions (v4 S4)
    S["conditions"]["settings"].update({
        "heading": "What the socks have to do",
        "lede": rich(
            "Scholars set conditions for the footwear you’re allowed to "
            "wipe over. Three of them are about the sock itself, and those are "
            "the three we can speak to."),
        "footnote": (
            "There’s one more condition, and it’s about you rather "
            "than the socks. You put them on after a full wudu, with your feet "
            "washed. From your next wudu onwards, you wipe."),
    })
    cond_rows = [
        ("Water mustn’t get through to your foot",
         "Cotton socks soak through. Ours have a Porelle® waterproof layer "
         "sealed inside them, so water doesn’t reach the skin. It’s "
         "the same layer in every pair we make — there’s no separate "
         "wudu version."),
        ("They have to hold their shape",
         "They need to sit over the foot as a covering rather than collapse "
         "flat against it. Ours stand up on their own when you take them off, "
         "and there’s a photograph of that below."),
        ("They have to stay on your foot",
         "Shaped so they stay in place through a normal day rather than "
         "working loose and sliding down."),
    ]
    for pos, (title, body) in enumerate(cond_rows, 1):
        row = nth(S, "conditions", pos)
        row["title"] = title
        row["body"] = rich(body)
        row.pop("image_fallback", None)
        row.pop("image_alt", None)

    # --------------------------------------------------- the scholars (v4 S5)
    # The document's own red block: nothing conclusive can be published until
    # each scholar's written confirmation, permission and exact words exist.
    # Its stated fallback applies — the section says only that they examined
    # the socks, with no conclusion attached. The "[His own words, to be
    # supplied]" placeholders, the "published in full, unedited" claim and
    # the "Read what they said" link all wait for the client's material.
    S["credentials"]["settings"].update({
        "heading": "Who has looked at them",
        "lede": rich(
            "We didn’t want to make a religious claim about our own "
            "socks, so we asked people qualified to look at them."),
        "footnote": (
            "There’s no certificate, because no organisation issues "
            "certificates for socks. What we have is two qualified scholars "
            "who examined them. If you follow a different school or a "
            "different scholar, ask them. We’d rather you were sure than "
            "take our word for it."),
        "link_label": "", "link_url": "",
    })
    # The names carry the client-verified links (supplied 10 Aug 2026):
    # Saiful Islam to the JKN Institute's own about page, Amjad Mohammed to
    # his Wikipedia biography. Liquid renders titles unescaped, so the
    # anchor survives; the row-title link style lives in hs-pages.css.
    S["credentials"]["blocks"] = collections.OrderedDict([
        ("sc1", item(
            '<a href="https://www.jkn.org.uk/about-us/" rel="noopener">'
            "Shaykh Mufti Saiful Islam</a>",
            "Founder and Principal of the JKN Institute in Bradford, where "
            "he also heads the fatwa service.")),
        ("sc2", item(
            '<a href="https://en.wikipedia.org/wiki/Amjad_M._Mohammed" '
            'rel="noopener">Mufti Amjad Mohammed</a>',
            "Founder and Principal of Dār al-ʿUlūm al-Zaytuniyya in "
            "Bradford, and a lecturer in Islamic jurisprudence. He has "
            "written extensively on Islamic law for Muslims living in "
            "Britain.")),
    ])
    S["credentials"]["block_order"] = ["sc1", "sc2"]

    # ---------------------------------------------------- travel (v4 S7)
    S["travel"]["settings"]["heading"] = "Hajj, Umrah and travel"
    S["travel"]["blocks"] = collections.OrderedDict([
        ("tv1", item(
            "Long days, shared facilities",
            "Pilgrimage means long days, busy washrooms and nowhere to dry "
            "anything properly. A pair that keeps water out and dries "
            "overnight is worth the space in the bag.")),
        ("tv2", item(
            "Take more than one pair",
            "Most people travelling take two or three. They wash cool and "
            "air dry, which is slower than a tumble dryer, so one pair "
            "won’t keep up.")),
    ])
    S["travel"]["block_order"] = ["tv1", "tv2"]

    # ------------------------------------------------------- everyday wudu (new)
    everyday = collections.OrderedDict()
    everyday_order = []
    for n, (title, body) in enumerate([
        ("Wudu at work",
         "Washing your feet in a basin built for hands is awkward, cold and "
         "slow — and then you sit in damp socks for the rest of the "
         "afternoon."),
        ("Ten minutes back, several times a day",
         "Not usually the reason people buy the first pair. Often the reason "
         "they come back for a second."),
        ("Everywhere that isn’t a mosque",
         "Airports, building sites, university prayer rooms, car parks in "
         "February. Wudu rarely happens somewhere designed for it."),
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
            ("heading", "Why people buy them"),
            ("lede", rich(
                "Hajj comes round once. Most people buy these for the other "
                "fifty-one weeks of the year.")),
            # The highest-value internal link on the site: commercial intent
            # handing off to informational intent, and back again.
            ("link_label", "How masah is done, step by step"),
            ("link_url", "/pages/how-to-make-masah"),
        ])),
        ("blocks", everyday),
        ("block_order", everyday_order),
    ])

    # ------------------------------------------------------------------- FAQ
    # v4 doc questions. Q2's "Their words are published in full" clause waits
    # with the quotes themselves (the doc's red block); the answer ships
    # truncated to what is true today. Q4 and Q6 carry the doc's own fiqh
    # framing and are flagged in its red block for scholar checking — the
    # client instructed publication of the document as supplied.
    questions = [
        ("What are wudu socks?",
         "Waterproof socks made so you can wipe over them during wudu instead "
         "of washing your feet. They need to keep water out, hold their shape "
         "and stay on the foot — those are the conditions scholars set "
         "for the footwear itself."),
        ("Are these certified for wudu?",
         "No, and no sock is — there’s no organisation that issues "
         "certificates for this. What we have is two UK scholars who examined "
         "the socks."),
        ("Do I still have to wash my feet?",
         "You wash them as part of a full wudu before the socks go on. From "
         "your next wudu onwards, you wipe over them instead. The masah page "
         "sets it out step by step."),
        ("How long can I keep wiping for?",
         "Scholars give twenty-four hours if you’re at home and "
         "seventy-two if you’re travelling. The clock starts at your "
         "first wipe after wudu breaks, not when you put the socks on. "
         "That’s the part most people have slightly wrong."),
        ("What’s different about these and your other socks?",
         "Nothing in the waterproof layer — it’s the same in every "
         "pair. What matters for masah is that the sock holds its shape "
         "rather than collapsing onto the foot, and that’s built into how "
         "it’s knitted."),
        ("Are these the same as leather socks or khuffs?",
         "Not the same material. Khuffs are the leather footwear the "
         "classical rulings were written about. These are a modern waterproof "
         "version aimed at the same three properties. Whether that counts as "
         "equivalent is a question for scholars, and the masah page explains "
         "how it’s discussed."),
        ("Can women wear them?",
         "Yes. They’re unisex and start at UK 3. Go by your foot length "
         "rather than the men’s or women’s size you’re used "
         "to."),
        ("Will washing them ruin them?",
         "Cool wash, inside out, no fabric softener, then air dry away from "
         "the radiator. Heat and softener are what finish off a waterproof "
         "layer, not wearing them."),
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
    # v4 S8: the buy heading and the three-pair intro that explains the
    # pre-selected quantity.
    S["buy"]["settings"]["heading"] = "Choose your colour and size"
    S["buy"]["settings"]["lede"] = rich(
        "Praying five times a day means washing them often. Most people here "
        "keep three pairs so there’s always a dry one, which is why three "
        "is already selected.")

    # ---------------------------------------------------- ask us (v4 S10)
    S["scholarly"]["settings"].update({
        "eyebrow": "Ask us",
        "heading": "Ask us anything about how they’re made",
        "lede": rich(
            "If you need a specific detail to make up your own mind, or your "
            "imam does, ask us. We’ll tell you what’s in them and how "
            "they behave. We won’t tell you whether your wudu is valid, "
            "because that isn’t ours to say."),
    })

    # ------------------------------------------------- presentation (2026-08-07)
    # The client's wudu mockup, layout only — not a word moves. The rhythm rule
    # holds: no two adjacent sections share more than one of layout, scheme and
    # heading side.
    # Three properties, to the mockup's DOM: plain numbered rows at the large
    # scale on wash, with the wudu design sheet as the heading column's figure
    # — the photograph holds still with the claim while the rows scroll.
    S["conditions"]["settings"].update({
        "layout": "list", "color_scheme": "wash", "numbered": True,
        "row_scale": "large",
        "media_fallback": "wudu-design-sheet.jpg",
        "media_alt": (
            "HydroSox wudu design sheet: structured construction that holds "
            "its shape and stands upright when not worn, durable waterproof "
            "materials, and long-term durability."),
        "media_caption": (
            "A pair of black HydroSox standing upright unworn, holding their "
            "shape.")})
    # The difference, to the mockup's DOM: the header block above, the split
    # rows running the full width beneath it, on paper.
    S["credentials"]["settings"].update({
        "layout": "split", "color_scheme": "paper", "wide_head": True})
    # Scholarly questions, to the mockup's DOM: the company band on pale blue
    # with the header centred and the brand email standing under it as the
    # section's action — the section IS the invitation to write in.
    S["scholarly"]["settings"].update({
        "color_scheme": "blue", "centre_head": True, "email_cta": True})
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
