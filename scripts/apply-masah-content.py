#!/usr/bin/env python3
"""Builds the How to Make Masah page from the client's v4 Document 3.

History: this script previously composed a different masah page and was
deliberately never run — the client's own rule held the page as a placeholder
until scholarly sign-off. On 8 August 2026 the client supplied Document 3 of
the v4 rewrite, whose masah copy is written as sourced reportage, and
instructed application ("do the same for this pages"). It is applied with the
document's own red gates intact:

  * No HowTo schema. The document's developer note forbids it before
    scholarly approval — schema is read directly by language models and is
    much harder to retract than page copy.
  * The S8 "Read what the scholars said" link is held: the quotes it would
    point to do not exist yet.
  * The water-inside-the-sock ruling is deliberately NOT paraphrased; the
    page says so in the document's own words (S6 note).
  * The document asks the reviewing scholars to check S3, S4 and parts of
    S10 after publication of this version; that review remains outstanding
    and is recorded in the project memory.

Every sentence below is the document's, verbatim, including typography.
Idempotent: running it twice changes nothing the second time.
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"

ALSALAM = "https://alsalam.ac.uk/wiping-over-socks"


def rich(*paras):
    return "".join("<p>%s</p>" % p.strip() for p in paras if p and p.strip())


def _lead_comments(raw):
    pos = 0
    while True:
        m = re.match(r"\s*/\*[\s\S]*?\*/\s*", raw[pos:])
        if not m or m.end() == 0:
            return pos
        pos += m.end()


def item(title, body, link=None, title_link=False):
    """A row. `title_link` makes the heading itself the link.

    A source is already named in full in its title, so printing the bare URL
    underneath as a second link says the same thing twice — once in a form
    nobody reads. The title carries the destination instead.
    """
    st = collections.OrderedDict([("title", title), ("body", rich(body))])
    if link:
        st["link_label"], st["link_url"] = link
        if title_link:
            st["link_title"] = True
    return collections.OrderedDict([("type", "item"), ("settings", st)])


def cols(anchor, eyebrow, heading, lede, entries, layout="list",
         numbered=False, scheme="paper", footnote=None):
    blocks, order = collections.OrderedDict(), []
    for n, entry in enumerate(entries, 1):
        k = "i%d" % n
        blocks[k] = item(*entry)
        order.append(k)
    st = collections.OrderedDict([
        ("color_scheme", scheme), ("layout", layout), ("numbered", numbered),
        ("anchor_id", anchor), ("eyebrow", eyebrow), ("heading", heading)])
    if lede:
        st["lede"] = rich(lede)
    if footnote:
        st["footnote"] = footnote
    return collections.OrderedDict([
        ("type", "content-columns"), ("settings", st),
        ("blocks", blocks), ("block_order", order)])


def main():
    path = TPL / "page.how-to-make-masah.json"
    raw = path.read_text()
    header = raw[:_lead_comments(raw)]
    d = json.loads(raw[_lead_comments(raw):],
                   object_pairs_hook=collections.OrderedDict)
    S = d["sections"]

    # S1 — opening. The first paragraph is written to make complete sense on
    # its own; the sub-note is the page's we-are-not-scholars boundary.
    S["intro"] = collections.OrderedDict([
        ("type", "centre-note"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("heading_tag", "h1"),
            ("max_width", 46),
            ("eyebrow", "How to make masah"),
            ("heading", "How to make masah on socks"),
            ("body", rich(
                "Masah means wiping over your socks during wudu instead of "
                "washing your feet. This page explains what it is, the "
                "conditions scholars set, how it’s done and how long it "
                "lasts.")),
            ("footnote", rich(
                "We make socks. We’re not scholars. Everything here is "
                "drawn from published sources, which are named at the bottom "
                "of the page, and none of it is a ruling. For a ruling that "
                "applies to you, ask a scholar you trust.")),
        ])),
    ])

    # S2 — khuff and jawrab. Every reference to Dr Nadwi links to the
    # Al-Salam article, per the document's developer note.
    S["words"] = cols(
        "two-words", "Two words",
        "Khuff and jawrab aren’t the same thing",
        "Most of the disagreement about masah on socks comes back to this, "
        "and it’s rarely explained simply.",
        [("Khuff — leather footwear",
          "Khuff, plural khuffain, means leather footwear that covers the "
          "ankle. Closer to a boot than a sock. Wiping over khuffain is "
          "recorded in the authentic hadith collections and is accepted "
          "across all four Sunni schools."),
         ("Jawrab — cloth socks",
          "Jawrab is the word for socks made of cloth rather than leather. "
          "Dr Akram Nadwi of the Al-Salam Institute in Oxford notes it came "
          "into Arabic from the Persian gor-e-pa, meaning “grave of the "
          "foot” — the Arabs had no word of their own for something "
          "they rarely wore.",
          ("Al-Salam Institute, Oxford", ALSALAM)),
         ("Where the discussion sits",
          "The question was never really whether you can wipe over khuffain. "
          "It’s whether cloth socks share enough of the same properties "
          "to take the same ruling, and if so, which properties matter.")],
        scheme="paper")

    # S3 — the conditions. The document's own red block asks the reviewing
    # scholars to check all five wordings; that review is outstanding.
    S["conditions"] = cols(
        "conditions", "The conditions", "What the socks have to do",
        "Different scholars set slightly different conditions, and some "
        "treat them as practical guidance rather than strict requirements. "
        "These are the ones that come up again and again.",
        [("Put on after a full wudu",
          "The socks go on after a complete wudu in which the feet were "
          "washed. This one isn’t disputed."),
         ("Covering the ankle",
          "The covering has to come over the ankle. Both khuff and cloth "
          "socks do, which is much of why many scholars applied the same "
          "ruling to both."),
         ("Strong enough to walk in",
          "The classical wording is that the footwear should stand up to "
          "walking a distance without tearing — usually put at around "
          "three miles."),
         ("Water shouldn’t easily soak through",
          "Stated by many scholars, and the condition a waterproof sock "
          "speaks to most directly."),
         ("Staying on without being tied",
          "The covering should stay on the foot in normal use rather than "
          "needing constant adjustment.")],
        scheme="wash",
        footnote=(
            "Al-Salam Institute records the last three as conditions "
            "“some jurists propose”, and describes them as practical "
            "rather than affecting the core ruling. Other scholars treat "
            "them as necessary. That difference is real and long-standing, "
            "and it isn’t one a sock company can settle."))

    # S4 — the method, numbered. NO HowTo schema until scholarly approval.
    S["method"] = cols(
        "method", "The method", "How masah is done",
        "Described as it’s commonly taught. The details of hand "
        "position differ between the schools, and those differences are set "
        "out further down.",
        [("Do a full wudu first, then put the socks on",
          "The feet are washed as part of a complete wudu before the socks "
          "go on. Masah applies from the next wudu onwards, not this one."),
         ("At your next wudu, wipe instead of washing",
          "Go through wudu as normal. When you reach the feet, wipe over "
          "the socks rather than washing the feet."),
         ("Wet hands, over the top of the foot",
          "With wet hands, wipe over the upper surface of each sock, moving "
          "from the toes towards the shin. Right hand for the right foot, "
          "left for the left."),
         ("Top surface only",
          "The wiping is of the upper surface. The sole isn’t wiped.")],
        layout="steps", numbered=True, scheme="paper")

    # S5 — how long it lasts.
    S["duration"] = cols(
        "how-long", "How long", "How long masah lasts",
        "This is the part most commonly misunderstood, and it’s "
        "misunderstood in one particular way.",
        [("At home: twenty-four hours",
          "Someone who isn’t travelling in the sense the Sharia "
          "recognises may wipe for one day and one night."),
         ("Travelling: seventy-two hours",
          "Someone who is a traveller in that sense may wipe for three days "
          "and three nights."),
         ("The clock starts at the first wipe",
          "This is the bit people get wrong. The period runs from the first "
          "masah you make after your wudu breaks — not from when you "
          "put the socks on. Sources including IslamQA state this "
          "directly."),
         ("When the time is up",
          "Once the period ends, masah is no longer valid. The socks come "
          "off and the feet are washed for the next wudu.")],
        scheme="wash")

    # S6 — what ends it. The water-inside point is deliberately left for the
    # reviewing scholars to word; the note saying so is the document's own.
    S["ends"] = cols(
        "what-ends-it", "What ends it", "What ends masah",
        None,
        [("Anything that breaks wudu",
          "Masah is part of wudu. Whatever breaks the wudu breaks the masah "
          "with it, and a fresh wudu is needed."),
         ("Taking the socks off",
          "Removing them during the period ends the masah, even if the time "
          "hasn’t run out."),
         ("Anything requiring ghusl",
          "Where a full ghusl is required, wiping isn’t enough. The "
          "feet are washed.")],
        layout="split", scheme="paper",
        footnote=(
            "Sources also deal with water getting inside the sock and "
            "wetting the foot. Because that’s directly relevant to a "
            "waterproof sock, we’ve deliberately left it for the "
            "reviewing scholars to word rather than paraphrasing it "
            "ourselves."))

    # S7 — where the schools differ: the page's most important section for a
    # UK audience, on the dark emphasis ground. Nadwi references link.
    S["schools"] = cols(
        "the-schools", "The schools", "Where the schools differ",
        "Set out as a description of positions, not a recommendation. "
        "Follow the school and the scholar you follow.",
        [("On leather khuffain",
          "All four Sunni schools accept wiping over khuffain. This "
          "isn’t contested."),
         ("On cloth socks — the stricter reading",
          "Several schools have historically required a sock to be like a "
          "khuff in strength and in not letting water through before the "
          "same ruling applies. On that reading, thin cotton socks "
          "don’t qualify."),
         ("On cloth socks — the broader reading",
          "Dr Akram Nadwi records that a large number of Companions, early "
          "scholars and Imams are reported to have wiped over cloth socks, "
          "and that several contemporary scholars permit it without "
          "insisting on strict thickness. He cites the report that Imam Abu "
          "Hanifa himself wiped over his socks near the end of his life, "
          "saying: “Today I have done something I had not done "
          "before.”",
          ("Al-Salam Institute, Oxford", ALSALAM)),
         ("Why this question comes up so much in Britain",
          "Nadwi writes that he held a more cautious view before coming to "
          "England, and revised it after seeing how hard Muslims found it "
          "to wash their feet in offices, universities and airports — "
          "to the point that some were missing prayers. Whatever position "
          "you hold, that’s the situation this question is now asked "
          "in.",
          ("Al-Salam Institute, Oxford", ALSALAM))],
        scheme="ink")

    # S8 — the only commercial section. The second CTA of the document's
    # pair ("Read what the scholars said") is held until their words exist.
    S["fits"] = collections.OrderedDict([
        ("type", "centre-note"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"),
            ("max_width", 46),
            ("eyebrow", "The socks"),
            ("heading", "Where our socks fit into this"),
            ("heading_size", "h3"),
            ("body", rich(
                "HydroSox socks are waterproof, they hold their shape rather "
                "than collapsing against the foot, and they’re shaped to "
                "stay on. Those are physical facts you can check. Whether "
                "they satisfy the conditions above, for the school you "
                "follow, isn’t ours to decide.")),
            ("footnote", rich(
                "Shaykh Mufti Saiful Islam and Mufti Amjad Mohammed have "
                "examined them. There’s no certificate, because nobody "
                "issues certificates for socks.")),
            ("cta_label", "Wudu socks"),
            ("cta_url", "/pages/wudu-socks"),
        ])),
    ])

    # S9 — sources, each a real outbound link where a URL exists. The
    # correction offer is the strongest trust signal available on a page
    # like this, and no competitor makes it.
    S["sources"] = cols(
        "sources", "Sources", "Where this came from",
        "Everything above comes from one of these. Where they differ, "
        "we’ve said so rather than picking one.",
        [("Al-Salam Institute, Oxford — “Wiping Over Socks: A "
          "Brief Overview”, Dr Mohammad Akram Nadwi",
          "The overview this page draws its account of the two readings "
          "from.",
          ("alsalam.ac.uk/wiping-over-socks", ALSALAM), True),
         ("IslamQA (Hanafi) — Darul Iftaa Birmingham and Askimam, on "
          "how long masah lasts and when the period starts",
          "Where the twenty-four and seventy-two hour periods, and the "
          "point the clock starts, are set out.",
          ("islamqa.org", "https://islamqa.org"), True),
         ("Sahih al-Bukhari and Sahih Muslim",
          "The underlying narrations on wiping over khuffain, as cited in "
          "the above.")],
        scheme="wash",
        footnote=(
            "If you think anything on this page is wrong, tell us and "
            "we’ll correct it. That offer is open to anyone."))

    # S10 — questions. Unique site-wide (the validator holds the line), so
    # the page claims FAQPage for them. Q7's refusal stays exactly as
    # written, per the document.
    qs = [
        ("What is masah?",
         "Masah means wiping over your socks during wudu instead of washing "
         "your feet. The permission is recorded in the authentic hadith "
         "collections in relation to khuffain — leather footwear that "
         "covers the ankle. Whether it extends to cloth socks, and on what "
         "conditions, has been discussed by scholars for centuries."),
        ("What are the conditions for wiping over socks?",
         "The ones that come up most often: the socks go on after a full "
         "wudu, they cover the ankle, they’re strong enough to walk in, "
         "water doesn’t easily soak through, and they stay on without "
         "being tied. Scholars differ on how strictly the last three "
         "apply."),
        ("How long does masah last?",
         "Twenty-four hours if you’re at home and seventy-two if "
         "you’re travelling. The period starts at your first wipe "
         "after wudu breaks, not when you put the socks on — which is "
         "the detail most commonly misunderstood."),
        ("Can you do masah on ordinary cotton socks?",
         "This is where scholars differ. The stricter reading requires the "
         "sock to be like a khuff in strength and in not letting water "
         "through, which thin cotton socks aren’t. A broader reading, "
         "held by a number of Companions, early Imams and contemporary "
         "scholars, permits it more readily."),
        ("What ends masah?",
         "Anything that breaks wudu, taking the socks off, and anything "
         "that requires a full ghusl. When the twenty-four or seventy-two "
         "hours are up, masah is no longer valid and the feet are washed "
         "for the next wudu."),
        ("Is masah on socks allowed in the Hanafi school?",
         "Hanafi sources have historically required a sock to be like a "
         "khuff in strength and in not letting water through. It’s "
         "also reported that Imam Abu Hanifa himself wiped over his socks "
         "near the end of his life. Ask a Hanafi scholar for the position "
         "that applies to you."),
        ("Do HydroSox meet the conditions?",
         "We can’t answer that, and it would be wrong of us to. Our "
         "socks are waterproof, they hold their shape and they stay on the "
         "foot — those are physical facts. Whether that satisfies the "
         "conditions, for the school you follow, is a question for a "
         "scholar rather than a sock company."),
        ("Where can I get a ruling for my own situation?",
         "From a scholar you trust, or your local mosque or Dar al-Ifta. "
         "This page reports established positions and names its sources so "
         "you can take them to someone qualified. It’s a starting "
         "point for that conversation, not a replacement for it."),
    ]
    blocks, order = collections.OrderedDict(), []
    for n, (q, a) in enumerate(qs, 1):
        k = "q%d" % n
        blocks[k] = collections.OrderedDict([
            ("type", "question"),
            ("settings", collections.OrderedDict([
                ("question", q), ("answer", rich(a))]))])
        order.append(k)
    S["questions"] = collections.OrderedDict([
        ("type", "faq-accordion"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"), ("anchor_id", "questions"),
            ("one_at_a_time", False), ("emit_schema", True),
            ("eyebrow", "Questions"), ("heading", "Common questions"),
            # No buy button under a religious ruling — the page closes on a
            # commercial band instead. The route to a person takes its place.
            ("help_prefix", "Something not here?"),
            ("help_label", "Phone or email us"),
            ("help_link", "/pages/contact"),
            ("cta_label", "")])),
        ("blocks", blocks), ("block_order", order)])

    # The old placeholder sections go; the page argues from sources now.
    for old in ("scholarly", "wudu", "quiet"):
        S.pop(old, None)

    d["order"] = ["crumb", "intro", "words", "conditions", "method",
                  "duration", "ends", "schools", "fits", "sources",
                  "questions"]
    orphans = [k for k in S if k not in d["order"]]
    if orphans:
        raise SystemExit("masah: orphaned %s" % orphans)

    path.write_text(header + json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    print("wrote templates/page.how-to-make-masah.json  (%d sections, %d questions)"
          % (len(d["order"]), len(qs)))


if __name__ == "__main__":
    main()
