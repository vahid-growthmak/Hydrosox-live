#!/usr/bin/env python3
"""Applies the Phase 5A/5B content to the Technology, FAQ and support pages.

The Masah page is NOT here. It is composed by scripts/apply-masah-content.py
and held until a scholar signs it off — see that file.

One rule governs every placeholder in the brief. Where a fact is missing, the
brief's own instruction (set on the Running page's weight figure) is to cut the
line rather than substitute an adjective. A literal "[CLIENT TO CONFIRM]" must
never reach the page: it would be rendered to a reader and, worse, ingested
verbatim by a language model. So each one is handled explicitly below —
either an honest interim answer in the site's own voice, or the question is
left out until the fact arrives:

  * Country of manufacture — answered honestly rather than omitted. The brief
    is right that an unanswered question here gets guessed at, and a confident
    wrong guess is very hard to correct afterwards. Saying "we have not
    published it yet, and here is why" forecloses the guess without inventing
    a country.
  * Amazon listing — omitted. We do not know whether it is live, and unlike the
    above there is no honest interim form: any answer asserts a commercial fact.
  * Product lifespan — answered in the shape the page already uses for test
    figures ("we do not publish one yet"), which is consistent and true.
  * Partner arrangements — the partners stay named and the framing stays, but
    no arrangement is described, because none has been evidenced.

Idempotent: running it twice changes nothing the second time.
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


def item(title, body, link=None):
    st = collections.OrderedDict([("title", title), ("body", rich(body))])
    if link:
        st["link_label"], st["link_url"] = link
    return collections.OrderedDict([("type", "item"), ("settings", st)])


def cols(anchor, eyebrow, heading, lede, entries, numbered=False,
         scheme="paper", link=None, footnote=None):
    blocks, order = collections.OrderedDict(), []
    for n, entry in enumerate(entries, 1):
        k = "i%d" % n
        blocks[k] = item(*entry) if len(entry) > 2 else item(entry[0], entry[1])
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


def faq(anchor, eyebrow, heading, lede, questions, emit=False):
    blocks, order = collections.OrderedDict(), []
    for n, (q, a) in enumerate(questions, 1):
        k = "q%d" % n
        blocks[k] = collections.OrderedDict([
            ("type", "question"),
            ("settings", collections.OrderedDict([
                ("question", q), ("answer", rich(a))]))])
        order.append(k)
    st = collections.OrderedDict([
        ("color_scheme", "paper"), ("anchor_id", anchor),
        ("one_at_a_time", False), ("emit_schema", emit),
        ("eyebrow", eyebrow), ("heading", heading)])
    if lede:
        st["lede"] = rich(lede)
    return collections.OrderedDict([
        ("type", "faq-accordion"), ("settings", st),
        ("blocks", blocks), ("block_order", order)])


def load_index():
    raw = (TPL / "index.json").read_text()
    return json.loads(raw[_lead_comments(raw):],
                      object_pairs_hook=collections.OrderedDict)


# ===========================================================================
def technology():
    header, d = read("page.technology.json")
    S = d["sections"]

    # The membrane section gains the paragraph that explains *why* the trick
    # works. A page called "the mechanism, not the claim" that never states the
    # mechanism is only asserting a different thing.
    # All three paragraphs live in `prose`, and ONLY there. The section once
    # carried them in `lede` while an older `prose` value survived underneath
    # — the layout renders lede above the prose branch, so the page showed
    # the same paragraphs twice (client screenshot, 2026-08-07). The lede is
    # cleared explicitly so the duplicate can never return, and the lead
    # treatment sets the opening claim in the pale-blue panel — the client's
    # asked-for box against the wall-of-text read.
    # v4 (Document 3, 8 Aug 2026). The PFOA claim is removed site-wide by
    # that document's red block — it appears in none of the client's own
    # documents; it returns only if evidenced in writing.
    S["intro"]["settings"].update({
        "eyebrow": "The technology",
        "heading": "How waterproof socks work",
        "body": rich(
            "“Waterproof” is a word anyone can print on a label. This "
            "is what’s underneath ours, so you can judge it rather than "
            "take our word for it."),
    })
    S["membrane"]["settings"]["eyebrow"] = "The waterproof layer"
    S["membrane"]["settings"]["heading"] = "Porelle® isn’t a name we made up"
    S["membrane"]["settings"]["lede"] = ""
    S["membrane"]["settings"]["lead_first_para"] = True
    S["membrane"]["settings"]["prose"] = rich(
        "The waterproof layer is Porelle®, made by a separate company. That "
        "matters more than it sounds: a named layer is one someone else has "
        "to stand behind, and you can go and look them up. Water can’t "
        "get through it. Sweat, as vapour, can.",
        "Brands that don’t name their waterproof layer are asking you to "
        "trust an unnamed one. We’d rather you checked ours.",
        "The principle isn’t new and isn’t ours. A waterproof "
        "breathable layer works because liquid water and water vapour are "
        "very different sizes. The holes are far too small for a droplet to "
        "pass through and comfortably big for a vapour molecule. That "
        "difference is the whole technology, and it’s been in outdoor "
        "clothing for decades.")

    # The construction section becomes the homepage's scroll-scrub — the
    # reader takes the sock apart with their own scrolling, which is the one
    # treatment where the section demonstrates the thing it describes. Copied
    # wholesale from index.json so the layer text and the frames can never
    # drift between the two pages; the three layer bodies there are already
    # word-identical to what this page carried as a list. The heading stays
    # this page's own, and the eyebrow becomes "The construction" — it said
    # "The problem", the same copy-paste error the wudu brief documents, and
    # the client's mockup shows the corrected label.
    idx = load_index()
    layers = json.loads(json.dumps(idx["sections"]["construction"]),
                        object_pairs_hook=collections.OrderedDict)
    layers["settings"].update({
        "anchor_id": "construction",
        # v4: this page's layer copy DIVERGES from the homepage's on purpose
        # now — the document writes each page its own sentences ("no sentence
        # appears on two pages"), so the single-source copy carries this
        # page's own text below. The frames and the scrub stay shared.
        "eyebrow": "The build",
        "heading": "Why there are three layers",
        "lede": (
            "<p>One waterproof layer on its own would be uncomfortable and "
            "wouldn’t last. The other two exist to make it wearable.</p>"
            "<p>The layer doing the waterproofing is the one you never touch. "
            "That’s deliberate — a waterproof layer exposed to rubbing "
            "is a waterproof layer with a short life.</p>"),
        # A shorter track than the homepage's: this page has more below it.
        "track_height": 220,
        # Wash, as the mockup sets this section on this page (the homepage
        # copy stays paper). Safe for the frames: the sequence draws inside
        # the stage's own rounded --plate panel, so the section ground never
        # touches the imagery.
        "color_scheme": "wash",
    })
    for bk, (heading, role, body) in {
        "y1": ("Inner layer", "Against your skin",
               "<p>A soft knitted lining that moves sweat off your foot and "
               "keeps the waterproof layer from sitting directly against you. "
               "Without it a waterproof sock feels like a carrier bag, and "
               "the layer wears out against your foot instead of against the "
               "shoe.</p>"),
        "y2": ("Middle layer", "The waterproof one",
               "<p>The Porelle® membrane. Water can’t get in. Sweat can "
               "get out. It’s sealed between the other two and never "
               "forms the outside of the sock.</p>"),
        "y3": ("Outer layer", "The wear surface",
               "<p>The knitted face that takes the rubbing inside a boot or "
               "shoe. It’s also what holds the sock’s shape when "
               "you’re not wearing it, which matters for how long it "
               "lasts and, separately, for masah.</p>"),
    }.items():
        if bk in layers["blocks"]:
            layers["blocks"][bk]["settings"].update({
                "heading": heading, "role": role, "body": body})
    # The homepage section ends with a link block pointing at this very page;
    # a self-link is dropped, everything else is kept.
    keep = collections.OrderedDict()
    for bk in (layers.get("block_order") or []):
        b = layers["blocks"][bk]
        if b.get("type") == "link" and "/pages/technology" in str(b.get("settings", {})):
            continue
        keep[bk] = b
    layers["blocks"] = keep
    layers["block_order"] = list(keep)
    S["layers"] = layers

    # The sweat objection decides more sales than any other, and every
    # competitor page in the mapped set either ignores it or overclaims.
    S["breathability"] = cols(
        "breathability", "Breathability",
        "Breathable doesn’t mean dry",
        "This is where most waterproof sock pages go vague. It’s also "
        "the question nearly everyone actually has, so here’s the "
        "mechanism and the limit.",
        [("Breathability is a rate, not a state",
          "The layer moves sweat outwards at a certain speed. It "
          "doesn’t remove moisture and it doesn’t make a sock "
          "ventilated."),
         ("Where the limit is",
          "Your foot produces sweat at a rate that depends on effort and "
          "temperature. Produce it faster than the layer can move it and the "
          "surplus stays inside. That isn’t a fault, it’s "
          "arithmetic."),
         ("When you’ll notice",
          "Walking pace in British weather is comfortably within it. A steep "
          "climb in mild air, a hard run, or summer rain will exceed it. "
          "Cold air helps, because the difference in humidity across the "
          "layer is what drives it out."),
         ("What actually helps",
          "A sock that fits, footwear that isn’t sealed shut, and "
          "taking them off at the end of the day. No waterproof layer "
          "changes the fact that a foot in a boot for ten hours is in a "
          "humid place.")],
        scheme="wash",
        link=("When these are the wrong sock", "/pages/running-and-trail"))

    # Teaching the reader how to interrogate our competitors, on the one page
    # where we have no figure to give. That is what earns a citation: the page
    # becomes useful to someone who is not going to buy anything.
    # centre-note's footnote is richtext and content-columns' is a textarea.
    # Shopify refuses a bare string in a richtext setting on upload, and the
    # template it refuses is the one that stops updating — so the two are not
    # interchangeable even though they look it.
    S["testing"]["settings"].update({
        "eyebrow": "Testing",
        "heading": "We don’t publish test figures yet",
        "body": rich(
            "Independent test data is the only kind worth printing and we "
            "don’t have it yet. Rather than quote a waterproof rating or "
            "a breathability number we can’t stand behind, we’ve "
            "left this section empty until we can."),
        "footnote": rich(
            "For what it’s worth, the two numbers to ask any brand in "
            "this category for are hydrostatic head — how much water "
            "pressure a fabric holds back before it leaks — and a "
            "breathability rating, usually given as grams of vapour passed "
            "per square metre in twenty-four hours."),
    })

    S["failure"] = cols(
        "failure", "What ends it", "Four ways a waterproof layer dies",
        "A waterproof sock almost never fails from age. It fails from one of "
        "these, and three are avoidable.",
        [("Heat",
          "A tumble dryer, an iron, or a radiator. Direct heat is the "
          "fastest way to finish one off and the most common. Air dry, "
          "always."),
         ("Fabric softener",
          "Softener coats the holes the layer breathes through. The sock "
          "still keeps water out and stops letting sweat out, which is the "
          "worst of both."),
         ("Rubbing",
          "The outer knit takes this, which is why there are three layers. "
          "But a sock worn in a boot with a rough interior, or over months "
          "on site, will eventually wear through."),
         ("A hole",
          "A toenail, a thorn, or a sharp stone inside a boot. Once "
          "it’s pierced the waterproofing is gone and can’t be "
          "restored. No spray or reproofing treatment brings a waterproof "
          "layer back.")],
        link=("How to wash them properly", "/pages/care-and-washing"))

    S["faq"] = faq(
        "questions", "Questions", "Common questions",
        None,
        [("How do waterproof socks work?",
          "A thin waterproof layer is sealed between two knitted layers. Its "
          "holes are too small for liquid water to pass through and big "
          "enough for water vapour to escape, so rain and puddle water stay "
          "out while sweat can move away from your foot."),
         ("What is a waterproof breathable membrane?",
          "A thin sheet that blocks liquid water one way while letting water "
          "vapour through the other. It works because a water droplet is far "
          "bigger than a vapour molecule. HydroSox uses Porelle®, made by a "
          "separate company."),
         ("Why do waterproof socks need three layers?",
          "Because the waterproof layer needs protecting on both sides. The "
          "inner knit keeps it off your skin and moves sweat towards it. The "
          "outer knit takes the rubbing inside a boot. A waterproof layer "
          "used as the wear surface wouldn’t last a season."),
         ("Can waterproof socks be reproofed?",
          "No. Reproofing works on a water-repellent finish applied to a "
          "fabric surface. It can’t repair a waterproof layer. Once one "
          "is pierced or worn through, the waterproofing is gone for good."),
         ("What is hydrostatic head?",
          "The standard measure of how much water pressure a fabric holds "
          "back before water passes through, given in millimetres. It’s "
          "the number worth asking any waterproof brand for. We don’t "
          "publish one yet because we don’t have independent test "
          "data."),
         ("Do all waterproof socks use the same membrane?",
          "No, and many don’t say what they use at all. Some use a "
          "named third-party layer, some use an unnamed one, and some are "
          "just a tightly knitted or treated sock with no waterproof layer "
          "in it. If a listing doesn’t name one, that’s usually "
          "why.")],
        emit=True)

    # The activity strip goes: the brief's section list for this page runs
    # opening → membrane → layers → breathability → testing → failure →
    # questions, and the use-case argument belongs to the pages that own it.
    for dead in ("activities", "wont"):
        S.pop(dead, None)
    # Presentation, to the client's mockup: breathability as the mockup's
    # ruled stacked rows on paper (title over body, sticky heading left —
    # checked against the live mockup DOM, which sets a dl of stacked rows,
    # not term-beside-definition), the test-figures note on the blue
    # stating-a-limit band. Failure: back to the mockup's paper band of
    # outlined cards — the client asked for the dark numbered rows on
    # 2026-08-07 and reversed it the same day after seeing both ("any box"),
    # attaching the mockup's cards as the target. Same four rows, same words.
    S["breathability"]["settings"].update({
        "layout": "list", "color_scheme": "paper"})
    S["testing"]["settings"]["color_scheme"] = "blue"
    S["failure"]["settings"].update({
        "layout": "band", "color_scheme": "paper", "numbered": False})

    # The closing band the mockup adds, words from the mockup verbatim.
    S["close"] = collections.OrderedDict([
        ("type", "closing-cta"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "ink"),
            ("anchor_id", "close"),
            ("eyebrow", "The product"),
            ("heading", "The mechanism is the argument. This is the sock."),
            ("cta_label", "Buy a pair"),
            ("cta_url", "#buy"),
            ("alt_label", "How to wash them"),
            ("alt_url", "/pages/care-and-washing"),
        ])),
    ])

    d["order"] = ["crumb", "intro", "membrane", "layers", "breathability",
                  "testing", "failure", "faq", "buy", "close"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("technology: orphaned %s" % orphans)
    write("page.technology.json", header, d)
    return "technology", len(d["order"])


# ===========================================================================
def faq_page():
    header, d = read("page.faq.json")
    S = d["sections"]

    groups = [
        ("product", "The product", "What the sock actually is.", [
            ("Can water get in over the top of the sock?",
             "Yes. A sock is open at the cuff, so water deeper than the cuff "
             "will go in, exactly as it would with any sock. No waterproof "
             "sock behaves otherwise, and any brand implying it does is "
             "overstating."),
            # The snow question moved to the category hub verbatim in the v4
            # content (8 Aug 2026), and the site rule is one page per
            # question. Removed here rather than reworded — the FAQ page's
            # own v4 document decides what replaces it.
            ("Can I wear them for swimming, or in the shower?",
             "They are not designed for immersion. They are built for water "
             "arriving from outside during normal use — rain, spray, puddles, "
             "wet ground — not for being submerged, and we would rather say so "
             "than take the sale."),
            ("Will they start to smell?",
             "They are no more prone to it than any sock, provided they are "
             "washed and air dried between wears rather than left damp in a "
             "bag. A membrane does not cause odour; a wet sock left in a boot "
             "overnight does."),
            ("Do they stretch out over time?",
             "They loosen slightly with wear, as knitted socks do. The shaped "
             "fit is built to hold longer than a standard sock because it is "
             "structural rather than decorative — it is also the property that "
             "matters for masah."),
            ("Can I wear them without shoes?",
             "Around the house, yes. But the outer knit is the wear surface, "
             "and walking on hard floors or outside without footwear abrades "
             "it far faster than a boot does. It is the quickest way to "
             "shorten their life."),
        ]),
        ("wudu", "Wudu and masah", "The everyday questions.", [
            ("Do I need to wash my feet before putting them on?",
             "Yes. The sources are consistent that the footwear must be put on "
             "after a complete wudu in which the feet were washed. Masah "
             "applies from the next wudu onwards, not from the one during "
             "which you put them on."),
            ("Can I wear them for Hajj or Umrah?",
             "Many people buy them for pilgrimage travel, where facilities are "
             "shared and there is little chance to dry anything. On the "
             "separate question of footwear restrictions in ihram, ask a "
             "scholar — that is not a question we should be answering."),
            ("Can children use them for wudu?",
             "Our sizes start at UK 3, so they fit older children. On whether "
             "and from what age masah applies for a child, ask a scholar "
             "rather than a sock company."),
            ("What happens if water gets inside them during wudu?",
             "This is addressed in the sources and it is a point we have "
             "deliberately not paraphrased, because it matters and because "
             "getting it approximately right is worse than not answering. The "
             "masah page carries the reviewed wording."),
            ("Are these suitable for use at the mosque?",
             "There is no reason they would not be. The practical reason "
             "people buy them is the places where wudu is harder — offices, "
             "sites, airports, universities — rather than a mosque with proper "
             "facilities."),
            ("Do you sell a separate wudu version?",
             "No. It is the same sock, the same membrane and the same "
             "construction whichever page you buy it from, at the same price. "
             "There is no wudu edition and no wudu premium."),
        ]),
        ("sizing", "Sizing and fit", "The bands are on the size guide.", [
            ("How do I measure my foot?",
             "Stand on a sheet of paper with your heel against a wall, mark "
             "the tip of your longest toe, and measure from the wall to the "
             "mark. That figure in centimetres is what the size bands are set "
             "by, and it is more reliable than your shoe size."),
            ("What if I am larger than UK 14?",
             "We do not currently make a size above XL, which covers UK 12–14. "
             "We would rather tell you that plainly than sell you something "
             "that will not fit."),
            ("Do they fit wide feet?",
             "They are a close, stretchy fit rather than a loose one. If you "
             "normally need a wide fitting in shoes, take the larger band — a "
             "sock that grips across the width is uncomfortable over a full "
             "day and shortens the life of the membrane."),
            ("Will they slip down?",
             "They are shaped to stay in place through normal wear rather than "
             "working loose over a day. If a pair does slip, it is usually a "
             "size too large, which is worth checking against the foot-length "
             "bands."),
            ("Can I wear another sock underneath?",
             "You can, but there is usually no need — the inner knit is "
             "designed to sit against the skin. Adding a liner underneath adds "
             "bulk, which matters most in cycling shoes and safety boots where "
             "there is least room."),
        ]),
        ("care", "Washing and lifespan", "The full instructions are on the "
         "care page.", [
            ("How do I dry them quickly?",
             "You cannot, safely. Turn them inside out and air dry at room "
             "temperature with air moving around them. Never on a radiator and "
             "never in a tumble dryer — direct heat is the single most common "
             "way a waterproof sock dies."),
            ("Can I wash them with the rest of my washing?",
             "Yes, on a cool cycle, provided there is no fabric softener in "
             "the load and nothing abrasive like zips or Velcro. Softener is "
             "the problem more often than temperature is."),
            ("What temperature should I wash them at?",
             "Cool, on a gentle cycle. The membrane is a laminate, and heat is "
             "what breaks laminates down."),
            ("How do I get mud off them?",
             "Rinse under a cold tap first to get the grit out, then wash "
             "cool. Grit left in the knit is abrasive against the membrane "
             "from the inside, which matters more than the mud does."),
            ("Are they still waterproof once they have been punctured?",
             "No, and it cannot be repaired. A membrane is a continuous "
             "barrier — once it is pierced by a toenail, a thorn or a stone, "
             "the water goes through and no spray or reproofing treatment will "
             "bring it back."),
        ]),
        ("delivery", "Delivery, returns and warranty", "What is settled, and "
         "what is not.", [
            ("Where do you deliver to?",
             "The United Kingdom, from a UK warehouse. Delivery is free on two "
             "pairs or more; on a single pair it is charged at checkout and "
             "shown before you pay."),
            ("Do you deliver outside the UK?",
             "This is still being confirmed and we will not promise a service "
             "we cannot yet support. If you are outside the UK, email us and "
             "we will tell you honestly where things stand."),
            ("Can I return them if I have worn them?",
             "Returns are for unworn socks in the original packaging with the "
             "seal intact — you may inspect them as you would in a shop. If a "
             "pair is faulty, that is a different matter entirely and worn or "
             "not makes no difference."),
            ("What if my order does not arrive?",
             "Email or phone us with the order number and we will chase it "
             "with the courier. Until the parcel is with you, the "
             "responsibility for getting it there is ours."),
            ("Can I change or cancel an order?",
             "If it has not been dispatched, yes — email or phone us straight "
             "away. After dispatch it becomes a return, and you have fourteen "
             "days from the day the parcel arrives to tell us you are "
             "cancelling."),
            ("Do you offer exchanges?",
             "If a size is wrong, the simplest route is to return the unworn "
             "pair and order the right one. Contact us before sending anything "
             "back and we will tell you exactly what to do."),
        ]),
        ("company", "The company", "Who is behind this.", [
            # Answered rather than omitted: an unanswered manufacturing
            # question is one an assistant will fill in for us.
            ("Where are HydroSox made?",
             "We have not published a country of manufacture yet, and we are "
             "not going to print one we have not confirmed with the "
             "manufacturer. It is a fair question, it will be answered here "
             "plainly when we can evidence it, and in the meantime what we can "
             "say is that HydroSox is a UK registered company shipping from a "
             "UK warehouse."),
            ("Do you sell to shops, or wholesale?",
             "Yes. There is no public trade pricing and no automated tiering — "
             "tell us what you sell and to whom on the trade page, and we will "
             "reply with terms that fit."),
            ("How can I pay?",
             "Visa, Mastercard, American Express, Apple Pay, Google Pay and "
             "Shop Pay. Checkout is guest by default, so no account is needed. "
             "We never see or store your full card details."),
            ("Is there a shop I can visit?",
             "No. HydroSox is online only, from a UK warehouse. The registered "
             "address and phone number are on every page of this site rather "
             "than behind a contact form, so there is always a person to "
             "reach."),
        ]),
    ]

    for old in ("product", "wudu", "sizing", "care", "delivery", "returns",
                "company"):
        S.pop(old, None)
    total = 0
    for key, eyebrow, heading, qs in groups:
        S[key] = faq(key, eyebrow, heading, None, qs, emit=False)
        total += len(qs)

    # The jump grid has to match the groups it jumps to.
    tiles, tile_order = collections.OrderedDict(), []
    for n, (key, eyebrow, heading, qs) in enumerate(groups, 1):
        k = "g%d" % n
        tiles[k] = collections.OrderedDict([
            ("type", "card"),
            ("settings", collections.OrderedDict([
                ("title", eyebrow), ("body", heading),
                ("meta", "%d questions" % len(qs)), ("link", "#%s" % key)]))])
        tile_order.append(k)
    S["groups"]["blocks"] = tiles
    S["groups"]["block_order"] = tile_order
    S["groups"]["settings"]["heading"] = "Six groups."
    S["groups"]["settings"]["columns"] = 3

    d["order"] = (["intro", "groups"] + [g[0] for g in groups]
                  + ["still", "buy"])
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("faq: orphaned %s" % orphans)
    write("page.faq.json", header, d)
    return "faq", total


# ===========================================================================
def size_guide():
    header, d = read("page.size-guide.json")
    S = d["sections"]

    # The four bands as the mockup's real table (client, 2026-08-07: "you can
    # add as section please") — Band, Foot length, UK, EU, US as columns, one
    # row per band, every cell verbatim from the mockup's own markup. The same
    # figures the buy widget's overlay carries; the EU/US conversions serve
    # "sock size conversion uk eu us" demand from international visitors.
    band_rows = [
        ("S", "22.0 - 24.0 cm", "UK 3-5", "EU 36-38", "US 4-6"),
        ("M", "24.5 - 26.5 cm", "UK 6-8", "EU 39-42", "US 6.5-9"),
        ("L", "27.0 - 29.0 cm", "UK 9-11", "EU 43-46", "US 9.5-12"),
        ("XL", "29.5 - 32.0 cm", "UK 12-14", "EU 47-49", "US 12.5-14.5"),
    ]
    chart_blocks, chart_order = collections.OrderedDict(), []
    for n, cells in enumerate(band_rows, 1):
        k = "b%d" % n
        chart_blocks[k] = collections.OrderedDict([
            ("type", "row"),
            ("settings", collections.OrderedDict(
                ("cell%d" % i, cell) for i, cell in enumerate(cells, 1))),
        ])
        chart_order.append(k)
    S["chart"] = collections.OrderedDict([
        ("type", "data-table"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("anchor_id", "bands"),
            ("eyebrow", "The four bands"),
            ("heading", "The four bands"),
            ("head_note", rich(
                "The same measurements appear in the size guide that opens "
                "over the buy widget. They are read from one place, so the "
                "two cannot disagree.")),
            ("col1", "Band"),
            ("col2", "Foot length"),
            ("col3", "UK"),
            ("col4", "EU"),
            ("col5", "US"),
        ])),
        ("blocks", chart_blocks),
        ("block_order", chart_order),
    ])

    S["howto"] = cols(
        "measuring", "Measuring and choosing", "Measuring and choosing", None,
        [("How to measure",
          "Stand on a sheet of paper with your heel against a wall, mark the "
          "tip of your longest toe, and measure from the wall to the mark. Do "
          "it in the afternoon — feet are slightly larger later in the day."),
         ("Between two sizes",
          "Take the larger one. These are a close, stretchy fit, and a size "
          "down grips the toes and shortens the life of the membrane."),
         ("Measure both feet",
          "Most people have one foot slightly larger than the other. Size to "
          "the larger one. It is a small thing and it is the reason a lot of "
          "socks feel right on one foot and tight on the other."),
         ("Inside boots and cycling shoes",
          "They sit at roughly the bulk of a mid-weight sock. Snug walking "
          "boots and race-fit cycling shoes are where that matters — the "
          "use-case pages cover each in more detail.")],
        scheme="wash")

    S["faq"] = faq(
        "questions", "Questions", "Before you choose a band.", None,
        [("What if I am between two size bands?",
          "Take the larger. A sock that grips across the toes is uncomfortable "
          "over a full day and puts constant tension on the membrane, which "
          "shortens its life. The fit is stretchy enough that the larger band "
          "will not feel loose."),
         ("Are the sizes unisex?",
          "Yes. One range from UK 3 to UK 14, sized on foot length rather than "
          "on a men's or women's scale. Take the band your measurement falls "
          "into and ignore the label you are used to."),
         ("Do they fit the same as my normal socks?",
          "Closer. They are shaped and structural rather than loose-knit, so "
          "they feel more fitted than a standard sock at the same nominal "
          "size. That is deliberate and it is what keeps them in place."),
         ("What if I order the wrong size?",
          "Return the unworn pair within fourteen days and order the right "
          "one. Contact us first and we will tell you exactly what to do — it "
          "is quicker than guessing.")],
        emit=True)

    # Presentation. The chart is built above as the data-table; measuring
    # runs as the band
    # of four paper cards on wash, pinned two across as the mockup sets them.
    S["howto"]["settings"].update({
        "layout": "band", "color_scheme": "wash", "card_columns": "two"})

    # The closing band the mockup adds, words from the mockup verbatim.
    S["close"] = collections.OrderedDict([
        ("type", "closing-cta"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "ink"),
            ("anchor_id", "close"),
            ("eyebrow", "The product"),
            ("heading", "Measured, and ready to order."),
            ("cta_label", "Buy a pair"),
            ("cta_url", "#buy"),
            ("alt_label", "Care and washing"),
            ("alt_url", "/pages/care-and-washing"),
        ])),
    ])

    d["order"] = ["intro", "chart", "howto", "faq", "buy", "close"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("size-guide: orphaned %s" % orphans)
    write("page.size-guide.json", header, d)
    return "size-guide", len(d["order"])


# ===========================================================================
def care():
    header, d = read("page.care-and-washing.json")
    S = d["sections"]

    S["wash"] = cols(
        "washing", "Washing instructions", "Washing instructions", None,
        [("Wash cool",
          "A laminate fails from heat long before it fails from age. Cool "
          "wash, gentle cycle."),
         ("Turn them inside out",
          "It puts the knit face, not the lining, against the drum."),
         ("No fabric softener",
          "Softener coats the pores the membrane breathes through. Once they "
          "are clogged the sock still keeps water out, but it stops moving "
          "vapour — which is the worst of both."),
         ("No bleach", "It attacks the laminate, not just the colour."),
         ("Air dry",
          "Away from a radiator. A membrane does not need heat to dry, and "
          "heat is the thing most likely to end it."),
         ("Never tumble dry or iron", "Both are heat, applied directly."),
         ("Rinse the grit out first",
          "After a muddy walk or a wet ride, rinse under a cold tap before "
          "washing. Fine grit trapped in the knit is abrasive against the "
          "membrane from the inside, and it does more damage than the mud "
          "does.")],
        numbered=False)

    S["damage"] = cols(
        "damage", "What damages the membrane", "What damages the membrane",
        None,
        [("They are not indestructible",
          "A membrane is a membrane. Abrasion, toenails and the wrong wash "
          "cycle will eventually end one."),
         ("Breathable does not mean dry inside",
          "Work hard enough and you will sweat faster than any membrane can "
          "move vapour. Breathability slows that. It does not repeal it."),
         ("Keep your toenails short",
          "The least glamorous advice on this site and one of the most useful. "
          "A long toenail inside a close-fitting sock is a puncture waiting to "
          "happen, and a punctured membrane cannot be repaired."),
         ("Do not leave them damp in a bag",
          "A wet sock left in a kit bag or a boot overnight is where odour "
          "starts, and prolonged damp does the knit no good either. Air dry "
          "them the same day.")],
        scheme="wash")

    # A page that only says how to look after them is half a page. This is the
    # half that keeps a customer whose pair appears to have failed.
    S["failing"] = cols(
        "if-it-changes", "If something changes",
        "If a pair stops keeping water out.",
        "There are three usual explanations, and they need different "
        "responses.",
        [("Water came in over the cuff",
          "The most common one, and not a fault. If the water was deeper than "
          "the sock is tall, it went in the top. Nothing is wrong with the "
          "sock."),
         ("The membrane is clogged rather than failed",
          "If they feel clammy but still keep water out, that is usually "
          "fabric softener build-up. A cool wash with no detergent residue "
          "sometimes recovers it. Sometimes it does not."),
         ("The membrane is punctured",
          "If water comes through the body of the sock, the laminate has been "
          "pierced. That cannot be repaired or reproofed. If it happened "
          "within the first weeks of normal use, that is a fault and we want "
          "to hear about it.")],
        link=("Where you stand if it is a fault", "/pages/warranty"))

    S["faq"] = faq(
        "questions", "Questions", "About washing them.", None,
        [("How often should I wash them?",
          "After every wet or muddy outing, and otherwise as often as you "
          "would wash any sock. Washing them correctly does no harm; leaving "
          "grit and sweat in them does."),
         ("Can I wash them by hand?",
          "Yes, and for a single muddy pair it is often quicker. Cool water, a "
          "little detergent, no softener, rinse thoroughly and air dry."),
         ("What detergent should I use?",
          "An ordinary liquid detergent is fine. Avoid anything marketed as a "
          "softening or conditioning detergent, and avoid biological powders "
          "left undissolved against the fabric."),
         ("Can I put them on a radiator to dry?",
          "No. Direct heat is the fastest way to end a laminate, and a "
          "radiator is the most common culprit precisely because it is the "
          "most tempting after a wet day."),
         # Answered in the shape this site already uses for test figures.
         ("How long should a pair last?",
          "We do not publish a figure yet, because we do not have one we could "
          "stand behind. What we can tell you is what decides it: abrasion "
          "inside footwear, and heat or softener in the wash. Those end a "
          "membrane far sooner than elapsed time does, and three of the four "
          "are in your control.")],
        emit=True)

    # Presentation: the seven wash steps on the numbered rail, the damage
    # list as cards, the what-changed triage as the dark emphasis band, and
    # the no-figure statement on the blue stating-a-limit scheme.
    # Presentation, to the client's mockup DOM (2026-08-07): the wash steps as
    # plain stacked rows under the sticky heading — the mockup numbers nothing
    # here; the damage list as the 2 × 2 band of paper cards on wash; and the
    # three what-changed cases as light divided columns under a band header,
    # replacing the dark focus treatment. Words untouched throughout.
    S["wash"]["settings"].update({
        "layout": "list", "color_scheme": "paper", "numbered": False})
    S["damage"]["settings"].update({
        "layout": "band", "color_scheme": "wash", "card_columns": "two"})
    S["failing"]["settings"].update({
        "layout": "band", "color_scheme": "paper", "mirror": False,
        "divided": True})
    S["life"]["settings"]["color_scheme"] = "blue"
    # The closing "Worn one out?" note goes dark, per the client (2026-08-07)
    # and the mockup — the page hands off into the dark footer from ink.
    S["tail"]["settings"]["color_scheme"] = "ink"

    d["order"] = ["intro", "wash", "damage", "failing", "life", "faq", "tail"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("care: orphaned %s" % orphans)
    write("page.care-and-washing.json", header, d)
    return "care-and-washing", len(d["order"])


# ===========================================================================
def about():
    header, d = read("page.about.json")
    S = d["sections"]

    S["what"] = cols(
        "what", "What there is to say", "What there is to say", None,
        [("What we sell",
          "A waterproof sock with a licensed Porelle® membrane sealed inside a "
          "three-layer knit, in four colourways and four sizes, at one price "
          "that does not change depending on how you arrived."),
         ("How we talk about it",
          "Every claim on this site is either checkable or absent. We publish "
          "what the product will not do on the homepage, which is the half "
          "most brands leave out."),
         ("Where we are",
          "A UK registered company with a UK warehouse. The address and phone "
          "number are on every page."),
         # Answers the question a sceptical reader has before the first
         # paragraph is finished: if the membrane is comparable, why half the
         # price? Left unanswered it reads as a reason to distrust the rest.
         ("What it costs and why",
          "Twenty pounds a pair, against thirty to fifty for the established "
          "performance brands. That is not a lower-quality membrane; it is one "
          "product sold direct, with no retail markup and no thirty-item "
          "accessory range to fund.")])

    S["gap"] = cols(
        "missing", "What is missing",
        "What is missing, and why we are saying so", None,
        [("Who is behind it",
          "No founder or team is named on this site yet. That is a real gap, "
          "not a stylistic choice, and it will be filled with named people "
          "rather than a stock photograph and a mission statement."),
         ("How the product was developed",
          "Not written yet. When it is, it will not carry invented timelines "
          "or test counts."),
         ("Independent test data",
          "We publish no hydrostatic head or breathability figure, because we "
          "do not have independently tested ones. The technology page explains "
          "what those numbers mean and why we would rather have none than an "
          "unverified one.")],
        scheme="wash")

    # Named, with no arrangement described — neither has been evidenced, and an
    # unspecified "partnership" reads as marketing to exactly the reader it is
    # meant to impress.
    S["support"] = collections.OrderedDict([
        ("type", "centre-note"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("anchor_id", "beyond-the-product"),
            ("eyebrow", "Beyond the product"),
            ("heading", "Two partnerships, and no logo wall."),
            ("body", rich(
                "HydroSox works with The Fair Group, supporting mental health "
                "innovation and neuro-diagnostic services, and with Humanity "
                "Welfare Trust, which delivers humanitarian aid projects. The "
                "detail of each arrangement is published on the partners page "
                "once it can be evidenced rather than asserted.")),
            ("link_label", "What each partnership actually involves"),
            ("link_url", "/pages/our-partners"),
        ])),
    ])

    # Presentation, to the mockup DOM (2026-08-07): the four say-cards as an
    # outlined row under the heading — bordered paper cards, four across on a
    # desktop — and the three gaps as divided columns on wash. Words untouched.
    S["what"]["settings"].update({
        "layout": "band", "color_scheme": "paper", "outlined": True})
    S["gap"]["settings"].update({
        "layout": "band", "color_scheme": "wash", "divided": True})

    d["order"] = ["intro", "what", "gap", "support", "company", "reviews",
                  "close"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("about: orphaned %s" % orphans)
    write("page.about.json", header, d)
    return "about", len(d["order"])


# ===========================================================================
def reviews():
    header, d = read("page.reviews.json")
    S = d["sections"]

    S["standard"] = cols(
        "standard", "The standard", "The standard this feed will be held to",
        None,
        [("Verified buyers only",
          "A review has to come from an order. No unverified submissions, and "
          "no reviews written by us."),
         ("Negative reviews stay up",
          "Published alongside the rest, unedited. If the socks disappoint "
          "someone, that belongs here."),
         ("Filterable by activity and rating",
          "A commuter's experience is more useful to another commuter than an "
          "overall average is. The filters go live with the feed."),
         ("The aggregate is the real one",
          "Whatever the average turns out to be is what gets printed, "
          "including the rating and the total volume in one line."),
         ("We will not offer anything for a review",
          "No discount, no free pair, no prize draw. A review bought with an "
          "incentive is not evidence, and it is not permitted to be presented "
          "as though it were.")])

    S["faq"] = faq(
        "questions", "Questions", "About the feed that is not here yet.", None,
        [("When will there be reviews?",
          "When enough people have bought and used a pair to make a rating "
          "mean something. We would rather show nothing than show four reviews "
          "and an average."),
         ("Will you publish bad reviews?",
          "Yes, unedited and alongside the rest. A feed with no negatives in "
          "it tells a careful reader that it has been filtered, which is worse "
          "than a mixed one.")],
        emit=True)

    d["order"] = ["breadcrumb", "intro", "standard", "meanwhile", "faq",
                  "feed", "buy"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("reviews: orphaned %s" % orphans)
    write("page.reviews.json", header, d)
    return "reviews", len(d["order"])


# ===========================================================================
def press():
    header, d = read("page.press.json")
    S = d["sections"]

    # Double duty: a usable fact sheet for a journalist, and a dense block of
    # unambiguous brand facts on a high-crawl page — including three explicit
    # negatives that pre-empt claims an assistant might otherwise infer.
    S["facts"] = collections.OrderedDict([
        ("type", "company-details"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("anchor_id", "brand-facts"),
            ("emit_schema", False),
            ("eyebrow", "The facts"),
            ("heading", "Everything a journalist needs, in one place."),
            ("lede", rich(
                "Logo, product photography and this fact sheet are available "
                "on request. Email us and a person will reply.")),
        ])),
        ("blocks", collections.OrderedDict([
            ("f1", {"type": "row", "settings": {
                "label": "Company", "kind": "text",
                "value": "HydroSox, a UK registered company"}}),
            ("f2", {"type": "row", "settings": {
                "label": "Registered address", "kind": "text",
                "value": "399–405 Oxford Street, Mayfair, London W1C 2BU"}}),
            ("f3", {"type": "row", "settings": {
                "label": "Product", "kind": "text",
                "value": "One waterproof sock: three-layer knit, licensed "
                         "Porelle® membrane, four colourways, UK 3–14"}}),
            ("f4", {"type": "row", "settings": {
                "label": "Price", "kind": "text",
                "value": "£20.00 a pair, £16.00 a pair in a five-pack"}}),
            ("f5", {"type": "row", "settings": {
                "label": "Membrane", "kind": "text",
                "value": "Porelle®, licensed third party"}}),
            ("f6", {"type": "row", "settings": {
                "label": "Test data", "kind": "text",
                "value": "None published. We do not have independently tested "
                         "figures."}}),
            ("f7", {"type": "row", "settings": {
                "label": "Reviews", "kind": "text",
                "value": "None published. There are none yet."}}),
            ("f8", {"type": "row", "settings": {
                "label": "Certification", "kind": "text",
                "value": "No certificate has been issued in relation to "
                         "masah, by us or by anyone else."}}),
        ])),
        ("block_order", ["f%d" % n for n in range(1, 9)]),
    ])

    d["order"] = ["breadcrumb", "intro", "facts", "form"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("press: orphaned %s" % orphans)
    write("page.press.json", header, d)
    return "press", len(d["order"])


# ===========================================================================
def partner_with_us():
    header, d = read("page.partner-with-us.json")
    S = d["sections"]

    S["proposition"] = cols(
        "proposition", "What you would be stocking",
        "What you would be stocking", None,
        [("One product, properly specified",
          "A named, licensed membrane and a published construction. Easier to "
          "sell than an unnamed laminate, and it stands up to a customer "
          "asking what is actually in it."),
         ("A price that does not move",
          "One retail price across every channel, so you are never undercut by "
          "our own storefront."),
         ("Stated limits",
          "We publish what the product will not do. That reduces returns, and "
          "it is the reason customers believe the rest of it."),
         ("UK company, UK stock",
          "Registered address and phone published. Shipped from the UK, not "
          "drop-shipped from elsewhere."),
         ("A category with a defined audience",
          "Waterproof socks sell to walkers, cyclists, runners and trades. The "
          "wudu segment adds a large, geographically concentrated audience "
          "that mainstream outdoor brands do not serve at all."),
         ("Four sizes, four colours, one SKU family",
          "A small range to hold and a simple one to merchandise. No seasonal "
          "carryover and no size curve to guess at beyond UK 3 to 14.")])

    # The form asks "what is this about" but the page never said who it was
    # for. Naming the channels helps the right enquiries arrive.
    S["audience"] = cols(
        "who-this-is-for", "Who this is for",
        "The kinds of enquiry we can act on.", None,
        [("Independent outdoor and cycling retailers",
          "Physical or online, UK based."),
         ("Islamic retailers and mosque shops",
          "A segment mainstream outdoor wholesalers do not serve, and where "
          "the product argument is strongest."),
         ("Workwear and safety suppliers",
          "Selling into trades, agriculture, groundworks and facilities."),
         ("Corporate and bulk orders",
          "Staff kit, event supply, and charitable distribution.")],
        scheme="wash")

    # Presentation, to the mockup DOM (2026-08-07): the audience as the band
    # of paper cards two across on wash — the stocking list already matches
    # the mockup's stacked rows. Words untouched.
    #
    # The form STAYS two-column: the mockup's centred card was tried and the
    # client reversed it the same day ("looking too big") — heading, lede and
    # the direct email/phone on the left, the fields on the right.
    S["audience"]["settings"].update({
        "layout": "band", "color_scheme": "wash", "card_columns": "two"})
    S["form"]["settings"].update({
        "color_scheme": "paper", "centre": False})

    d["order"] = ["intro", "proposition", "audience", "proof", "direct",
                  "form", "press"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("partner: orphaned %s" % orphans)
    write("page.partner-with-us.json", header, d)
    return "partner-with-us", len(d["order"])


# ===========================================================================
def contact():
    header, d = read("page.contact.json")
    S = d["sections"]

    # Eight tiles rather than six. Masah is one of the most common reasons
    # someone will contact this business and the grid had no route to it;
    # warranty is a legitimate contact reason and completes the second row.
    tiles = [
        ("Size guide",
         "Measurement-led, four bands, and what to do if you fall between two.",
         "/pages/size-guide"),
        ("Shipping and delivery",
         "What is settled and what is still being confirmed.",
         "/pages/shipping-and-delivery"),
        ("Returns and refunds", "Fourteen days, no reason needed.",
         "/pages/returns-and-refunds"),
        ("Care and washing", "What shortens the life of a membrane.",
         "/pages/care-and-washing"),
        ("How to make masah",
         "The conditions, the method and how long it lasts.",
         "/pages/how-to-make-masah"),
        ("Warranty", "Where you stand if a pair is faulty rather than worn.",
         "/pages/warranty"),
        ("Track an order", "Ask us and we will look.", "/pages/track-order"),
        ("Questions", "The things people ask before they buy.", "/pages/faq"),
    ]
    blocks, order = collections.OrderedDict(), []
    for n, (title, body, link) in enumerate(tiles, 1):
        k = "r%d" % n
        blocks[k] = collections.OrderedDict([
            ("type", "card"),
            ("settings", collections.OrderedDict([
                ("title", title), ("body", body), ("link", link)]))])
        order.append(k)
    S["routes"]["blocks"] = blocks
    S["routes"]["block_order"] = order
    S["routes"]["settings"]["columns"] = 4

    write("page.contact.json", header, d)
    return "contact", len(order)


# ===========================================================================
def main():
    for fn in (technology, faq_page, size_guide, care, about, reviews, press,
               partner_with_us, contact):
        name, n = fn()
        print("  %-20s %s" % (name, n))


if __name__ == "__main__":
    main()
