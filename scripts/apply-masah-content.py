#!/usr/bin/env python3
"""Composes the full How to Make Masah page — HELD, NOT APPLIED.

=============================================================================
DO NOT RUN THIS SCRIPT UNTIL A QUALIFIED SCHOLAR HAS SIGNED THE PAGE OFF.
=============================================================================

The content brief makes the condition explicit and non-negotiable: this page
reports Islamic jurisprudence, it is written by a marketing agency, and it must
be read line by line — with the authority to change any sentence — by someone
qualified before it is published. Where no scholar is available, the brief says
to publish the shorter placeholder instead.

The placeholder is what is live now. Because a push to this repo deploys
straight to the storefront, running this script *is* publishing. So the page is
composed here, in full, and left unapplied. After sign-off, and after the
reviewer's corrections have been written into the strings below:

    python3 scripts/apply-masah-content.py

Three specific things the reviewer must rule on before that happens. They are
marked REVIEW in the code and each one is a place where we would rather cut the
sentence than state it imprecisely:

  1. S3 item 03 — whether the "roughly three miles" formulation belongs on the
     page at all, or needs more precise attribution.
  2. S3 item 04 — whether "water should not easily seep through" is the right
     rendering, or whether a stronger or weaker formulation is accurate.
  3. S6 — sources address water entering the sock and wetting a substantial
     part of the foot. That is directly relevant to a waterproof product, so we
     have deliberately not paraphrased it. The reviewer's wording goes in, or
     the point comes out.

Two things this script deliberately does NOT do, and which must stay undone
until approval: it adds no HowTo schema to the method section, and it leaves
FAQPage emission off. Schema is ingested directly by language models and is far
harder to retract than page copy.

What the page does not say, anywhere: that HydroSox socks are valid,
permissible, approved, certified or compliant. It states what the sock
physically does and what conditions the sources stipulate, and leaves the
reader to join those — or to ask someone qualified to.
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates" / "page.how-to-make-masah.json"

NADWI = "https://alsalam.ac.uk/wiping-over-socks/"


def rich(*paras):
    return "".join("<p>%s</p>" % p.strip() for p in paras if p and p.strip())


def item(title, body):
    return collections.OrderedDict([
        ("type", "item"),
        ("settings", collections.OrderedDict([
            ("title", title), ("body", rich(body))])),
    ])


def cols(key, eyebrow, heading, lede, entries, numbered=False, scheme="paper",
         link=None, footnote=None):
    blocks, order = collections.OrderedDict(), []
    for n, (t, b) in enumerate(entries, 1):
        k = "i%d" % n
        blocks[k] = item(t, b)
        order.append(k)
    st = collections.OrderedDict([
        ("color_scheme", scheme), ("layout", "list"), ("numbered", numbered),
        ("anchor_id", key), ("eyebrow", eyebrow), ("heading", heading),
    ])
    if lede:
        st["lede"] = rich(lede)
    if footnote:
        st["footnote"] = footnote
    if link:
        st["link_label"], st["link_url"] = link
    return collections.OrderedDict([
        ("type", "content-columns"), ("settings", st),
        ("blocks", blocks), ("block_order", order)])


def main():
    S = collections.OrderedDict()

    S["crumb"] = {"type": "breadcrumb", "settings": {
        "color_scheme": "paper", "home_label": "Home",
        "current_label": "How to make masah"}}

    # ---------------------------------------------------------------- S1
    # The standfirst is written to stand entirely on its own: it is the block
    # most likely to be lifted whole by an assistant answering "what is masah?",
    # so it has to make complete sense with nothing around it. The boundary is
    # stated immediately underneath rather than at the foot of the page.
    S["intro"] = collections.OrderedDict([
        ("type", "centre-note"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("anchor_id", "masah"),
            ("eyebrow", "How to make masah"),
            ("heading",
             "Masah on socks: what is established, and where the schools differ."),
            ("lead_first_para", True),
            ("body", rich(
                "Masah is the act of wiping over footwear during wudu instead "
                "of washing the feet. The permission for it is recorded in the "
                "authentic hadith collections, including Sahih al-Bukhari and "
                "Sahih Muslim, in relation to khuffain — leather footwear "
                "covering the ankle. Whether, and on what conditions, it "
                "extends to fabric socks has been discussed by scholars for "
                "centuries.")),
            ("footnote", rich(
             "HydroSox makes socks. This page reports what established "
             "scholarship holds and names its sources. It does not issue "
             "rulings, and nothing on it should be treated as one. For a "
             "ruling that applies to you, ask a scholar you trust.")),
        ])),
    ])

    # ---------------------------------------------------------------- S2
    S["words"] = cols(
        "two-words", "Two words", "Khuff and jawrab are not the same thing.",
        "Almost every disagreement about masah on socks comes back to this "
        "distinction, and it is rarely explained plainly.",
        [("Khuff — leather footwear",
          "Khuff (plural khuffain) refers to leather footwear that covers the "
          "ankle. It is closer to a boot than to a sock. The permission to "
          "wipe over khuffain is recorded in the authentic collections and is "
          "accepted across the four Sunni schools."),
         ("Jawrab — fabric socks",
          "Jawrab is the term for socks made of cloth rather than leather. "
          "<a href=\"%s\" rel=\"noopener\">Dr Akram Nadwi of the Al-Salam "
          "Institute</a> notes that the word entered Arabic from the Persian "
          "gor-e-pa, literally &ldquo;grave of the foot&rdquo;, because the "
          "Arabs had no word of their own for an item they rarely wore." % NADWI),
         ("Where the discussion actually sits",
          "The question has never really been whether one may wipe over "
          "khuffain. It is whether jawrab share enough of the relevant "
          "properties to take the same ruling — and if so, which properties "
          "matter.")])

    # ---------------------------------------------------------------- S3
    # REVIEW: items 03 and 04 below, and the closing note's characterisation of
    # the disagreement. See the module docstring.
    S["conditions"] = cols(
        "conditions", "The conditions", "What the sources ask of the sock.",
        "Different scholars stipulate different conditions, and some regard "
        "them as procedural rather than essential. These are the ones that "
        "recur.",
        [("Put on in a state of purity",
          "The footwear must be put on after a complete wudu in which the feet "
          "were washed. This condition is not disputed."),
         ("Covering the required part of the foot",
          "The covering must extend over the ankle. Both khuff and jawrab do "
          "this, which is a large part of why many scholars applied the same "
          "ruling to both."),
         ("Durable enough to be walked in",
          "The classical formulation is that the footwear should withstand "
          "walking a distance without tearing — commonly expressed as roughly "
          "three miles."),
         ("Water should not easily seep through",
          "Stated by many scholars, and the condition a waterproof "
          "construction speaks to most directly."),
         ("Staying in place without being tied",
          "The covering should remain on the foot in normal use rather than "
          "needing constant adjustment or fastening.")],
        footnote=(
            "Al-Salam Institute records the last three of these as conditions "
            "“some jurists propose”, and describes them as procedural rather "
            "than affecting the core ruling. Other scholars treat them as "
            "necessary. This is a genuine and long-standing difference, and it "
            "is not one a sock company can settle."))

    # ---------------------------------------------------------------- S4
    # REVIEW: the method as commonly taught in Hanafi sources. The reviewer may
    # want it set out school by school instead, in which case this section is
    # restructured rather than edited. NO HowTo schema until then.
    S["method"] = cols(
        "method", "The method", "How the wiping is done.",
        "Described as it is commonly taught. Details of hand position and "
        "extent differ between the schools, and the differences are set out in "
        "the section below.",
        [("Complete wudu first, then put the socks on",
          "The feet must be washed as part of a complete wudu before the socks "
          "go on. Masah applies from the next wudu onwards, not from this one."),
         ("At the next wudu, wipe rather than wash",
          "Proceed through wudu as normal. When you reach the feet, wipe over "
          "the socks instead of washing the feet."),
         ("Wet hands, over the top of the foot",
          "With wet hands, wipe over the upper surface of each sock, moving "
          "from the toes towards the shin. The right hand wipes the right foot "
          "and the left hand the left."),
         ("Both feet, and only the top surface",
          "The wiping is of the upper surface. The sole is not wiped.")],
        numbered=False, scheme="wash")

    # ---------------------------------------------------------------- S5
    S["duration"] = cols(
        "duration", "Duration", "Twenty-four hours, or seventy-two.",
        "This is the detail most commonly misunderstood, and it is "
        "misunderstood in a specific way.",
        [("A resident: twenty-four hours",
          "Someone who is not travelling in the sense recognised by the Sharia "
          "may wipe for one day and one night."),
         ("A traveller: seventy-two hours",
          "Someone who is a traveller in that sense may wipe for three days "
          "and three nights."),
         ("The clock starts at the first wipe, not when you put them on",
          "This is the part most people get wrong. The period runs from the "
          "first masah performed after the wudu was broken — not from the "
          "moment the socks went on. Sources including IslamQA state this "
          "explicitly."),
         ("When the period ends",
          "Once the period expires, masah is no longer valid. The socks come "
          "off and the feet are washed for the next wudu.")])

    # ---------------------------------------------------------------- S6
    # REVIEW: the water-ingress point is deliberately absent. See docstring.
    S["invalidators"] = cols(
        "invalidators", "Invalidators", "Three things end it.", None,
        [("Anything that breaks wudu",
          "Masah is part of wudu. Whatever invalidates the wudu invalidates "
          "the masah with it, and a fresh wudu is required."),
         ("Taking the socks off",
          "Removing the footwear during the period ends the masah, even if the "
          "period has not expired."),
         ("A state requiring ghusl",
          "Where major ritual impurity applies, wiping is not sufficient. A "
          "full ghusl is required, and the feet are washed.")],
        footnote=(
            "Sources also address water entering the sock and wetting a "
            "substantial part of the foot. Because that scenario is directly "
            "relevant to a waterproof sock, we have deliberately not "
            "summarised it here — it is a point on which we would rather quote "
            "the reviewing scholar directly than paraphrase."))

    # ---------------------------------------------------------------- S7
    S["schools"] = cols(
        "schools", "The schools",
        "On khuffain, agreement. On jawrab, discussion.",
        "Presented as a description of positions, not as a recommendation. "
        "Follow the school and the scholar you follow.",
        [("On leather khuffain",
          "The four Sunni schools accept the permissibility of wiping over "
          "khuffain. This is not a point of contention."),
         ("On fabric socks — the stricter reading",
          "Several schools have historically required that a sock be "
          "sufficiently like a khuff in durability and impermeability before "
          "the same ruling applies. On this reading, thin cotton socks do not "
          "qualify."),
         ("On fabric socks — the broader reading",
          "<a href=\"%s\" rel=\"noopener\">Dr Akram Nadwi</a> records that a "
          "substantial number of Companions, Tabi&rsquo;een and early Imams "
          "are reported to have wiped over cloth socks, and that a number of "
          "contemporary scholars permit it without insisting on strict "
          "thickness. He cites the narration in which Imam Abu Hanifa is "
          "reported to have wiped over his socks near the end of his life, "
          "saying: &ldquo;Today I have done something I had not done "
          "before.&rdquo;" % NADWI),
         ("Why the practical question is live in Britain",
          "<a href=\"%s\" rel=\"noopener\">Nadwi</a> writes that he took a "
          "more cautious position before coming to England, and revised it "
          "after seeing the difficulty Muslims faced washing their feet in "
          "offices, universities and airports — to the point that some were "
          "missing prayers. Whatever position you hold, that is the context in "
          "which this question is now asked here." % NADWI)],
        scheme="wash")

    # ---------------------------------------------------------------- S8
    S["product"] = collections.OrderedDict([
        ("type", "centre-note"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "ink"),
            ("anchor_id", "the-product"),
            ("eyebrow", "The product"),
            ("heading", "What is built for this, and what is not certified."),
            ("body", rich(
                "HydroSox is waterproof, structured to hold its shape rather "
                "than collapse against the foot, and shaped to stay in place "
                "through normal wear. Those are physical properties we can "
                "state and you can check. Whether they satisfy the conditions "
                "set out above, for the school you follow, is not ours to "
                "determine.")),
            ("footnote", rich(
             "No certificate has been issued, by us or by anyone else.")),
            ("cta_label", "Wudu socks"),
            ("cta_url", "/pages/wudu-socks"),
            ("link_label", "How it is built"),
            ("link_url", "/pages/technology"),
        ])),
    ])

    # ---------------------------------------------------------------- S9
    # Real outbound links to named authorities. Attribution without a link is
    # not attribution, and being visibly sourced is the whole basis on which
    # this page can be quoted at all.
    S["sources"] = cols(
        "sources", "Sources", "Where this came from.",
        "Every substantive statement above is drawn from one of these. Where "
        "they differ, we have said so rather than picking one.",
        [("Al-Salam Institute, Oxford",
          "&ldquo;Wiping Over Socks: A Brief Overview&rdquo;, Dr Mohammad "
          "Akram Nadwi. <a href=\"%s\" rel=\"noopener\">alsalam.ac.uk</a>"
          % NADWI),
         ("IslamQA (Hanafi)",
          "Darul Iftaa Birmingham and Askimam, on the duration of masah and "
          "when the period begins. <a href=\"https://islamqa.org/\" "
          "rel=\"noopener\">islamqa.org</a>"),
         ("Sahih al-Bukhari and Sahih Muslim",
          "The underlying narrations regarding wiping over khuffain, as cited "
          "in the above.")],
        footnote=(
            "If you believe anything on this page is inaccurate, tell us and "
            "we will correct it. That offer is open to anyone, and we would "
            "rather be corrected than be wrong."))

    # ---------------------------------------------------------------- S10
    # emit_schema stays False. FAQPage on this page goes live with the
    # reviewer's sign-off and not before.
    questions = [
        ("What is masah?",
         "Masah is wiping over footwear during wudu instead of washing the "
         "feet. The permission is recorded in the authentic hadith "
         "collections in relation to khuffain — leather footwear covering the "
         "ankle. Whether it extends to fabric socks, and on what conditions, "
         "has been discussed by scholars for centuries."),
        ("What are the conditions for wiping over socks?",
         "The conditions that recur across the sources are: the socks are put "
         "on after a complete wudu, they cover the ankle, they are durable "
         "enough to walk in, water does not easily seep through, and they stay "
         "on the foot without being tied. Scholars differ on how strictly the "
         "last three apply."),
        ("How long does masah last?",
         "Twenty-four hours for a resident and seventy-two hours for a "
         "traveller in the sense recognised by the Sharia. The period runs "
         "from the first wipe performed after wudu was broken — not from the "
         "moment the socks were put on, which is the detail most commonly "
         "misunderstood."),
        ("Can you do masah on ordinary cotton socks?",
         "This is the point on which scholars differ. The stricter reading "
         "requires the sock to resemble a khuff in durability and "
         "impermeability, which thin cotton socks do not. A broader reading, "
         "held by a number of Companions, early Imams and contemporary "
         "scholars, permits it more readily."),
        ("What breaks masah?",
         "Anything that breaks wudu, removing the socks during the period, and "
         "a state requiring ghusl. When the twenty-four or seventy-two hour "
         "period expires, masah is no longer valid and the feet are washed for "
         "the next wudu."),
        ("Is masah on socks allowed in the Hanafi school?",
         "Hanafi sources have historically required a sock to be like a khuff "
         "in durability and impermeability. It is also reported that Imam Abu "
         "Hanifa himself wiped over his socks near the end of his life. Ask a "
         "Hanafi scholar for the position that applies to you."),
        ("Do HydroSox satisfy the conditions for masah?",
         "We cannot answer that, and we would be wrong to. HydroSox is "
         "waterproof, holds its shape and stays on the foot — those are "
         "physical facts. Whether they satisfy the conditions, for the school "
         "you follow, is a question for a scholar rather than for a sock "
         "company."),
        ("Where can I get a ruling for my own situation?",
         "From a scholar you trust, or a local mosque or Dar al-Ifta. This "
         "page reports established positions and names its sources so you can "
         "take them to someone qualified. It is a starting point for that "
         "conversation, not a substitute for it."),
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
    S["faq"] = collections.OrderedDict([
        ("type", "faq-accordion"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"), ("anchor_id", "questions"),
            ("one_at_a_time", False),
            ("emit_schema", False),  # REVIEW — see docstring
            ("eyebrow", "Questions"),
            ("heading", "The things people ask about masah."),
            ("lede", rich(
                "Each answer is written to stand on its own. Where the honest "
                "answer is that we cannot say, that is the answer.")),
            ("help_prefix", "Need a ruling for your own situation?"),
            ("help_label", "Ask a scholar you trust"),
            ("help_link", "/pages/contact"),
        ])),
        ("blocks", blocks), ("block_order", order),
    ])

    order = ["crumb", "intro", "words", "conditions", "method", "duration",
             "invalidators", "schools", "product", "sources", "faq"]
    data = collections.OrderedDict([
        ("sections", S), ("order", order)])
    header = ("/* How to Make Masah, composed by scripts/apply-masah-content.py.\n"
              "   Published only after scholarly review and sign-off. Re-run that\n"
              "   script rather than hand-editing. */\n")
    TPL.write_text(header + json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("wrote templates/page.how-to-make-masah.json  (%d sections, %d questions)"
          % (len(order), len(questions)))
    print("NOTE: FAQPage and HowTo schema remain OFF pending scholarly approval.")


if __name__ == "__main__":
    main()
