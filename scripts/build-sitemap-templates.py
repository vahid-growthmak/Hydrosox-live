#!/usr/bin/env python3
"""
Brings the templates into line with the sitemap.

The sitemap is the single source of truth for which page lives at which URL and
which sections it carries. Two things it asks for were missing:

  * one activity page at /pages/hiking-and-walking, not two at /pages/hiking
    and /pages/walking
  * a breadcrumb on 14 pages, a review module on 6, an inline buy widget and a
    related-guides strip on every activity page

Rather than hand-editing 20 JSON files, this script composes them, so the
mapping from sitemap row to template section is written down once and can be
re-run when the sitemap changes.

Content is only ever moved, never invented: the merged activity page takes the
hiking hero the sitemap describes ("boots that wet out on a long day in the
hills") and keeps walking's distinct rows as extra rows in the same sections.

Run from the theme root:  python3 scripts/build-sitemap-templates.py
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"

PRODUCT = "hydrosox-waterproof-socks"
PRODUCT_URL = f"/products/{PRODUCT}"

# ---------------------------------------------------------------- sitemap facts

# Pages the sitemap puts a breadcrumb on, with the middle rung it sits under.
# None means the trail is Home > This page.
BREADCRUMBS = {
    "hiking-and-walking": ("Shop by activity", "/#activity"),
    "all-day-in-boots": ("Shop by activity", "/#activity"),
    "cycling-and-commuting": ("Shop by activity", "/#activity"),
    "running-and-trail": ("Shop by activity", "/#activity"),
    "technology": None,
    "how-to-make-masah": None,
    "reviews": None,
    "our-partners": None,
    "press": None,
    "shipping-and-delivery": ("Help", "/pages/faq"),
    "returns-and-refunds": ("Help", "/pages/faq"),
    "warranty": ("Help", "/pages/faq"),
    "track-order": ("Help", "/pages/faq"),
    "wudu-socks": None,
}

ACTIVITIES = [
    "hiking-and-walking",
    "all-day-in-boots",
    "cycling-and-commuting",
    "running-and-trail",
]

# Sitemap 3.11: "Two siblings only." Each activity points at the next two.
SIBLINGS = {
    a: [x for x in ACTIVITIES if x != a][:2] for a in ACTIVITIES
}

ACTIVITY_TITLES = {
    "hiking-and-walking": "Hiking and walking",
    "all-day-in-boots": "All day in boots",
    "cycling-and-commuting": "Cycling and commuting",
    "running-and-trail": "Running and trail",
}

# Pages the sitemap puts a review module on.
REVIEW_PAGES = ACTIVITIES + ["wudu-socks", "about"]

# Sitemap 15.3: "Six tags matching the activity taxonomy plus care and wudu."
# Sitemap 16.6 makes the routing mandatory — every guide must reach exactly one
# activity page — so the tag taxonomy and the routing table are the same thing.
# (tag, destination handle, link label, supporting line)
ARTICLE_ROUTES = [
    (
        "hiking",
        "hiking-and-walking",
        "Hiking and walking",
        "Long days on wet ground, and the shoes that were never waterproof.",
    ),
    (
        "walking",
        "hiking-and-walking",
        "Hiking and walking",
        "Long days on wet ground, and the shoes that were never waterproof.",
    ),
    (
        "boots",
        "all-day-in-boots",
        "All day in boots",
        "Long shifts in footwear that keeps the rain out and then seals the sweat in.",
    ),
    (
        "cycling",
        "cycling-and-commuting",
        "Cycling and commuting",
        "Overshoes that leak at the ankle, with no drying option at the other end.",
    ),
    (
        "running",
        "running-and-trail",
        "Running and trail",
        "Cold, soaked feet on winter miles, and blisters in a wet race.",
    ),
    (
        "wudu",
        "wudu-socks",
        "Wudu socks",
        "The three physical conditions masah turns on, stated plainly.",
    ),
    (
        "care",
        "care-and-washing",
        "Care and washing",
        "What shortens the life of a membrane, and what does not.",
    ),
]


# Page templates are page.<handle>.json; blog, collection, product and 404 are
# addressed by their own file name. Resolving that here keeps every call site
# free of the prefix.
BARE = {"index", "product", "collection", "404", "blog", "blog.guides", "search", "cart", "article"}


def path_for(name):
    return TPL / (f"{name}.json" if name in BARE else f"page.{name}.json")


def load(name):
    p = path_for(name)
    if not p.exists():
        return None
    return json.loads(re.sub(r"^\s*/\*[\s\S]*?\*/\s*", "", p.read_text()))


# Shopify's JSON templates accept a leading block comment, so composed files say
# so. It tells the next reader that edits belong in this script or in the theme
# editor, not in the JSON.
HEADER = (
    "/* Composed by scripts/build-sitemap-templates.py from the sitemap.\n"
    "   Re-run that script rather than hand-editing this file; section\n"
    "   content itself is editable in the Shopify theme editor. */\n"
)


def scrub(node):
    """Drop null settings anywhere in a template.

    Shopify refuses a template that carries a null setting value and keeps the
    previously deployed version live, so the page silently stays stale and it
    reads as a slow sync. An omitted setting falls back to the schema default,
    which is what a null was trying to express anyway.
    """
    if isinstance(node, dict):
        return {k: scrub(v) for k, v in node.items() if v is not None}
    if isinstance(node, list):
        return [scrub(v) for v in node]
    return node


def save(name, data):
    path_for(name).write_text(HEADER + json.dumps(scrub(data), indent=2) + "\n")


def strip_header(text):
    return re.sub(r"^\s*/\*[\s\S]*?\*/\s*", "", text)


def buy_widget_from_home():
    """The buy widget, copied wholesale out of the homepage.

    Copied rather than re-declared so the price ladder, the colourways and the
    size guide cannot diverge between the homepage and a landing page.
    """
    home = load("index")
    buy = json.loads(json.dumps(home["sections"]["buy"]))
    buy["settings"]["anchor_id"] = "buy"
    return buy


def activity_cards_from_home():
    """{handle: {"title", "body"}} for every activity card on the homepage.

    One source of truth for what an activity is called and how it is described.
    The sibling cross-links read from here rather than carrying their own copy,
    which fixes two things at once: a card repointed at a different activity used
    to lose its body entirely (what happened when hiking and walking merged and
    the retired links were replaced), and titles drifted into two spellings — the
    homepage, menu and footer say "Cycling & Commuting" while a hand-written
    fallback map said "Cycling and commuting", so a single row could show both.
    """
    home = load("index")
    out = {}
    activity = home["sections"].get("activity", {})
    for key in activity.get("block_order", []):
        st = activity["blocks"][key].get("settings", {})
        link = (st.get("link") or "").rstrip("/")
        if link:
            out[link.split("/")[-1]] = {
                "title": st.get("title") or "",
                "body": st.get("problem") or "",
            }
    return out


def faq_from_home(limit=6):
    """The question list, copied out of the homepage FAQ."""
    home = load("index")
    faq = json.loads(json.dumps(home["sections"]["faq"]))
    keys = [k for k in faq.get("block_order", []) if faq["blocks"][k]["type"] == "question"]
    keep = keys[:limit]
    faq["blocks"] = {k: faq["blocks"][k] for k in keep}
    faq["block_order"] = keep
    faq["settings"]["anchor_id"] = "faq"
    return faq


def breadcrumb(handle, title):
    """The trail for one page.

    `current_label` is only an override — the section derives the leaf from the
    object being viewed. Emitting it as null rather than omitting it makes
    Shopify reject the entire template on upload, so an absent title is left
    out. See scrub() for the general guard.
    """
    parent = BREADCRUMBS.get(handle)
    s = {"color_scheme": "paper", "home_label": "Home"}
    if title:
        s["current_label"] = title
    if parent:
        s["parent_label"], s["parent_url"] = parent
    return {"type": "breadcrumb", "settings": s}


def review_module(scheme="wash"):
    """A review module with no reviews in it.

    Sitemap 3.6: "If real review volume is not available at launch this block is
    OMITTED rather than fabricated." The section renders nothing while it holds
    no reviews, so placing it here is safe — it appears the moment real reviews
    are entered in the editor, and until then the page is unaffected.
    """
    return {
        "type": "review-module",
        "settings": {
            "layout": "strip",
            "color_scheme": scheme,
            "pace": "tight",
            "show_aggregate": True,
            "eyebrow": "Reviews",
            "aggregate_link_label": "Read every review",
            "aggregate_link_url": "/pages/reviews",
        },
    }


def related_guides(tag, scheme="paper"):
    return {
        "type": "related-guides",
        "settings": {
            "blog": "guides",
            "tag": tag,
            "count": 2,
            "color_scheme": scheme,
            "pace": "base",
            "eyebrow": "Guides",
            "heading": "Worth reading first.",
            "link_label": "All guides",
            "link_url": "/blogs/guides",
        },
    }


# --------------------------------------------------------------- activity pages


def merge_activity_pages():
    """Fold page.walking into page.hiking as page.hiking-and-walking.

    The sitemap's hero brief for this page is hiking's ("boots that wet out on a
    long day in the hills"), so hiking leads. Walking's rows are appended to the
    matching sections, which is the whole reason the merge is lossless: both
    pages are built from the same section types with the same block shapes.
    """
    hiking, walking = load("hiking"), load("walking")
    if not hiking or not walking:
        print("  hiking/walking already merged, skipping")
        return load("hiking-and-walking")

    merged = json.loads(json.dumps(hiking))

    # Append walking's blocks to the sections that carry rows. The hero, the
    # limits note and the closing CTA are single-voice sections, so hiking's
    # stay as they are rather than being concatenated into a muddle.
    for key in ("problem", "answers", "practice"):
        if key not in merged["sections"] or key not in walking["sections"]:
            continue
        dst, src = merged["sections"][key], walking["sections"][key]
        for bk, block in src.get("blocks", {}).items():
            nk = f"w-{bk}"
            dst.setdefault("blocks", {})[nk] = block
            dst.setdefault("block_order", []).append(nk)

    # The merged page covers both, so the headings say both.
    merged["sections"]["hero"]["settings"]["eyebrow"] = "Hiking and walking"
    merged["sections"]["problem"]["settings"]["heading"] = (
        "The boot is not the last line — and most wet feet are not earned on a mountain."
    )

    save("hiking-and-walking", merged)
    for dead in ("hiking", "walking"):
        (TPL / f"page.{dead}.json").unlink(missing_ok=True)
    print("  merged hiking + walking -> hiking-and-walking (2 templates removed)")
    return merged


def build_activity(handle):
    data = load(handle)
    if not data:
        print(f"  !! missing page.{handle}.json")
        return

    title = ACTIVITY_TITLES[handle]
    tag = handle.split("-")[0]

    # The hero eyebrow carries no running number. These pages are reached from a
    # menu and from each other, not read as a numbered sequence, so "01 —" in
    # front of the activity name was counting something the visitor never sees.
    # The setting stays in the schema, so it can be put back from the editor.
    hero_settings = data["sections"]["hero"]["settings"]
    hero_settings.pop("index_label", None)

    # The eyebrow names this activity. Three of the four pages had inherited the
    # homepage's own label, "Shop by activity", which said nothing about the page
    # it was on and only read as filler once the number was gone.
    hero_settings["eyebrow"] = (
        activity_cards_from_home().get(handle, {}).get("title") or ACTIVITY_TITLES[handle]
    )

    # Trim siblings to the two the sitemap allows.
    sib = data["sections"].get("siblings")
    if sib:
        cards = activity_cards_from_home()
        wanted = SIBLINGS[handle]
        keep, blocks = [], {}
        for bk in sib.get("block_order", []):
            b = sib["blocks"][bk]
            link = (b.get("settings") or {}).get("link", "")
            if any(f"/pages/{w}" == link for w in wanted):
                keep.append(bk)
                blocks[bk] = b
        # A link that pointed at a retired handle is repointed rather than lost.
        if len(keep) < 2:
            for w in wanted:
                if not any((blocks[k]["settings"].get("link") == f"/pages/{w}") for k in keep):
                    nk = f"sib-{w}"
                    blocks[nk] = {
                        "type": "card",
                        "settings": {
                            "title": cards.get(w, {}).get("title") or ACTIVITY_TITLES[w],
                            "body": cards.get(w, {}).get("body", ""),
                            "link": f"/pages/{w}",
                        },
                    }
                    keep.append(nk)
        sib["blocks"], sib["block_order"] = blocks, keep[:2]

        # Restate every card from the homepage, so a row cannot mix two
        # spellings of the same activity or show a card with no body.
        for bk in sib["block_order"]:
            st = sib["blocks"][bk].setdefault("settings", {})
            target = (st.get("link") or "").rstrip("/").split("/")[-1]
            src = cards.get(target)
            if src:
                if src["title"]:
                    st["title"] = src["title"]
                if src["body"]:
                    st["body"] = src["body"]

        # The column count has to match the two-sibling rule. Left at 4 the two
        # cards sat in the left half of the row with a hole beside them.
        sib["settings"]["columns"] = len(sib["block_order"])

    order = data["order"]

    # Insert in sitemap order: breadcrumb first, then buy widget and reviews
    # after the hero, then guides before the siblings.
    new_sections = dict(data["sections"])
    new_sections["breadcrumb"] = breadcrumb(handle, title)
    new_sections["buy"] = buy_widget_from_home()
    new_sections["reviews"] = review_module()
    new_sections["faq"] = faq_from_home()
    new_sections["guides"] = related_guides(tag)

    out = ["breadcrumb", "hero"]
    if "specs" in order:
        out.append("specs")
    # 3.5: the buy widget takes the position; siblings move below.
    out += ["buy", "reviews"]
    out += [k for k in order if k not in ("hero", "specs", "siblings", "close")]
    out += ["faq", "guides", "siblings", "close"]
    # Keep only keys that exist, preserving order and dropping duplicates.
    seen, final = set(), []
    for k in out:
        if k in new_sections and k not in seen:
            seen.add(k)
            final.append(k)

    save(handle, {"sections": new_sections, "order": final})
    print(f"  page.{handle}: {len(final)} sections")


# ------------------------------------------------------------------ other pages


def add_breadcrumbs_and_reviews():
    for handle, parent in BREADCRUMBS.items():
        if handle in ACTIVITIES:
            continue  # handled by build_activity
        data = load(handle)
        if not data:
            print(f"  !! no template for {handle}")
            continue
        if "breadcrumb" in data["sections"]:
            continue
        title = ACTIVITY_TITLES.get(handle) or handle.replace("-", " ").capitalize()
        # Prefer the page hero's heading as the breadcrumb leaf where there is one.
        for k in data["order"]:
            st = data["sections"][k].get("settings", {})
            if data["sections"][k]["type"] in ("page-hero", "centre-note") and st.get("heading"):
                title = None  # let the section fall back to the real page title
                break
        data["sections"]["breadcrumb"] = breadcrumb(handle, title)
        data["order"] = ["breadcrumb"] + data["order"]
        save(handle, data)
        print(f"  page.{handle}: + breadcrumb")

    for handle in REVIEW_PAGES:
        if handle in ACTIVITIES:
            continue
        data = load(handle)
        if not data or "reviews" in data["sections"]:
            continue
        data["sections"]["reviews"] = review_module()
        # Before the closing section where there is one, otherwise at the end.
        tail = data["order"][-1]
        if data["sections"][tail]["type"] in ("closing-cta", "centre-note"):
            data["order"].insert(len(data["order"]) - 1, "reviews")
        else:
            data["order"].append("reviews")
        save(handle, data)
        print(f"  page.{handle}: + review module")


def build_reviews_page():
    """Sitemap 12. The review module renders nothing while it holds no reviews,
    which is 12.3's omission rule enforced in code — so with the placeholder
    intro that was all this page had, and it read as unfinished.

    A reviews page with no reviews still has a job: say there are none, say why,
    and state the standard the feed will be held to when it fills. That is
    checkable now, where a fabricated rating would not be. The module and its
    filters stay in place and appear the moment real reviews are entered.
    """
    data = load("reviews") or {"sections": {}, "order": []}

    data["sections"]["breadcrumb"] = breadcrumb("reviews", None)

    data["sections"]["intro"] = note(
        heading_tag="h1", heading_size="h2", hide_rule=True,
        eyebrow="Reviews",
        heading="There are none yet, and we are not going to invent any.",
        body="<p>HydroSox is new. A rating with nothing behind it is worth nothing, and a feed of five-star reviews with no negatives in it reads as filtered to exactly the person who is reading carefully.</p>")

    data["sections"]["standard"] = items([
        ("Verified buyers only",
         "<p>A review has to come from an order. No unverified submissions, and no reviews written by us.</p>"),
        ("Negative reviews stay up",
         "<p>Published alongside the rest, unedited. If the socks disappoint someone, that belongs here.</p>"),
        ("Filterable by activity and rating",
         "<p>A commuter's experience is more useful to another commuter than an overall average is. The filters go live with the feed.</p>"),
        ("The aggregate is the real one",
         "<p>Whatever the average turns out to be is what gets printed, including the rating and the total volume in one line.</p>"),
    ], numbered=True, heading="The standard this feed will be held to",
        head_note="<p>Set out now, while it costs us nothing to promise, so it can be held against us later.</p>")

    data["sections"]["meanwhile"] = items([
        ("The membrane is named",
         "<p>Porelle®, licensed from a third party. You can look it up, which is more than an unnamed laminate offers.</p>"),
        ("The limits are published",
         "<p>What the socks will not do is on the homepage. No competitor in this category publishes that.</p>"),
        ("The company is named",
         "<p>UK registered, with the address and phone number on every page rather than behind a contact form.</p>"),
    ], color_scheme="wash", heading="What you can check instead",
        head_note="<p>Reviews are one kind of evidence. Until there are some, here is the kind that does not depend on volume.</p>")

    # 12.3-12.5. Renders nothing until real reviews exist, then brings the
    # aggregate, the feed and the filters with it. This page owns the schema.
    data["sections"]["feed"] = {
        "type": "review-module",
        "settings": {
            "layout": "feed",
            "color_scheme": "paper",
            "pace": "base",
            "show_aggregate": True,
            "show_filters": True,
            "emit_schema": True,
            "eyebrow": "Reviews",
            "heading": "What people say after a wet day.",
        },
    }

    data["sections"]["buy"] = buy_widget_from_home()

    data["order"] = ["breadcrumb", "intro", "standard", "meanwhile", "feed", "buy"]
    save("reviews", data)
    print("  page.reviews: intro + standard + what to check instead + feed + buy widget")


def build_forms():
    """Sitemap 21.3, 22.4 and 23.5 — three forms, one section type."""
    specs = {
        "contact": dict(
            heading="Send us a message.",
            lede="<p>We answer every message ourselves. If the answer is already written down, the routes below are faster than waiting for us.</p>",
            submit="Send message",
            choices=["An order I have placed", "Sizing or fit", "Wudu and masah", "Trade or wholesale", "Press", "Something else"],
            fields=[
                ("Order number", False, "text", "If your message is about an order, this saves us asking.", False),
                ("Message", True, "text", "", True),
            ],
        ),
        "partner-with-us": dict(
            heading="Tell us about your business.",
            lede="<p>We are selective rather than exclusive. The more of this you fill in, the faster we can tell you whether we are a fit.</p>",
            submit="Send enquiry",
            choices=["Retail stockist", "Online reseller", "Workwear or trade supply", "Islamic retail", "Distributor"],
            fields=[
                ("Company name", False, "text", "", True),
                ("Website", False, "url", "", False),
                ("Telephone", False, "tel", "", False),
                ("Where you sell", True, "text", "Stores, marketplaces, or the regions you cover.", True),
                ("Indicative first order", False, "number", "In pairs. An estimate is fine.", False),
                ("Anything else", True, "text", "", False),
            ],
        ),
        "press": dict(
            heading="Press enquiries.",
            lede="<p>We can supply product for review, photography, and figures we are able to stand behind. We do not supply claims we cannot evidence.</p>",
            submit="Send enquiry",
            choices=["Product for review", "Interview or comment", "Imagery and assets", "Fact check"],
            fields=[
                ("Publication", False, "text", "", True),
                ("Website", False, "url", "", False),
                ("Deadline", False, "text", "So we know what is realistic.", False),
                ("What you need", True, "text", "", True),
            ],
        ),
    }

    for handle, spec in specs.items():
        data = load(handle) or {"sections": {}, "order": []}
        blocks, order_b = {}, []
        for i, label in enumerate(spec["choices"]):
            k = f"c{i + 1}"
            blocks[k] = {"type": "choice", "settings": {"label": label}}
            order_b.append(k)
        for i, (label, multi, itype, help_, req) in enumerate(spec["fields"]):
            k = f"f{i + 1}"
            blocks[k] = {
                "type": "field",
                "settings": {
                    "label": label,
                    "multiline": multi,
                    "rows": 5,
                    "input_type": itype,
                    "help": help_,
                    "required": req,
                },
            }
            order_b.append(k)

        data["sections"]["form"] = {
            "type": "enquiry-form",
            "settings": {
                "color_scheme": "paper",
                "pace": "base",
                "anchor_id": "enquiry",
                "eyebrow": "Get in touch",
                "heading": spec["heading"],
                "lede": spec["lede"],
                "submit_label": spec["submit"],
                "consent_note": "<p>We use these details to answer your message and nothing else. See our <a href=\"/policies/privacy-policy\">privacy policy</a>.</p>",
            },
            "blocks": blocks,
            "block_order": order_b,
        }
        if handle in BREADCRUMBS:
            data["sections"]["breadcrumb"] = breadcrumb(handle, None)
        order = [k for k in data["order"] if k not in ("form", "breadcrumb")]
        head = ["breadcrumb"] if handle in BREADCRUMBS else []
        # The form goes before any closing section, which is a way out.
        if order and data["sections"][order[-1]]["type"] in ("closing-cta", "centre-note"):
            data["order"] = head + order[:-1] + ["form", order[-1]]
        else:
            data["order"] = head + order + ["form"]
        save(handle, data)
        print(f"  page.{handle}: + enquiry form ({len(order_b)} blocks)")


def build_blog_and_collection():
    save(
        "blog.guides",
        {
            "sections": {
                "main": {
                    "type": "main-blog",
                    "settings": {
                        "color_scheme": "paper",
                        "pace": "base",
                        "per_page": 9,
                        "eyebrow": "Guides",
                        "heading": "Written for people who get wet.",
                        "lede": "<p>Straight answers about waterproofing, sizing, care and masah. No filler, and nothing that contradicts what the product pages say.</p>",
                        "empty_note": "The first guides are being written. Nothing has been published here as a placeholder.",
                        "show_tags": True,
                        "all_label": "Everything",
                    },
                },
                "buy": buy_widget_from_home(),
            },
            "order": ["main", "buy"],
        },
    )
    print("  blog.guides: intro + tags + grid + buy widget")

    save(
        "collection",
        {
            "sections": {
                "main": {
                    "type": "main-collection",
                    "settings": {
                        "color_scheme": "paper",
                        "per_page": 12,
                        "supporting": "<p>One sock, made properly, in four colourways and four sizes. If you are choosing between activities rather than products, the activity pages explain which conditions each one is written for.</p>",
                    },
                }
            },
            "order": ["main"],
        },
    )
    print("  collection: + supporting content")


def build_article():
    """Compose the guide article template — sitemap page 16, sections 16.2-16.8.

    16.6 is mandatory: "an article cannot publish without this link and one PDP
    link". The activity link is resolved from the article's own tags by
    main-article, so the routing table lives here once rather than being
    retyped per article; the PDP link is the inline buy widget at 16.5.

    16.5 asks for the buy widget "after the first substantive section". A JSON
    template can only place sections around the body, not inside it, so it sits
    directly after the body — the nearest structural equivalent.
    """
    save(
        "article",
        {
            "sections": {
                "breadcrumb": {
                    "type": "breadcrumb",
                    "settings": {
                        "color_scheme": "paper",
                        "home_label": "Home",
                        "parent_label": "Guides",
                        "parent_url": "/blogs/guides",
                    },
                },
                "main": {
                    "type": "main-article",
                    "blocks": {
                        f"route_{handle.replace('-', '_')}": {
                            "type": "activity_link",
                            "settings": {
                                "tag": tag,
                                "label": label,
                                "url": f"/pages/{handle}",
                                "note": note,
                            },
                        }
                        for tag, handle, label, note in ARTICLE_ROUTES
                    },
                    "block_order": [
                        f"route_{handle.replace('-', '_')}"
                        for _, handle, _, _ in ARTICLE_ROUTES
                    ],
                    "settings": {
                        "color_scheme": "paper",
                        "show_author": False,
                        "kicker_divider": "·",
                        "image_aspect": "16 / 9",
                        "back_label": "All guides",
                        "route_eyebrow": "Made for this",
                    },
                },
                "buy": buy_widget_from_home(),
                "related": related_guides(""),
                "signup": {
                    "type": "newsletter-offer",
                    "settings": {
                        "color_scheme": "wash",
                        "eyebrow": "£5 off your first pair",
                        "heading": "Get the code before the weather turns.",
                        "body": "<p>Applies to a single pair. The two-pair saving is already built into the price.</p>",
                        "field_label": "Email address",
                        "submit_label": "Send my code",
                        "success_message": "Thanks. Your code is on its way.",
                        "tag": "newsletter",
                        "note": '<p>One email to set you up, then only when there is something worth sending. Unsubscribe any time. See our <a href="/policies/privacy-policy">privacy policy</a>.</p>',
                    },
                },
            },
            "order": ["breadcrumb", "main", "buy", "related", "signup"],
        },
    )
    print(f"  article: breadcrumb + body + buy widget + related + capture")
    print(f"           {len(ARTICLE_ROUTES)} activity tag routes")

    # The generic blog. /blogs/guides has its own composed template; this is
    # what any other blog falls back to, so it should not be a bare stub.
    save(
        "blog",
        {
            "sections": {
                "main": {
                    "type": "main-blog",
                    "settings": {
                        "color_scheme": "paper",
                        "pace": "base",
                        "per_page": 9,
                        "show_tags": False,
                        "empty_note": "Nothing has been published here yet.",
                    },
                }
            },
            "order": ["main"],
        },
    )
    print("  blog: generic fallback index")


def guide_rows_from_home():
    """The size bands, read out of the homepage buy widget.

    Sitemap 13.2 wants the overlay and this page to agree. Reading the blocks
    rather than restating them means they cannot drift apart.
    """
    home = load("index")
    buy = home["sections"]["buy"]
    rows, notes = [], []
    for key in buy.get("block_order", []):
        b = buy["blocks"][key]
        if b["type"] == "guide_row":
            st = b["settings"]
            rows.append((st.get("size", ""), st.get("foot_length", ""), st.get("uk_shoe", "")))
        elif b["type"] == "guide_note":
            notes.append((b["settings"].get("label", ""), b["settings"].get("body", "")))
    return rows, notes


def limits_from_home():
    """The honest-limits rows, read out of the homepage."""
    home = load("index")
    lim = home["sections"]["limits"]
    out = []
    for key in lim.get("block_order", []):
        st = lim["blocks"][key]["settings"]
        out.append((st.get("heading", ""), st.get("body", "")))
    return out


def layers_from_home():
    """The three construction layers, read out of the homepage."""
    home = load("index")
    con = home["sections"]["construction"]
    out = []
    for key in con.get("block_order", []):
        b = con["blocks"][key]
        if b["type"] != "layer":
            continue
        st = b["settings"]
        out.append((st.get("heading", ""), st.get("role", ""), st.get("body", "")))
    return out


def rich(text):
    """Wrap plain text for a richtext setting.

    Shopify refuses a template whose richtext value is not inside a block-level
    tag, and keeps the previously deployed version live — so the page silently
    stays stale. Values read out of a textarea setting arrive as bare text, and
    this is where they get their <p>.
    """
    if not text:
        return text
    stripped = text.strip()
    if stripped.startswith(("<p", "<ul", "<ol", "<h", "<blockquote", "<div")):
        return stripped
    return f"<p>{stripped}</p>"


def items(pairs, numbered=False, **settings):
    """A content-columns section from (title, body) pairs."""
    blocks, order = {}, []
    for i, (title, body) in enumerate(pairs, 1):
        key = f"i{i}"
        blocks[key] = {"type": "item", "settings": {"title": title, "body": rich(body)}}
        order.append(key)
    base = {"color_scheme": "paper", "layout": "list", "numbered": numbered}
    base.update(settings)
    return {"type": "content-columns", "settings": base, "blocks": blocks, "block_order": order}


def build_support_pages():
    """Size guide, care, FAQ and technology — sitemap pages 13, 14, 18 and 10.

    Each carried a single placeholder note while the sitemap asks for four to
    seven sections. The content for all four already exists elsewhere in the
    theme, so these are composed from it rather than written: the size bands
    come out of the buy widget, the limits and the layers out of the homepage.
    Nothing here is invented, and where the sitemap forbids a figure the
    section states the mechanism instead.
    """
    rows, notes = guide_rows_from_home()

    # 13. Size guide
    table = [
        (size, f"<p>Foot length {length}. Fits {shoe}.</p>")
        for size, length, shoe in rows
    ]
    save("size-guide", {
        "sections": {
            "intro": {"type": "centre-note", "settings": {
                "color_scheme": "paper", "heading_tag": "h1", "heading_size": "h2",
                "eyebrow": "Size guide", "heading": "Measure the foot, not the shoe.",
                "body": "<p>Shoe sizing is not consistent between brands, and the foot length is what actually has to fit. Four bands cover UK 3 to UK 14.</p>"}},
            "chart": items(table, heading="The four bands",
                           head_note="<p>The same measurements appear in the size guide that opens over the buy widget. They are read from one place, so the two cannot disagree.</p>",
                           row_density="compact"),
            "howto": items(notes, heading="Measuring and choosing"),
            "buy": buy_widget_from_home(),
        },
        "order": ["intro", "chart", "howto", "buy"],
    })
    print(f"  page.size-guide: intro + {len(table)} bands + {len(notes)} notes + buy widget")

    # 14. Care and washing
    limits = limits_from_home()
    wash = [
        ("Wash cool", "<p>A laminate fails from heat long before it fails from age. Cool wash, gentle cycle.</p>"),
        ("Turn them inside out", "<p>It puts the knit face, not the lining, against the drum.</p>"),
        ("No fabric softener", "<p>Softener coats the pores the membrane breathes through. Once they are clogged the sock still keeps water out, but it stops moving vapour.</p>"),
        ("No bleach", "<p>It attacks the laminate, not just the colour.</p>"),
        ("Air dry", "<p>Away from a radiator. A membrane does not need heat to dry, and heat is the thing most likely to end it.</p>"),
        ("Never tumble dry or iron", "<p>Both are heat, applied directly.</p>"),
    ]
    damage = [(h, b) for h, b in limits if "indestructible" in h.lower() or "breathable" in h.lower()]
    save("care-and-washing", {
        "sections": {
            "intro": {"type": "centre-note", "settings": {
                "color_scheme": "paper", "heading_tag": "h1", "heading_size": "h2",
                "eyebrow": "Care and washing", "heading": "What shortens the life of a membrane.",
                "body": "<p>These are washable and meant to be washed. Almost everything that ends a waterproof sock early is heat, softener or abrasion — not wear.</p>"}},
            "wash": items(wash, numbered=True, heading="Washing instructions"),
            "damage": items(damage or limits[:2], color_scheme="wash", heading="What damages the membrane"),
            "life": {"type": "centre-note", "settings": {
                "color_scheme": "paper", "heading_size": "h3", "eyebrow": "Expected lifespan",
                "heading": "We do not publish a figure for this.",
                "body": "<p>We have no wear-test data yet, and a number with nothing behind it is worth nothing. What we can tell you is the mechanism: a membrane ends through abrasion, heat and clogged pores. Wash it cool, keep softener away from it and keep your toenails short, and you are addressing all three.</p>",
                "footnote": rich("When there is real wear-test data it will be published here, including the results that do not flatter us.")}},
            "buy": buy_widget_from_home(),
        },
        "order": ["intro", "wash", "damage", "life", "buy"],
    })
    print(f"  page.care-and-washing: intro + {len(wash)} steps + damage + lifespan + buy widget")

    # 18. FAQ
    faq = faq_from_home(limit=99)
    save("faq", {
        "sections": {
            "intro": {"type": "centre-note", "settings": {
                "color_scheme": "paper", "heading_tag": "h1", "heading_size": "h2",
                "eyebrow": "Questions", "heading": "The things people ask before they buy.",
                "body": "<p>Answered with the same facts as the rest of the site. If an answer here contradicts a product page, the product page is the one that is wrong.</p>"}},
            "questions": faq,
            "still": {"type": "centre-note", "settings": {
                "color_scheme": "wash", "heading_size": "h3",
                "eyebrow": "Still have a question", "heading": "Ask a person.",
                "body": "<p>The phone number and email are published on every page of this site, not held behind a contact form.</p>",
                "cta_label": "Contact us", "cta_url": "/pages/contact"}},
            "buy": buy_widget_from_home(),
        },
        "order": ["intro", "questions", "still", "buy"],
    })
    print(f"  page.faq: intro + {len(faq.get('block_order', []))} questions + contact + buy widget")

    # 10. Technology
    layers = layers_from_home()
    layer_items = [(h, f"<p>{r}.</p>" + b if r else b) for h, r, b in layers]
    wont = [(h, b) for h, b in limits]
    save("technology", {
        "sections": {
            "crumb": breadcrumb("technology", "The technology"),
            "intro": {"type": "centre-note", "settings": {
                "color_scheme": "paper", "heading_tag": "h1", "heading_size": "h2",
                "eyebrow": "The technology", "heading": "The mechanism, not the claim.",
                "body": "<p>“Waterproof” is a word anybody can print on a label. This is what is underneath ours, so you can judge it rather than take our word.</p>"}},
            "membrane": {"type": "content-columns", "settings": {
                "color_scheme": "paper", "layout": "prose", "eyebrow": "The membrane",
                "heading": "Porelle® is not a name we invented.",
                "prose": "<p>The waterproof layer is Porelle®, a licensed third-party waterproof-breathable membrane. That distinction matters more than it sounds: a membrane you can look up is a membrane someone else has to stand behind. Water cannot get through it; vapour from the foot can. It is PFOA free.</p><p>Brands that do not name their membrane are asking you to trust an unnamed laminate. We would rather you checked ours.</p>"}},
            "layers": items(layer_items, numbered=True, color_scheme="wash",
                            heading="Three layers, and what each one is for"),
            "testing": {"type": "centre-note", "settings": {
                "color_scheme": "paper", "heading_size": "h3",
                "eyebrow": "How this is tested", "heading": "We publish no test figures yet.",
                "body": "<p>Independent test data is the only kind worth printing, and we do not have it yet. Rather than quote a hydrostatic head or a breathability rating we cannot evidence, we name the membrane and let you look it up.</p>",
                "footnote": rich("When independent figures exist they will be published here with the name of whoever produced them.")}},
            "wont": items(wont, color_scheme="blue", heading="What it will not do",
                          head_note="<p>Every brand tells you what their socks do. This is the other half.</p>"),
            "activities": {"type": "link-cards", "settings": {
                "color_scheme": "paper", "columns": len(ACTIVITIES), "numbered": False,
                "eyebrow": "Built for", "heading": "Where this matters."},
                "blocks": {
                    f"c{i}": {"type": "card", "settings": {
                        "title": ACTIVITY_TITLES[a], "link": f"/pages/{a}"}}
                    for i, a in enumerate(ACTIVITIES, 1)},
                "block_order": [f"c{i}" for i in range(1, len(ACTIVITIES) + 1)]},
            "buy": buy_widget_from_home(),
        },
        "order": ["crumb", "intro", "membrane", "layers", "testing", "wont", "activities", "buy"],
    })
    print(f"  page.technology: intro + membrane + {len(layer_items)} layers + testing + limits + activities + buy")


# ------------------------------------------------------- support and content

def note(**s):
    base = {"color_scheme": "paper"}
    base.update(s)
    return {"type": "centre-note", "settings": base}


def cards(entries, **s):
    """link-cards from (title, body, link) triples."""
    blocks, order = {}, []
    for i, e in enumerate(entries, 1):
        title, body, link = (e + (None,))[:3] if len(e) < 3 else e
        st = {"title": title, "body": body}
        if link:
            st["link"] = link
        blocks[f"c{i}"] = {"type": "card", "settings": st}
        order.append(f"c{i}")
    base = {"color_scheme": "paper", "columns": 3, "numbered": False}
    base.update(s)
    return {"type": "link-cards", "settings": base, "blocks": blocks, "block_order": order}


def closing(**s):
    base = {"color_scheme": "ink", "show_rule": False}
    base.update(s)
    return {"type": "closing-cta", "settings": base}


def company_rows(**s):
    base = {
        "color_scheme": "wash",
        "eyebrow": "Reach a person",
        "heading": "Who you are dealing with.",
        "lede": "<p>Published here rather than buried in a policy page. The phone number and email are answered by people, not a form queue.</p>",
        "link_label": "",
        "link_url": "",
    }
    base.update(s)
    return {
        "type": "company-details",
        "settings": base,
        "blocks": {
            "d1": {"type": "row", "settings": {"label": "Company", "kind": "text", "value": "HydroSox, UK registered"}},
            "d2": {"type": "row", "settings": {"label": "Registered address", "kind": "address"}},
            "d3": {"type": "row", "settings": {"label": "Phone", "kind": "tel"}},
            "d4": {"type": "row", "settings": {"label": "Email", "kind": "email"}},
        },
        "block_order": ["d1", "d2", "d3", "d4"],
    }


# What is settled, and what is honestly not, on the delivery side. Stated once
# here because four pages need to agree with each other and with the policy.
DELIVERY_SETTLED = [
    ("Free on two pairs or more",
     "<p>The threshold sits at the two-pair price, so the saving and the free delivery arrive together.</p>"),
    ("On a single pair, delivery is charged",
     "<p>The exact amount is shown at checkout before you pay. You are never charged a delivery cost you have not seen.</p>"),
    ("Dispatched from the United Kingdom",
     "<p>UK company, UK stock. Nothing is drop-shipped from elsewhere.</p>"),
    ("No delivery speed is promised",
     "<p>Deliberately. We will not print a next-day promise that confirmed stock cannot support, so no speed appears anywhere on this site until it can.</p>"),
]

DELIVERY_OPEN = [
    ("Dispatch cut-off", "<p>Being confirmed against stock.</p>"),
    ("Carrier and transit time", "<p>Being confirmed.</p>"),
    ("Tracking", "<p>Whether a tracking link is sent is being confirmed.</p>"),
    ("Outside the UK", "<p>Destinations and whether duties are collected at checkout are being confirmed.</p>"),
]


def build_content_pages():
    """The pages the sitemap describes but that were still single placeholders.

    Everything here is built from facts the site already states or from UK
    statute. Where the sitemap forbids invention — a founder's name, a warranty
    term, a delivery date, masah guidance — the page says plainly that it is not
    settled yet and points at what is. That is the honest version of a
    placeholder: real structure, real detail where it exists, and no filler.
    """

    # 24. Shipping and delivery
    save("shipping-and-delivery", {
        "sections": {
            "crumb": breadcrumb("shipping-and-delivery", "Shipping and delivery"),
            "intro": note(heading_tag="h1", heading_size="h2", hide_rule=True,
                eyebrow="Shipping and delivery",
                heading="What is settled, and what is not.",
                body="<p>Everything below is either already true at checkout or openly unfinished. Nothing in between.</p>"),
            "settled": items(DELIVERY_SETTLED, heading="Settled today"),
            "open": items(DELIVERY_OPEN, color_scheme="blue", heading="Still being confirmed",
                head_note="<p>These are the questions people ask most, and we would rather say we do not know yet than guess.</p>"),
            "policy": note(color_scheme="wash", heading_size="h3",
                eyebrow="The formal version",
                heading="The shipping policy is the binding text.",
                body="<p>This page explains it. The policy states it.</p>",
                cta_label="Read the shipping policy", cta_url="/policies/shipping-policy",
                link_label="Returns and refunds", link_url="/pages/returns-and-refunds"),
            "buy": buy_widget_from_home(),
        },
        "order": ["crumb", "intro", "settled", "open", "policy", "buy"],
    })
    print("  page.shipping-and-delivery: 4 sections + buy widget")

    # 25. Returns and refunds
    save("returns-and-refunds", {
        "sections": {
            "crumb": breadcrumb("returns-and-refunds", "Returns and refunds"),
            "intro": note(heading_tag="h1", heading_size="h2", hide_rule=True,
                eyebrow="Returns and refunds",
                heading="Fourteen days, no reason needed.",
                body="<p>Your statutory rights are the floor here, not the ceiling. Nothing on this page reduces them.</p>"),
            "how": items([
                ("Tell us within 14 days",
                 "<p>Fourteen days from the day the parcel arrives. Email or phone us — a clear statement that you are cancelling is enough, there is no form to find.</p>"),
                ("Send them back within 14 more",
                 "<p>Unworn, in the original packaging, with any seal intact. You may inspect them as you would in a shop.</p>"),
                ("Refunded within 14 days of arrival",
                 "<p>The price plus the standard outbound delivery charge if you paid one, back to the card you used.</p>"),
            ], numbered=True, heading="Changing your mind"),
            "faulty": items([
                ("Within 30 days, reject and get a full refund",
                 "<p>Under the Consumer Rights Act 2015 goods must be of satisfactory quality, fit for purpose and as described.</p>"),
                ("After 30 days, repair or replacement",
                 "<p>And a refund or price reduction if that does not resolve it. We do not charge for returning faulty goods.</p>"),
            ], color_scheme="wash", heading="If something is actually wrong with them"),
            "not": items([
                ("Normal wear is not a fault",
                 "<p>A membrane ends through abrasion, heat and clogged pores. That is wear, not a defect.</p>"),
                ("Washing against the care instructions",
                 "<p>Fabric softener, bleach, a hot wash or a tumble dryer will end a membrane early. The care page explains why.</p>"),
            ], color_scheme="blue", heading="What is not covered"),
            "policy": note(color_scheme="wash", heading_size="h3",
                eyebrow="The formal version",
                heading="The refund policy is the binding text.",
                body="<p>Who pays return postage and the return address are stated there.</p>",
                cta_label="Read the refund policy", cta_url="/policies/refund-policy",
                link_label="Care and washing", link_url="/pages/care-and-washing"),
            "buy": buy_widget_from_home(),
        },
        "order": ["crumb", "intro", "how", "faulty", "not", "policy", "buy"],
    })
    print("  page.returns-and-refunds: 5 sections + buy widget")

    # 26. Warranty
    save("warranty", {
        "sections": {
            "crumb": breadcrumb("warranty", "Warranty"),
            "intro": note(heading_tag="h1", heading_size="h2", hide_rule=True,
                eyebrow="Warranty",
                heading="We have not set warranty terms yet.",
                body="<p>Saying so is more useful than a vague promise. Your statutory rights already cover a great deal, and they apply whether or not a brand offers anything on top.</p>",
                footnote="<p>When terms are set they will be published here in full, including what they exclude.</p>"),
            "rights": items([
                ("Satisfactory quality, fit for purpose, as described",
                 "<p>The Consumer Rights Act 2015 requires all three. A sock that is not waterproof is not as described, and that is a fault however long you have had it.</p>"),
                ("Thirty days to reject outright",
                 "<p>A full refund, no repair attempt required.</p>"),
                ("Six months where the fault is presumed ours",
                 "<p>Within six months of delivery a fault is assumed to have been there from the start unless we can show otherwise.</p>"),
            ], numbered=True, heading="What you already have"),
            "fault": items([
                ("A fault", "<p>Delamination, a seam that lets water through, a membrane that leaks in the first weeks of normal use.</p>"),
                ("Wear", "<p>Thinning at the heel or toe over months of use, abrasion inside a boot, damage from toenails or the wrong wash cycle.</p>"),
            ], color_scheme="wash", heading="Fault or wear",
                head_note="<p>The honest line between the two, so you know which conversation you are having.</p>"),
            "contact": company_rows(eyebrow="Something wrong?",
                heading="Tell a person, not a form.",
                lede="<p>Describe what happened and when. We would rather hear it than not.</p>"),
            "buy": buy_widget_from_home(),
        },
        "order": ["crumb", "intro", "rights", "fault", "contact", "buy"],
    })
    print("  page.warranty: 4 sections + contact + buy widget")

    # 27. Track order
    save("track-order", {
        "sections": {
            "crumb": breadcrumb("track-order", "Track order"),
            "intro": note(heading_tag="h1", heading_size="h2", hide_rule=True,
                eyebrow="Track order",
                heading="Ask us and we will look.",
                body="<p>There is no tracking widget on this page yet, because tracking is still being confirmed with the carrier. In the meantime a person will check for you.</p>"),
            "how": items([
                ("Email us the order number",
                 "<p>It is in your confirmation email, and it starts with a hash. We will tell you where the parcel actually is.</p>"),
                ("Or phone during the day",
                 "<p>Quicker if your parcel is due today.</p>"),
                ("Order history, if you made an account",
                 "<p>Guest checkout is the default here, so most orders will not have one. Nothing is hidden behind an account.</p>"),
            ], numbered=True, heading="Three ways to find out"),
            "contact": company_rows(eyebrow="Checking an order",
                heading="Reach us directly.",
                lede="<p>Have the order number to hand and this takes one message.</p>"),
            "next": note(color_scheme="wash", heading_size="h3",
                eyebrow="While you are here",
                heading="Delivery, in plain numbers.",
                body="<p>What is settled and what is not, on the shipping page.</p>",
                cta_label="Shipping and delivery", cta_url="/pages/shipping-and-delivery",
                link_label="Returns and refunds", link_url="/pages/returns-and-refunds"),
        },
        "order": ["crumb", "intro", "how", "contact", "next"],
    })
    print("  page.track-order: 3 sections + contact")

    # 11. How to make masah
    save("how-to-make-masah", {
        "sections": {
            "crumb": breadcrumb("how-to-make-masah", "How to make masah"),
            "intro": note(heading_tag="h1", heading_size="h2", hide_rule=True,
                eyebrow="How to make masah",
                heading="Guidance we will not write ourselves.",
                body="<p>Step-by-step guidance on masah has to be written or reviewed by someone who understands the practice. We are a sock company. Publishing our own version of it would be presumptuous, and getting it subtly wrong would be worse.</p>",
                footnote="<p>This page will carry reviewed guidance, credited to whoever reviewed it. Until then, what we can speak to is the sock.</p>"),
            "conditions": items([
                ("Waterproof", "<p>A Porelle® membrane sealed inside a three-layer knit. Water does not pass through it.</p>"),
                ("Holds its shape", "<p>Structured so it stays as a covering rather than collapsing against the foot.</p>"),
                ("Stays on the foot", "<p>Shaped and close-fitting, so it remains in place in normal use.</p>"),
            ], numbered=True, heading="The three physical properties",
                head_note="<p>These are the properties the masah conditions rest on, and they are ours to state because they are facts about the product rather than rulings.</p>"),
            "scholarly": company_rows(eyebrow="Scholarly questions",
                heading="Ask, and we will say what we know.",
                lede="<p>If you need to know something specific about the construction in order to reach your own judgement, ask and we will answer factually. We will not offer a ruling.</p>"),
            "wudu": note(color_scheme="wash", heading_size="h3",
                eyebrow="The product",
                heading="What is built for this, and what is not certified.",
                body="<p>No certificate has been issued, and the wudu page says so on its face.</p>",
                cta_label="Wudu socks", cta_url="/pages/wudu-socks",
                link_label="How it is built", link_url="/pages/technology"),
            "buy": buy_widget_from_home(),
        },
        "order": ["crumb", "intro", "conditions", "scholarly", "wudu", "buy"],
    })
    print("  page.how-to-make-masah: 4 sections + buy widget")

    # 20. Our partners
    save("our-partners", {
        "sections": {
            "crumb": breadcrumb("our-partners", "Our partners"),
            "intro": note(heading_tag="h1", heading_size="h2", hide_rule=True,
                eyebrow="Our partners",
                heading="Two, and only what we can evidence.",
                body="<p>A partnership is easy to assert on a website and harder to demonstrate. Both are named below; the detail of each arrangement is published once there is something concrete to point at.</p>"),
            "who": items([
                ("The Fair Group",
                 "<p>Named as a partner. The nature and scope of the arrangement is published here once it can be evidenced rather than asserted.</p>"),
                ("Humanity Welfare Trust",
                 "<p>Named as a partner. Same standard: what the relationship actually involves, published when it can be shown.</p>"),
            ], heading="Who we work with"),
            "why": note(color_scheme="wash", heading_size="h3",
                eyebrow="Why so little here",
                heading="Because the alternative is a logo wall.",
                body="<p>Unevidenced partner claims are one of the easiest things to put on a store and one of the least useful to read. This page stays short until it can be specific.</p>"),
            "close": closing(eyebrow="Working with us",
                heading="Trade and press enquiries reach a person.",
                body="<p>No public trade pricing, and no form queue.</p>",
                cta_label="Partner with us", cta_url="/pages/partner-with-us",
                alt_label="Press", alt_url="/pages/press"),
        },
        "order": ["crumb", "intro", "who", "why", "close"],
    })
    print("  page.our-partners: 3 sections + closing")

    # 19. About
    save("about", {
        "sections": {
            "intro": note(heading_tag="h1", heading_size="h2", hide_rule=True,
                eyebrow="About HydroSox",
                heading="A UK company selling one product properly.",
                body="<p>One sock, one page, one price. The interesting part of this business is the membrane and the honesty, not the origin story.</p>"),
            "what": items([
                ("What we sell",
                 "<p>A waterproof sock with a licensed Porelle® membrane sealed inside a three-layer knit, in four colourways and four sizes, at one price that does not change depending on how you arrived.</p>"),
                ("How we talk about it",
                 "<p>Every claim on this site is either checkable or absent. We publish what the product will not do on the homepage, which is the half most brands leave out.</p>"),
                ("Where we are",
                 "<p>A UK registered company with a UK warehouse. The address and phone number are on every page.</p>"),
            ], heading="What there is to say"),
            "gap": items([
                ("Who is behind it",
                 "<p>No founder or team is named on this site yet. That is a real gap, not a stylistic choice, and it will be filled with named people rather than a stock photograph and a mission statement.</p>"),
                ("How the product was developed",
                 "<p>Not written yet. When it is, it will not carry invented timelines or test counts.</p>"),
            ], color_scheme="blue", heading="What is missing, and why we are saying so"),
            "company": company_rows(eyebrow="The company",
                heading="Who you are buying from, in full.",
                lede="<p>If something goes wrong you should know exactly who you are dealing with.</p>"),
            "reviews": review_module("paper"),
            "close": closing(eyebrow="The product",
                heading="Two decisions and a quantity.",
                body="<p>No account needed.</p>",
                cta_label="Buy a pair", cta_url=PRODUCT_URL,
                alt_label="How it is built", alt_url="/pages/technology"),
        },
        "order": ["intro", "what", "gap", "company", "reviews", "close"],
    })
    print("  page.about: 3 sections + company + reviews + closing")


def build_wudu_page():
    """Sitemap page 7. The reference had six sections against nine rows, and
    opened on a centre-note rather than a hero, so it read like a placeholder.

    7.4 is BLOCKING in the sitemap: HydroSox publishes no certificate. That is
    stated on the page's face rather than implied by omission, which is also
    what stops the page carrying paid spend by accident.
    """
    save("wudu-socks", {
        "sections": {
            "crumb": breadcrumb("wudu-socks", "Wudu socks"),
            "hero": {
                "type": "page-hero",
                "settings": {
                    "color_scheme": "ink",
                    "min_height": 40,
                    "eyebrow": "Designed with wudu in mind",
                    "heading": "Built for the three conditions masah turns on.",
                    "lede": "<p>Waterproof, structured to hold its shape, shaped to stay on the foot. Those are physical properties we can state plainly. What they mean for you is yours to judge.</p>",
                    "image_fallback": "hydrosox-colourways.jpg",
                    "image_alt": "Four HydroSox colourways shown together.",
                    "focal_point": "50% 45%",
                    "scrim_vertical": 55,
                    "scrim_horizontal": 35,
                    "cta_label": "Buy a pair",
                    "cta_url": PRODUCT_URL,
                    "link_label": "How it is built",
                    "link_url": "/pages/technology",
                },
            },
            "certificate": items([
                ("No certificate has been issued",
                 "<p>Not by us, not by anyone else, not yet. A brand cannot award itself one, and we are not going to imply approval we do not have by leaving the question unanswered.</p>"),
                ("What we can state instead",
                 "<p>The physical facts: what the membrane is, how the sock is constructed, and how it behaves. Those are checkable. The ruling is not ours to make.</p>"),
            ], color_scheme="blue", heading="On certification",
                head_note="<p>The most important thing on this page, so it comes first.</p>"),
            "conditions": items([
                ("Waterproof",
                 "<p>A licensed Porelle® membrane sealed between two knitted layers. Water does not pass through it. This is the same membrane in every HydroSox pair, not a separate wudu version.</p>"),
                ("Holds its shape",
                 "<p>Structured so it stays a covering over the foot rather than collapsing flat against it when worn.</p>"),
                ("Stays on the foot",
                 "<p>A close, shaped fit that stays in place through normal wear, rather than working loose over a day.</p>"),
            ], numbered=True, heading="The three properties, one at a time"),
            "credentials": items([
                ("The membrane is named and licensed",
                 "<p>Porelle® is a third-party laminate. You can look it up, and someone other than us stands behind it. Compare that with an unnamed waterproof layer.</p>"),
                ("Three layers, each specified",
                 "<p>Lining, membrane, wear face. The construction page sets out what each one is for.</p>"),
                ("PFOA free, stated",
                 "<p>Printed because it is true, not because it tests well.</p>"),
            ], color_scheme="wash", heading="Why this pair rather than another",
                head_note="<p>The differentiator is the named membrane. Everything else in this category tends to be asserted rather than evidenced.</p>"),
            "travel": items([
                ("Long days away from home",
                 "<p>Pilgrimage travel means long days, shared ablution facilities and little chance to dry anything properly. A pair that keeps water out and can be washed cool and air-dried overnight is doing useful work.</p>"),
                ("Multiples, not singles",
                 "<p>Most people buying for travel buy more than one pair. The quantity ladder on this page prices that in rather than treating it as a bulk request.</p>"),
            ], heading="Hajj, Umrah and travel"),
            "buy": buy_widget_from_home(),
            "reviews": review_module("wash"),
            "faq": faq_from_home(limit=4),
            "scholarly": company_rows(
                eyebrow="Scholarly questions",
                heading="Ask about the construction, and we will answer factually.",
                lede="<p>If you need a specific detail about how the sock is made in order to reach your own judgement, ask. We will tell you what it is made of and how it behaves. We will not offer a ruling on your behalf.</p>"),
            "close": closing(
                eyebrow="Whichever reason brought you here",
                heading="The same sock, at the same price.",
                body="<p>One product, one page, one price that does not change depending on how you found us.</p>",
                cta_label="Buy a pair", cta_url=PRODUCT_URL,
                alt_label="How to make masah", alt_url="/pages/how-to-make-masah"),
        },
        "order": ["crumb", "hero", "certificate", "conditions", "credentials",
                  "travel", "buy", "reviews", "faq", "scholarly", "close"],
    })
    print("  page.wudu-socks: hero + certificate + conditions + credentials + travel")
    print("                   + buy widget + reviews + FAQ + contact + closing")


def enrich_form_pages():
    """Sitemap 21 and 22. Both had the form and a closing note but none of the
    surrounding content the sitemap asks for: direct contact details, the
    self-service routes, the trade proposition and the press route.

    The forms themselves are built by build_forms() and are left untouched;
    this only adds what sits around them.
    """
    # 21. Contact
    data = load("contact")
    if data and "details" not in data["sections"]:
        data["sections"]["intro"] = note(
            heading_tag="h1", heading_size="h2", hide_rule=True,
            eyebrow="Contact",
            heading="A phone number, an email, and a person.",
            body="<p>Both are published on every page of this site rather than held behind a form. The form below is for when writing it out is easier.</p>")
        data["sections"]["details"] = company_rows(
            eyebrow="Direct",
            heading="Reach us without the form.",
            lede="<p>Phone during the day, or email any time. Registered address below, for anything that has to be posted.</p>")
        data["sections"]["routes"] = cards([
            ("Size guide", "<p>Measurement-led, four bands, and what to do if you fall between two.</p>", "/pages/size-guide"),
            ("Shipping and delivery", "<p>What is settled and what is still being confirmed.</p>", "/pages/shipping-and-delivery"),
            ("Returns and refunds", "<p>Fourteen days, no reason needed.</p>", "/pages/returns-and-refunds"),
            ("Care and washing", "<p>What shortens the life of a membrane.</p>", "/pages/care-and-washing"),
            ("Track an order", "<p>Ask us and we will look.</p>", "/pages/track-order"),
            ("Questions", "<p>The things people ask before they buy.</p>", "/pages/faq"),
        ], columns=3, color_scheme="wash", eyebrow="Faster than waiting",
            heading="Most answers are already written down.",
            lede="<p>If one of these covers it you do not need to wait for a reply.</p>")
        order = ["intro", "details"] + [k for k in data["order"] if k not in ("intro", "details")] + ["routes"]
        data["order"] = order
        save("contact", data)
        print("  page.contact: + intro + direct details + 6 self-service routes")

    # 22. Partner with us
    data = load("partner-with-us")
    if data and "proposition" not in data["sections"]:
        data["sections"]["intro"] = note(
            heading_tag="h1", heading_size="h2", hide_rule=True,
            eyebrow="Partner with us",
            heading="Trade enquiries, answered by a person.",
            body="<p>No public trade pricing, and no automated tiering. Tell us what you sell and to whom, and we will reply with terms that fit.</p>")
        data["sections"]["proposition"] = items([
            ("One product, properly specified",
             "<p>A named, licensed membrane and a published construction. Easier to sell than an unnamed laminate, and it stands up to a customer asking what is actually in it.</p>"),
            ("A price that does not move",
             "<p>One retail price across every channel, so you are never undercut by our own storefront.</p>"),
            ("Stated limits",
             "<p>We publish what the product will not do. That reduces returns, and it is the reason customers believe the rest of it.</p>"),
            ("UK company, UK stock",
             "<p>Registered address and phone published. Shipped from the UK, not drop-shipped.</p>"),
        ], heading="What you would be stocking")
        data["sections"]["proof"] = review_module("wash")
        data["sections"]["direct"] = company_rows(
            eyebrow="Direct",
            heading="Or skip the form.",
            lede="<p>Phone or email, whichever is quicker for you.</p>")
        data["sections"]["press"] = closing(
            eyebrow="Not a trade enquiry?",
            heading="Press and media go somewhere else.",
            body="<p>Assets, product facts and a named contact.</p>",
            cta_label="Press", cta_url="/pages/press",
            alt_label="Our partners", alt_url="/pages/our-partners")
        order = ["intro", "proposition", "proof"] + \
                [k for k in data["order"] if k not in ("intro", "proposition", "proof")] + \
                ["direct", "press"]
        data["order"] = order
        save("partner-with-us", data)
        print("  page.partner-with-us: + intro + proposition + proof + direct + press route")


def scrub_all_templates():
    """Strip null settings from every template, including ones nothing rebuilt.

    add_breadcrumbs_and_reviews is idempotent — it skips a page that already has
    a breadcrumb — so a template written before scrub() existed kept its null
    and was refused on every upload since. Rewriting only the files that
    actually change keeps this pass quiet once they are clean.
    """
    fixed = []
    for path in sorted(TPL.glob("*.json")):
        raw = path.read_text()
        try:
            data = json.loads(strip_header(raw))
        except json.JSONDecodeError:
            continue
        cleaned = scrub(data)
        if cleaned != data:
            path.write_text(HEADER + json.dumps(cleaned, indent=2) + "\n")
            fixed.append(path.name)
    if fixed:
        for name in fixed:
            print(f"  {name}: null settings removed")
    else:
        print("  no null settings anywhere")


def build_404():
    save(
        "404",
        {
            "sections": {
                "main": {
                    "type": "main-404",
                    "settings": {"show_search": True},
                    "blocks": {
                        "r1": {"type": "route", "settings": {"label": "Shop HydroSox", "note": "One product, four colourways", "link": PRODUCT_URL}},
                        "r2": {"type": "route", "settings": {"label": "Shop by activity", "note": "Hiking, boots, cycling, running", "link": "/pages/hiking-and-walking"}},
                        "r3": {"type": "route", "settings": {"label": "How they are built", "note": "The membrane and the three layers", "link": "/pages/technology"}},
                        "r4": {"type": "route", "settings": {"label": "Guides", "note": "Sizing, care, masah, conditions", "link": "/blogs/guides"}},
                        "r5": {"type": "route", "settings": {"label": "Common questions", "note": "Delivery, returns, warranty", "link": "/pages/faq"}},
                    },
                    "block_order": ["r1", "r2", "r3", "r4", "r5"],
                }
            },
            "order": ["main"],
        },
    )
    print("  404: search + 5 recovery routes")


def add_product_page_extras():
    """Sitemap 2.3, 2.15, 2.17, 2.18 — breadcrumb, reviews, guides, cross-links."""
    data = load("product")
    if not data:
        return
    changed = []
    if "breadcrumb" not in data["sections"]:
        data["sections"]["breadcrumb"] = {
            "type": "breadcrumb",
            "settings": {"color_scheme": "paper", "home_label": "Home"},
        }
        data["order"] = ["breadcrumb"] + data["order"]
        changed.append("breadcrumb")
    if "reviews" not in data["sections"]:
        data["sections"]["reviews"] = review_module()
        data["order"].append("reviews")
        changed.append("review module")
    if "guides" not in data["sections"]:
        data["sections"]["guides"] = related_guides("", scheme="paper")
        data["order"].append("guides")
        changed.append("related guides")
    if changed:
        save("product", data)
        print(f"  product: + {', '.join(changed)}")


def main():
    if not TPL.exists():
        sys.exit("run me from the theme root")

    print("activity pages")
    merge_activity_pages()
    for a in ACTIVITIES:
        build_activity(a)

    print("breadcrumbs and review modules")
    add_breadcrumbs_and_reviews()

    print("reviews page")
    build_reviews_page()

    print("forms")
    build_forms()

    print("blog and collection")
    build_blog_and_collection()

    print("guide article")
    build_article()

    print("support and content pages")
    build_support_pages()

    print("remaining sitemap pages")
    build_content_pages()

    print("wudu page")
    build_wudu_page()

    print("form pages")
    enrich_form_pages()

    print("404")
    build_404()

    print("product page")
    add_product_page_extras()

    # Last, so it also catches anything the builders above emitted.
    print("null scrub")
    scrub_all_templates()

    # Every internal link in every template must point somewhere real.
    handles = {p.stem.replace("page.", "") for p in TPL.glob("page.*.json")}
    bad = set()
    for p in TPL.glob("*.json"):
        for m in re.finditer(r'"(/pages/[a-z0-9-]+)"', p.read_text()):
            h = m.group(1).split("/")[-1]
            if h not in handles:
                bad.add(f"{m.group(1)} (in {p.name})")
    print("\nlink check")
    if bad:
        for b in sorted(bad):
            print(f"  !! dangling {b}")
    else:
        print(f"  every /pages/* link resolves ({len(handles)} page templates)")


if __name__ == "__main__":
    main()
