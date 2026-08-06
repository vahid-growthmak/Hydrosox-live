#!/usr/bin/env python3
"""Applies the client's homepage content spec to templates/index.json.

templates/index.json is hand-maintained rather than generated — the product and
activity template builders read *from* it — so this edits in place and is written
to be idempotent: running it twice changes nothing the second time.

Structural changes, from the spec's layout audit:
  - the buy widget moves below the proof sections (3.2)
  - wudu is promoted from a strip under the grid to a card inside it (3.5), and
    the standalone strip is deleted
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates/index.json"


def rich(text):
    """Rich text as Shopify stores it. A bare string is refused on upload."""
    t = text.strip()
    return t if t.startswith(("<p", "<ul", "<ol", "<h")) else f"<p>{t}</p>"


def load():
    raw = TPL.read_text()
    m = re.match(r"^\s*/\*[\s\S]*?\*/\s*", raw)
    header = raw[: m.end()] if m else ""
    body = raw[m.end():] if m else raw
    return header, json.loads(body, object_pairs_hook=collections.OrderedDict)


def save(header, data):
    TPL.write_text(header + json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main():
    header, d = load()
    S = d["sections"]
    changed = []

    # ---------------------------------------------------------------- S1 hero
    hero = S["hero"]["settings"]
    hero["eyebrow"] = "Waterproof socks"
    hero["body"] = rich(
        "A licensed Porelle® membrane sealed inside a three-layer knit. Hiking, "
        "running, cycling, work and wudu — the day carries on when the weather turns."
    )
    hero["image_alt"] = (
        "Four pairs of HydroSox waterproof socks in black, white, navy and grey, "
        "stood upright"
    )
    # S2 spec bar — the hero's own blocks. Two of the four values are restated.
    spec_values = {
        "Membrane": "Porelle®, licensed",
        "Construction": "Three-layer knit",
        "Chemistry": "PFOA free",
        "Origin": "UK company, UK stock",
    }
    for bk in S["hero"]["block_order"]:
        b = S["hero"]["blocks"][bk]["settings"]
        if b.get("label") in spec_values:
            b["value"] = spec_values[b["label"]]
    changed.append("S1 hero eyebrow, body, alt + S2 spec values")

    # ------------------------------------------- S3 product summary (new)
    # Takes the position the buy widget used to hold: enough to orient a first
    # visit, not enough to interrupt it.
    S["summary"] = collections.OrderedDict([
        ("type", "content-columns"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("layout", "list"),
            ("numbered", False),
            ("anchor_id", "product"),
            ("eyebrow", "The product"),
            ("heading", "One sock, four colours, four sizes"),
            ("lede", rich(
                "A crew-height waterproof sock in UK 3 to UK 14, from £20 a pair. "
                "The same sock and the same price whichever page you arrived on."
            )),
            ("cta_label", "Choose a size"),
            ("cta_url", "/#buy"),
        ])),
        ("blocks", collections.OrderedDict([
            ("p1", {"type": "item", "settings": {
                "title": "From £20 a pair",
                "body": rich(
                    "Free UK delivery on two pairs or more. Buying more than one "
                    "brings the per-pair price down to £16."
                )}}),
            ("p2", {"type": "item", "settings": {
                "title": "Sized on foot length, not shoe size",
                "body": rich(
                    "Four bands cover UK 3 to UK 14. Shoe sizing is not consistent "
                    "between brands, and the foot is what actually has to fit."
                )}}),
            ("p3", {"type": "item", "settings": {
                "title": "Fourteen days to change your mind",
                "body": rich(
                    "No reason needed, and no form to find. Your statutory rights "
                    "are the floor here, not the ceiling."
                )}}),
        ])),
        ("block_order", ["p1", "p2", "p3"]),
    ])
    changed.append("S3 product summary added")

    # ------------------------------------------------------------ S4 compare
    comp = S["comparison"]["settings"]
    comp["lede"] = rich(
        "We are new, and you have no reason to take our word for anything. So this "
        "compares what you can verify yourself in about four minutes — not what we "
        "would like you to feel."
    )
    # Naming a competitor's price range in a comparison we control is a
    # Business Protection from Misleading Marketing Regulations 2008 exposure:
    # comparative claims must be verifiable and kept current, and a price
    # printed today is wrong within months. The generalised line makes the same
    # point and carries none of that.
    for bk in S["comparison"]["block_order"]:
        b = S["comparison"]["blocks"][bk]["settings"]
        if b.get("label") == "Price per pair":
            b["ours_note"] = (
                "Cheaper waterproof socks exist. Those are the ones that do not "
                "name a membrane."
            )
    changed.append("S4 lede + row 4 note de-risked")

    # -------------------------------------------------------- S7 construction
    con = S["construction"]["settings"]
    con["heading"] = "Three layers, and what each is for."
    con["lede"] = rich(
        "“Waterproof” is a claim anybody can print on a label. This is the mechanism "
        "underneath it, so you can judge it rather than take our word."
    )
    layer_bodies = {
        "Inner layer": "A soft knitted lining that moves sweat off the foot and "
                       "stops the membrane sitting against the skin.",
        "Porelle® membrane": "A licensed third-party laminate. Water cannot get in; "
                             "vapour from the foot can get out.",
        "Outer layer": "The knitted face that takes abrasion inside a boot or shoe, "
                       "and holds the sock's shape when it is not being worn.",
    }
    for bk in S["construction"]["block_order"]:
        b = S["construction"]["blocks"][bk]
        if b["type"] == "layer" and b["settings"].get("heading") in layer_bodies:
            b["settings"]["body"] = rich(layer_bodies[b["settings"]["heading"]])
        # The old link duplicated the comparison's destination; this one builds
        # the relationship the Technology page needs.
        if b["type"] == "link":
            b["settings"]["label"] = "How the layers are made"
            b["settings"]["link"] = "/pages/technology"
    changed.append("S7 shortened + link repointed to /pages/technology")

    # ---------------------------------------------------------- S8 shop by use
    act = S["activity"]
    # The header menu says "Shop by Activity"; the section it links to has to say
    # the same thing. The spec renamed this to "Shop by use" in isolation, which
    # left the nav label and its destination disagreeing.
    act["settings"]["eyebrow"] = "Shop by Activity"
    act["settings"]["heading"] = "Find the version of wet feet you actually have."
    act["settings"]["lede"] = rich(
        "One sock. Five different problems it solves, described the way the people "
        "with those problems describe them."
    )
    # The deleted wudu strip's honest sentence about certification lands here, so
    # the statement stays prominent without the same message twice on one page.
    act["settings"]["footnote"] = (
        "Same sock either way — the activity only changes which pair you reach for. "
        "No certificate has been issued for the wudu claim, and the wudu page "
        "says so on its face."
    )

    # Wudu leads, at the size Hiking used to hold. The other four drop to a
    # single column each: featured spans 2 columns and 2 rows, so four singles
    # fill the remaining 2x2 exactly. Any other mix leaves a hole in the bento.
    existing = {}
    for bk in act["block_order"]:
        st = act["blocks"][bk]["settings"]
        existing[st.get("title")] = (bk, st)

    wudu = collections.OrderedDict([
        ("size", "featured"),
        ("title", "Wudu & Masah"),
        ("problem", "Wudu at work, five times a day, without taking your socks off."),
        ("meta", "Built for the three conditions"),
        ("link", "/pages/wudu-socks"),
        ("image_fallback", "activity-wudu-masah.webp"),
        ("image_alt", "Pulling on a pair of white HydroSox while seated"),
    ])
    order = ["a_wudu"]
    blocks = collections.OrderedDict()
    blocks["a_wudu"] = {"type": "activity", "settings": wudu}
    for title in ("Hiking & Walking", "All Day in Boots",
                  "Cycling & Commuting", "Running & Trail"):
        if title not in existing:
            sys.exit(f"activity card missing from homepage: {title}")
        bk, st = existing[title]
        st["size"] = "standard"
        blocks[bk] = {"type": "activity", "settings": st}
        order.append(bk)
    act["blocks"], act["block_order"] = blocks, order
    changed.append("S8 five cards, wudu featured, others standard")

    # ------------------------------------------------- S9 the wudu strip goes
    if "wudu" in S:
        del S["wudu"]
        changed.append("S9 standalone wudu strip deleted")

    # ------------------------------------------------------------- S10 the FAQ
    faq = S["faq"]
    faq["settings"]["emit_schema"] = True
    if not any(faq["blocks"][k]["settings"].get("question", "").startswith("Can I use these for wudu")
               for k in faq["block_order"]):
        faq["blocks"]["q_wudu"] = {"type": "question", "settings": {
            "question": "Can I use these for wudu?",
            "answer": rich(
                "They are built to the three physical properties the masah conditions "
                "rest on: waterproof, holding their shape, and staying on the foot. "
                "No certificate has been issued, by us or by anyone else. The masah "
                "page sets out the conditions and names its sources."
            )}}
        # Fourth, after the three that establish what the product is.
        faq["block_order"].insert(3, "q_wudu")
        changed.append("S10 wudu question added (7 -> 8)")
    changed.append("S10 FAQPage schema on")

    # ------------------------------------------------------- S11 the company
    S["about"]["settings"]["emit_schema"] = True
    changed.append("S11 Organization schema on")

    # ------------------------------------------------------------------ order
    # Buy widget below the proof. Spec 3.2: on every page that is not the PDP,
    # the buy block sits under the content rather than above it.
    d["order"] = [
        "hero", "summary", "comparison", "limits", "film",
        "construction", "activity", "buy", "faq", "about", "signup",
    ]
    missing = [k for k in d["order"] if k not in S]
    extra = [k for k in S if k not in d["order"]]
    if missing or extra:
        sys.exit(f"order mismatch — missing {missing}, orphaned {extra}")

    save(header, d)
    for c in changed:
        print(f"  {c}")
    print(f"\n  order: {' -> '.join(d['order'])}")


if __name__ == "__main__":
    main()
