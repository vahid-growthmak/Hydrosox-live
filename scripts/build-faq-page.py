#!/usr/bin/env python3
"""Builds /pages/faq out to the themed question bank — brief 3.7.

The page carried the same seven questions as the homepage, verbatim: two URLs
with identical content and, once schema was added, identical FAQPage markup. It
now carries its own set, grouped by theme, with a tile grid at the top that jumps
to each group.

No question here repeats the homepage's eight or the category hub's eight in the
same wording — those two sets are listed below and asserted against, because the
whole point of splitting them is undone the moment one is duplicated.

FAQPage structured data stays on the homepage. One page per claim.
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"
PAGE = TPL / "page.faq.json"

HEADER = ("/* FAQ page, composed by scripts/build-faq-page.py.\n"
          "   Re-run that script rather than hand-editing; the question text itself is\n"
          "   editable in the Shopify theme editor. */\n")


def rich(*paras):
    return "".join(f"<p>{p.strip()}</p>" for p in paras if p and p.strip())


def read(path):
    raw = path.read_text()
    m = re.match(r"^\s*/\*[\s\S]*?\*/\s*", raw)
    return (raw[: m.end()] if m else ""), json.loads(
        (raw[m.end():] if m else raw), object_pairs_hook=collections.OrderedDict)


# (anchor, tile title, tile blurb, section eyebrow, section heading, questions)
GROUPS = [
    ("product", "The product", "What it is, what is in it, and what it is not.",
     "The product", "What the sock actually is.", [
        ("What is the membrane, and do you make it?",
         "Porelle® is a third-party waterproof-breathable laminate, licensed rather "
         "than invented here. We knit the sock around it. The membrane's own "
         "composition is its manufacturer's to publish, and we will not guess at it "
         "on their behalf."),
        ("Are they really PFOA free?",
         "That is stated on the product, and it is a claim we carry from the "
         "manufacturer rather than one we have tested ourselves. If you need the "
         "documentation for a procurement process, ask and we will send what the "
         "manufacturer provides."),
        ("What height are they?",
         "Crew height, sitting above the ankle bone. One height only — there is no "
         "ankle or knee-length version, and if that changes this page will say so."),
        ("Which colours are there?",
         "Four: plain black, plain white, black with a navy panel, and black with a "
         "grey panel. The panel is cosmetic; the construction is identical."),
        ("Is there a men's version and a women's version?",
         "No. One sock, sized on foot length, covering UK 3 to UK 14. Splitting a "
         "single product into two listings would tell you nothing that the size "
         "bands do not already."),
     ]),
    ("wudu", "Wudu and masah", "What we report, and what we will not rule on.",
     "Wudu and masah", "Where we stop, and why.", [
        ("Has any scholar or body approved these socks?",
         "No. No certificate has been issued, by us or by anyone else. If one is ever "
         "issued we will publish it here with the name of whoever issued it, and "
         "until then the honest answer is the one above."),
        ("Why will you not simply say they are valid for masah?",
         "Because that is a ruling, and a sock company issuing rulings is not a sock "
         "company you should trust. We state the physical properties. Whether those "
         "satisfy the conditions is for someone qualified to say."),
        ("What are the three properties you keep referring to?",
         "Waterproof, holding their shape when not worn, and staying on the foot. "
         "Those are product facts, stated as product facts. The masah page sets out "
         "the conditions the classical positions describe and names its sources."),
        ("How long does masah last?",
         "That is one of the conditions, not a property of the sock, so it is set out "
         "on the masah page alongside the positions it comes from rather than "
         "answered here as though it were ours to decide."),
     ]),
    ("sizing", "Sizing and fit", "Four bands, measured on the foot.",
     "Sizing and fit", "Measured, not guessed.", [
        ("How do I measure my foot properly?",
         "Stand on a sheet of paper with your heel against a wall, mark the end of "
         "your longest toe, and measure from the wall to the mark. Do it late in the "
         "day, when your foot is at its largest."),
        ("I am between two bands. Which do I take?",
         "The larger one. These are a close, stretchy fit, and a size down grips the "
         "toes and shortens the life of the membrane."),
        ("Do they come in half sizes?",
         "No. Four bands cover UK 3 to UK 14, which is why they are published as foot "
         "lengths in centimetres rather than as shoe sizes."),
        ("Will they stretch out over time?",
         "They relax slightly with wear and recover in the wash. A sock that has gone "
         "permanently slack has usually been dried on heat, which damages the "
         "elastane as well as the membrane."),
        ("The size is wrong. What now?",
         "Fourteen days to change your mind, no reason needed and no form to find. "
         "The returns policy sets out the mechanics."),
     ]),
    ("care", "Washing and care", "What shortens a membrane's life.",
     "Washing and care", "A membrane dies of heat, not of use.", [
        ("Can I put them in the washing machine?",
         "Yes — a cool wash on a gentle cycle. What ends a membrane is heat and "
         "fabric softener rather than the wash itself, so the temperature matters far "
         "more than the method."),
        ("Can I tumble dry them?",
         "No. Heat is the single fastest way to destroy a waterproof membrane, and a "
         "tumble dryer applies it for half an hour at a time."),
        ("Can I use fabric softener?",
         "No. Softener works by coating fibres, and a coated membrane stops passing "
         "vapour — so the sock becomes less breathable rather than softer."),
        ("How should I dry them?",
         "Hung up, away from radiators and direct sun. They dry more slowly than an "
         "ordinary sock, which is the usual reason people who wear them daily keep "
         "three or more pairs."),
        ("Can I iron them or use a steamer?",
         "No. Both apply exactly the heat the membrane cannot survive, and neither is "
         "needed on a knitted sock."),
     ]),
    ("delivery", "Delivery", "Where it ships from, and what we will not promise.",
     "Delivery", "What we will and will not promise.", [
        ("Where do you ship from?",
         "A UK warehouse, held by a UK company. Nothing on this site is dropshipped "
         "from elsewhere and relabelled."),
        ("Do you ship outside the UK?",
         "The shipping policy states where we currently deliver. If your country is "
         "not listed, ask before ordering rather than assuming — we would rather tell "
         "you no than take the money and work it out afterwards."),
        ("When will my order arrive?",
         "No delivery speed is printed anywhere on this site, because we will not "
         "promise one that confirmed stock cannot support. When that changes it will "
         "be stated as a number of days, not as an adjective."),
        ("How do I track my order?",
         "A tracking reference goes out when the parcel is despatched, and the track "
         "order page takes an order number and an email address."),
     ]),
    ("returns", "Returns and faults", "The statutory floor, and what we add.",
     "Returns and faults", "Your rights are the floor, not the ceiling.", [
        ("How long do I have to change my mind?",
         "Fourteen days from delivery to tell us, and fourteen more to send them "
         "back. That is the statutory minimum for a distance sale and we have no "
         "interest in being stingier than the law."),
        ("Do they have to be unworn?",
         "You may examine them as you would in a shop. Wearing a pair for a week on "
         "a hill goes beyond that, and the refund can be reduced accordingly — which "
         "is the law's position, not a policy we invented."),
        ("They leaked. What happens?",
         "That is a faulty product, not a change of mind, and a different set of "
         "rights applies: thirty days to reject them outright for a full refund. Tell "
         "us what happened and where the water came in."),
        ("Who pays for return postage?",
         "It depends which of the two situations above applies, and the refund policy "
         "sets out both. A faulty pair is never at your cost."),
     ]),
    ("company", "The company", "Who you are dealing with.",
     "The company", "Who is behind this.", [
        ("Are you the brand or a reseller?",
         "The brand. We specify and sell the sock; the membrane inside it is licensed "
         "from a third party, which is stated everywhere it is mentioned rather than "
         "quietly implied to be ours."),
        ("Where are you based?",
         "A UK registered company at 399–405 Oxford Street, Mayfair, London W1C 2BU. "
         "The company section publishes the address, the phone number and the email "
         "on every page rather than behind a form."),
        ("Can I speak to an actual person?",
         "Yes. The phone number and email address are answered by people, and neither "
         "is a queue for a ticketing system."),
        ("Do you sell wholesale or to trade?",
         "There is no public trade pricing, and there is no form queue for it either. "
         "The partner page explains what we can and cannot do at this size."),
     ]),
]

# Asserted against, not just documented. Duplicating one of these undoes the
# whole reason for splitting the sets.
def other_pages_questions():
    seen = {}
    for name in ("index", "collection.waterproof-socks"):
        path = TPL / f"{name}.json"
        if not path.exists():
            continue
        _, d = read(path)
        for sec in d["sections"].values():
            if sec.get("type") != "faq-accordion":
                continue
            for k in sec.get("block_order", []):
                q = sec["blocks"][k]["settings"].get("question", "").strip().lower()
                if q:
                    seen[q] = name
    return seen


def main():
    header, d = read(PAGE)
    keep_intro = d["sections"].get("intro")
    keep_still = d["sections"].get("still")
    keep_buy = d["sections"].get("buy")

    S = collections.OrderedDict()
    order = []

    S["intro"] = keep_intro or {"type": "centre-note", "settings": {}}
    S["intro"]["settings"].update({
        "heading_tag": "h1", "heading_size": "h2", "hide_rule": True,
        "eyebrow": "Questions",
        "heading": "Everything we get asked, grouped.",
        "body": rich(
            "Thirty-one questions, in seven groups. The eight on the homepage and the "
            "eight on the waterproof socks page are different questions, not the same "
            "ones reworded — if one of these contradicts something elsewhere on the "
            "site, the more specific page is the one to trust.",
            "Where the answer is “it depends”, it says what it depends on. Where we do "
            "not know, it says that instead of guessing."),
    })
    order.append("intro")

    # The tile grid, reusing the pattern from the contact page's routes grid.
    tiles, tile_order = collections.OrderedDict(), []
    for i, (anchor, title, blurb, *_rest) in enumerate(GROUPS, 1):
        key = f"t{i}"
        tiles[key] = {"type": "card", "settings": {
            "title": title, "body": blurb, "link": f"#{anchor}"}}
        tile_order.append(key)
    S["groups"] = {"type": "link-cards", "settings": {
        "color_scheme": "wash", "columns": 4, "numbered": False, "hide_rule": True,
        "anchor_id": "groups",
        "eyebrow": "Jump to",
        "heading": "Seven groups.",
        "lede": rich("Each one is a section further down this page."),
    }, "blocks": tiles, "block_order": tile_order}
    order.append("groups")

    banned = other_pages_questions()
    clashes, total = [], 0
    for anchor, _t, _b, eyebrow, heading, questions in GROUPS:
        blocks, border = collections.OrderedDict(), []
        for i, (q, a) in enumerate(questions, 1):
            if q.strip().lower() in banned:
                clashes.append((q, banned[q.strip().lower()]))
            key = f"q{i}"
            blocks[key] = {"type": "question", "settings": {
                "question": q, "answer": rich(a)}}
            border.append(key)
            total += 1
        S[anchor] = {"type": "faq-accordion", "settings": {
            "color_scheme": "paper",
            "anchor_id": anchor,
            "one_at_a_time": False,
            # The homepage holds FAQPage for the site.
            "emit_schema": False,
            "eyebrow": eyebrow,
            "heading": heading,
            "help_prefix": "Not here?",
            "help_label": "Phone or email us",
            "help_link": "/pages/contact",
        }, "blocks": blocks, "block_order": border}
        order.append(anchor)

    if clashes:
        for q, where in clashes:
            print(f"  !! duplicates {where}: {q}")
        sys.exit("a question here repeats another page in the same wording")

    if keep_still:
        S["still"] = keep_still
        order.append("still")
    if keep_buy:
        S["buy"] = keep_buy
        order.append("buy")

    out = collections.OrderedDict([("sections", S), ("order", order)])
    PAGE.write_text(HEADER + json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"  {total} questions in {len(GROUPS)} groups, none repeating another page")
    print(f"  order: {' -> '.join(order)}")


if __name__ == "__main__":
    main()
