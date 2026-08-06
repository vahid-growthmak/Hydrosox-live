#!/usr/bin/env python3
"""Composes the Waterproof Socks category hub — templates/page.waterproof-socks.json.

The page answers "are waterproof socks the right thing for me?", which is a
different question from the product page's "is this the right sock, in my size,
at this price?". The two must share no copy, or Google picks one of them and the
choice may not be the one that converts. With a single-SKU catalogue that
duplication is the most damaging thing the site could do to itself.

So: the argument runs first and the buy widget comes last. The one piece of
repeated content is the buy widget itself, which is functional rather than
editorial.

The five use-case links point at /pages/*, which is where those pages live, and
the hub itself is a page too. The brief's URL map puts all of it under
/collections/* — the client ruled the other way, twice: pages only. The
waterproof-socks collection therefore goes back on the noindex list, because
without this template it renders Shopify's default product grid, which is a thin
duplicate of the product page — the exact thing brief 3.1 calls the most damaging
duplication on the site.
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates/page.waterproof-socks.json"
INDEX = ROOT / "templates/index.json"

HEADER = (
    "/* Waterproof Socks category hub, composed by scripts/build-category-hub.py.\n"
    "   Re-run that script rather than hand-editing; the section content itself is\n"
    "   editable in the Shopify theme editor. Bound to the waterproof-socks page\n"
    "   through its template suffix. */\n"
)

PRODUCT = "/products/hydrosox-waterproof-socks"


def rich(*paragraphs):
    """Rich text as Shopify stores it. A bare string is refused on upload."""
    return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p and p.strip())


def load_index():
    raw = INDEX.read_text()
    raw = re.sub(r"^\s*/\*[\s\S]*?\*/\s*", "", raw, count=1)
    return json.loads(raw, object_pairs_hook=collections.OrderedDict)


def buy_widget():
    """The homepage buy widget, copied wholesale.

    Copied rather than re-declared so the price ladder, the colourways and the
    size guide cannot diverge between the two pages. Repeated deliberately: a
    purchase widget is functional, and everything above it here is unique.
    """
    idx = load_index()
    buy = json.loads(json.dumps(idx["sections"]["buy"]), object_pairs_hook=collections.OrderedDict)
    buy["settings"]["anchor_id"] = "buy"
    return buy


def main():
    S = collections.OrderedDict()

    # -------------------------------------------------------------- breadcrumb
    # "Waterproof socks", not "HydroSox Waterproof Socks" — that label belongs to
    # the product page, and using it here is what made the two pages look like
    # the same page to a crawler.
    S["crumb"] = {"type": "breadcrumb", "settings": {
        "color_scheme": "paper",
        "home_label": "Home",
        "current_label": "Waterproof socks",
    }}

    # ------------------------------------------------------------------ S1 + S2
    S["hero"] = collections.OrderedDict([
        ("type", "hero-split"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "ink"),
            ("full_height", False),
            ("eyebrow", "Waterproof socks"),
            ("heading", "Waterproof socks, and what they honestly do."),
            ("body", rich(
                "A membrane sealed inside a knitted sock, so the water stays outside "
                "it. That works well in some conditions and less well in others, and "
                "this page covers both."
            )),
            ("cta_label", "Buy a pair"),
            ("cta_link", "#buy"),
            ("link_label", "How they work"),
            ("link_url", "#mechanism"),
            ("image_alt",
             "Four pairs of HydroSox waterproof socks in black, white, navy and grey, "
             "stood upright"),
            ("image_aspect", "9 / 8"),
            ("image_position", "50% 41%"),
        ])),
        ("blocks", collections.OrderedDict([
            ("s1", {"type": "spec", "settings": {"label": "Membrane", "value": "Porelle®, licensed"}}),
            ("s2", {"type": "spec", "settings": {"label": "Construction", "value": "Three-layer knit"}}),
            ("s3", {"type": "spec", "settings": {"label": "Chemistry", "value": "PFOA free"}}),
            ("s4", {"type": "spec", "settings": {"label": "Origin", "value": "UK company, UK stock"}}),
        ])),
        ("block_order", ["s1", "s2", "s3", "s4"]),
    ])

    # ------------------------------------------------------------------- S3
    # Written to be extracted: the first paragraph is a self-contained definition
    # that answers the query without the rest of the page, set a size larger so
    # it reads as one. It sits in the same left-heading/right-content structure
    # as every other section on the page — in a centred note the 55-word opening
    # ran nine centred lines, which read as a wall rather than a definition.
    S["definition"] = collections.OrderedDict([
        ("type", "content-columns"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("layout", "prose"),
            ("anchor_id", "definition"),
            ("eyebrow", "The definition"),
            ("heading", "A membrane, wearing a sock."),
            ("lead_first_para", True),
            ("prose", rich(
                "A waterproof sock is an ordinary-looking sock with a "
                "waterproof-breathable membrane sealed between two knitted layers. "
                "The knit gives it the feel and fit of a sock; the membrane stops "
                "liquid water passing through while still letting vapour from the "
                "foot escape. Worn inside a boot or shoe, it keeps the foot dry when "
                "the footwear no longer can.",
                "That last part is the point most descriptions skip. A waterproof "
                "sock is not a better sock. It is a layer that keeps working at the "
                "moment your boots stop — four hours into wet ground, or on the ride "
                "home when the shoes never dried from this morning.",
            )),
        ])),
    ])

    # ------------------------------------------------------------------- S4
    S["mechanism"] = collections.OrderedDict([
        ("type", "content-columns"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("layout", "list"),
            ("numbered", True),
            ("anchor_id", "mechanism"),
            ("eyebrow", "The mechanism"),
            ("heading", "Three layers, and why there are three."),
            ("lede", rich(
                "A single waterproof layer would be uncomfortable and would not last. "
                "The other two are there to make the middle one wearable."
            )),
            ("link_label", "The full construction, layer by layer"),
            ("link_url", "/pages/technology"),
        ])),
        ("blocks", collections.OrderedDict([
            ("m1", {"type": "item", "settings": {
                "title": "Inner layer — against the skin",
                "body": rich(
                    "A knitted lining that moves sweat away from the foot and keeps "
                    "the membrane from sitting directly against the skin, which is "
                    "what makes a waterproof sock feel like a sock rather than a bag."
                )}}),
            ("m2", {"type": "item", "settings": {
                "title": "Membrane — the waterproof barrier",
                "body": rich(
                    "A licensed Porelle® laminate. Liquid water cannot pass through "
                    "it. Water vapour, which is a much smaller molecule, can. That "
                    "asymmetry is the whole technology, and it has been around for "
                    "decades."
                )}}),
            ("m3", {"type": "item", "settings": {
                "title": "Outer layer — the wear surface",
                "body": rich(
                    "The knitted face that takes the abrasion inside a boot. It is "
                    "also what holds the sock's shape when it is not being worn, "
                    "which matters for durability and, separately, for masah."
                )}}),
        ])),
        ("block_order", ["m1", "m2", "m3"]),
    ])

    # ------------------------------------------------------------------- S5
    # Category-level limits, phrased so they do not repeat the product-level
    # limits on the homepage. Same honesty, different sentences.
    #
    # Widths tile the four-column grid: the dark intro spans 2 columns and 2
    # rows, so columns 3-4 need filling on both — two singles, then one double.
    S["limits"] = collections.OrderedDict([
        ("type", "honest-limits"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "ink"),
            ("anchor_id", "limits"),
            ("eyebrow", "The limits"),
            ("heading", "Three things no waterproof sock does."),
            ("lede", rich(
                "This is the part of the category nobody writes down. It is also the "
                "part that decides whether waterproof socks are right for you, so it "
                "goes above the price rather than below it."
            )),
            ("link_label", "How they are built"),
            ("link_url", "/pages/technology"),
        ])),
        ("blocks", collections.OrderedDict([
            ("l1", {"type": "limit", "settings": {
                "heading": "Water deeper than the cuff",
                "body": rich(
                    "A sock is open at the top. Step into water above the cuff and it "
                    "fills, exactly as any sock would. Height is the only thing that "
                    "changes where that line sits."
                ),
                "width": "1", "tone": "wash"}}),
            ("l2", {"type": "limit", "settings": {
                "heading": "Sustained hard effort",
                "body": rich(
                    "Breathability is real and it is finite. Work hard enough for long "
                    "enough and your foot produces vapour faster than any membrane can "
                    "move it. You end up damp from the inside instead of the outside."
                ),
                "width": "1", "tone": "wash"}}),
            ("l3", {"type": "limit", "settings": {
                "heading": "A punctured membrane",
                "body": rich(
                    "Once the laminate is pierced — a toenail, a thorn, a sharp stone "
                    "inside a boot — the waterproofing is gone and cannot be restored. "
                    "No wash, no spray and no reproofing treatment brings it back."
                ),
                "width": "2", "tone": "blue"}}),
        ])),
        ("block_order", ["l1", "l2", "l3"]),
    ])

    # ------------------------------------------------------------------- S6
    # The internal linking hub, and the reason this page exists for search. The
    # anchor text is the keyword phrase inside the sentence rather than the
    # heading: it reads naturally and it carries the term the destination owns.
    S["byuse"] = collections.OrderedDict([
        ("type", "content-columns"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "wash"),
            ("layout", "list"),
            ("numbered", False),
            ("anchor_id", "by-use"),
            ("eyebrow", "By use"),
            ("heading", "Five problems, one sock."),
            ("lede", rich(
                "The sock does not change. What changes is which of these you "
                "recognise, and therefore which page is worth your time."
            )),
        ])),
        ("blocks", collections.OrderedDict([
            ("u1", {"type": "item", "settings": {
                "title": "Wudu and masah",
                "body": rich(
                    "Performing wudu five times a day, often somewhere that was not "
                    "designed for it. <a href=\"/pages/wudu-socks\">Waterproof wudhu "
                    "socks</a> are the reason most people find this site."
                )}}),
            ("u2", {"type": "item", "settings": {
                "title": "Hiking and walking",
                "body": rich(
                    "<a href=\"/pages/hiking-and-walking\">Waterproof walking socks</a> "
                    "for the point, usually four hours in, where a boot has wet out and "
                    "there is nowhere on a hill to dry anything."
                )}}),
            ("u3", {"type": "item", "settings": {
                "title": "Long days in boots",
                "body": rich(
                    "<a href=\"/pages/all-day-in-boots\">Waterproof work socks</a> for a "
                    "ten-hour shift where the boot keeps the rain out and then keeps "
                    "everything the foot produces in."
                )}}),
            ("u4", {"type": "item", "settings": {
                "title": "Cycling and commuting",
                "body": rich(
                    "<a href=\"/pages/cycling-and-commuting\">Waterproof cycling socks</a> "
                    "for road spray, and for shoes that are still wet at home time "
                    "because nothing dried at the office."
                )}}),
            ("u5", {"type": "item", "settings": {
                "title": "Running and trail",
                "body": rich(
                    "<a href=\"/pages/running-and-trail\">Waterproof running socks</a> for "
                    "cold winter miles and wet races — with the honest caveat about "
                    "weight and warm-weather use on that page."
                )}}),
        ])),
        ("block_order", ["u1", "u2", "u3", "u4", "u5"]),
    ])

    # ------------------------------------------------------------------- S7
    # Against other *solutions*, not other brands. More useful to the reader, and
    # it carries none of the comparative-advertising exposure that naming a
    # competitor's prices would.
    S["alternatives"] = collections.OrderedDict([
        ("type", "comparison-table"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("anchor_id", "alternatives"),
            ("eyebrow", "The alternatives"),
            ("heading", "Against the other three options."),
            ("lede", rich(
                "Most people arriving here are choosing between four things, not four "
                "brands. This is where each one wins."
            )),
            ("table_caption",
             "Four ways to keep feet dry, with the conditions each one works and "
             "fails in."),
            ("col_criterion", "The option"),
            ("col_ours", "Works when"),
            ("col_theirs", "Fails when"),
        ])),
        ("blocks", collections.OrderedDict([
            ("a1", {"type": "criterion", "settings": {
                "label": "Ordinary socks + waterproof boots",
                "ours_value": "The ground is wet but shallow, and the day is short "
                              "enough that the boot does not wet out.",
                "theirs_value": "The boot wets out, or water comes over the top."}}),
            ("a2", {"type": "criterion", "settings": {
                "label": "Waterproof socks + any footwear",
                "ours_value": "The footwear will get wet and you accept that, but the "
                              "foot must not. Lets you wear lighter, cheaper or "
                              "non-waterproof shoes.",
                "theirs_value": "Water goes over the cuff, or the effort is hard enough "
                                "to out-sweat the membrane."}}),
            ("a3", {"type": "criterion", "settings": {
                "label": "Overshoes (cycling)",
                "ours_value": "You want to keep the shoe itself dry and block wind as "
                              "well as water.",
                "theirs_value": "They leak at the ankle, wear through at the heel, and "
                                "are awkward to fit in the dark."}}),
            ("a4", {"type": "criterion", "settings": {
                "label": "Waterproof socks + overshoes",
                "ours_value": "Genuinely cold, genuinely wet, genuinely long. The most "
                              "effective and most expensive combination.",
                "theirs_value": "Anything milder — you will overheat."}}),
        ])),
        ("block_order", ["a1", "a2", "a3", "a4"]),
    ])

    # ------------------------------------------------------------------- S8
    S["choosing"] = collections.OrderedDict([
        ("type", "content-columns"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("layout", "list"),
            ("numbered", True),
            ("anchor_id", "choosing"),
            ("eyebrow", "Choosing"),
            ("heading", "Four things worth checking."),
            ("lede", rich(
                "Whoever you end up buying from, these are the questions that separate "
                "a waterproof sock that works from one that has the word printed on "
                "the label."
            )),
            ("link_label", "Our size bands, in centimetres"),
            ("link_url", "/pages/size-guide"),
        ])),
        ("blocks", collections.OrderedDict([
            ("c1", {"type": "item", "settings": {
                "title": "Is the membrane named?",
                "body": rich(
                    "An unnamed “waterproof laminate” is a claim with nobody behind it. "
                    "A named membrane is one a third party has to stand behind. Ours is "
                    "Porelle®."
                )}}),
            ("c2", {"type": "item", "settings": {
                "title": "How many layers, and are they specified?",
                "body": rich(
                    "Three is the standard construction: lining, membrane, wear face. "
                    "If a listing does not say, it is usually because the answer is two."
                )}}),
            ("c3", {"type": "item", "settings": {
                "title": "Is the sock sized on the foot or on the shoe?",
                "body": rich(
                    "Shoe sizing is not consistent between brands. Foot length is. A "
                    "brand that publishes foot-length bands has thought about fit."
                )}}),
            ("c4", {"type": "item", "settings": {
                "title": "Does it say what it will not do?",
                "body": rich(
                    "This is the one that sorts the category. Every waterproof sock has "
                    "the same three limits. Very few sellers print them."
                )}}),
        ])),
        ("block_order", ["c1", "c2", "c3", "c4"]),
    ])

    # ------------------------------------------------------------------- S9
    S["buy"] = buy_widget()

    # ------------------------------------------------------------------- S10
    # Category-level questions. None of these appears on the homepage, the
    # product page or the FAQ page in this wording, and the page does not publish
    # FAQPage — the homepage holds that claim for the site.
    S["faq"] = collections.OrderedDict([
        ("type", "faq-accordion"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("anchor_id", "questions"),
            ("one_at_a_time", False),
            ("emit_schema", False),
            ("eyebrow", "Questions"),
            ("heading", "What people ask about the category."),
            ("lede", rich(
                "About waterproof socks generally, rather than about ours. Where the "
                "answer is “it depends”, it says what it depends on."
            )),
            ("help_prefix", "Something not here?"),
            ("help_label", "Phone or email us"),
            ("help_link", "/pages/contact"),
            ("cta_label", "Buy a pair"),
            ("cta_link", "#buy"),
            ("cta_note", "Two decisions and a quantity. No account needed."),
        ])),
        ("blocks", collections.OrderedDict()),
        ("block_order", []),
    ])

    QUESTIONS = [
        ("Do waterproof socks actually work?",
         "Yes, within limits worth knowing. A membrane sealed inside the knit stops "
         "liquid water reaching the foot, so you stay dry when a boot has wet out or a "
         "shoe is soaked. Water entering over the cuff, and sweat produced faster than "
         "the membrane can move it, are the two exceptions."),
        ("Are waterproof socks breathable?",
         "They are breathable, not ventilated. The membrane passes water vapour "
         "outwards, which delays the point at which the foot feels wet from the inside. "
         "On a hard, sustained effort you will out-produce it. That is thermodynamics, "
         "not a fault."),
        ("What is the difference between waterproof and water-resistant socks?",
         "A waterproof sock has a membrane and stops liquid water. A water-resistant "
         "sock has a treated or tightly knitted face that sheds light rain for a while "
         "and then wets through. If a product does not name a membrane, it is almost "
         "always the second kind."),
        ("Are waterproof socks warm?",
         "Warmer than an equivalent sock, because they block wind and stop evaporative "
         "cooling, but they are not insulated. Waterproofing and warmth are separate "
         "properties and worth choosing separately."),
        # The brief's wording, restored at the client's instruction pending their
        # confirmation. It states a wash temperature, which the client's own care
        # document does not address — the Care & Washing page and the FAQ page now
        # say the same thing, so at least the site is consistent while that is
        # being checked.
        ("Can you wear waterproof socks every day?",
         "Yes. Wash them cool between wears and let them air dry — a membrane dies of "
         "heat and softener long before it wears out. Most people who wear them daily "
         "keep three or more pairs so a dry pair is always ready."),
        ("How long do waterproof socks last?",
         "It depends almost entirely on abrasion and how they are washed, not on how "
         "many times they are worn. Heat, fabric softener and tumble drying end a "
         "membrane far faster than use does."),
        ("Are waterproof socks worth it?",
         "If your feet get wet on a recurring schedule — a job, a commute, a weekly "
         "walk, daily wudu — then yes, because the problem repeats. For one wet holiday "
         "a year, probably not."),
        ("What are the best waterproof socks in the UK?",
         "Judge them on four checkable things: whether the membrane is named, whether "
         "the layer count is published, whether sizing is measurement-led, and whether "
         "the seller states the limits. Most listings fail at least two."),
    ]
    for i, (q, a) in enumerate(QUESTIONS, 1):
        key = f"q{i}"
        S["faq"]["blocks"][key] = {"type": "question", "settings": {
            "question": q, "answer": rich(a)}}
        S["faq"]["block_order"].append(key)

    order = ["crumb", "hero", "definition", "mechanism", "limits",
             "byuse", "alternatives", "choosing", "buy", "faq"]
    missing = [k for k in order if k not in S]
    extra = [k for k in S if k not in order]
    if missing or extra:
        sys.exit(f"order mismatch — missing {missing}, orphaned {extra}")

    out = collections.OrderedDict([("sections", S), ("order", order)])
    TPL.write_text(HEADER + json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    words = len(re.findall(r"[A-Za-z']+", re.sub(r"<[^>]+>", " ", json.dumps(out))))
    print(f"  wrote {TPL.relative_to(ROOT)}")
    print(f"  {len(order)} sections, {len(QUESTIONS)} questions, ~{words} words of copy")
    print(f"  order: {' -> '.join(order)}")


if __name__ == "__main__":
    main()
