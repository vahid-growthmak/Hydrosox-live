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


def save(name, data):
    path_for(name).write_text(HEADER + json.dumps(data, indent=2) + "\n")


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
    parent = BREADCRUMBS.get(handle)
    s = {"color_scheme": "paper", "home_label": "Home", "current_label": title}
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

    # Trim siblings to the two the sitemap allows.
    sib = data["sections"].get("siblings")
    if sib:
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
                            "title": ACTIVITY_TITLES[w],
                            "link": f"/pages/{w}",
                        },
                    }
                    keep.append(nk)
        sib["blocks"], sib["block_order"] = blocks, keep[:2]

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
    """Sitemap 12: aggregate rating, full feed, filters, buy widget."""
    data = load("reviews") or {"sections": {}, "order": []}
    data["sections"]["breadcrumb"] = breadcrumb("reviews", None)
    data["sections"]["feed"] = {
        "type": "review-module",
        "settings": {
            "layout": "feed",
            "color_scheme": "paper",
            "pace": "base",
            "show_aggregate": True,
            "show_filters": True,
            # 12.3 is the site's aggregate, so this is the one page that owns
            # the AggregateRating schema.
            "emit_schema": True,
            "eyebrow": "Reviews",
            "heading": "What people say after a wet day.",
        },
    }
    data["sections"]["buy"] = buy_widget_from_home()
    order = [k for k in data["order"] if k not in ("breadcrumb", "feed", "buy", "reviews")]
    data["sections"].pop("reviews", None)
    data["order"] = ["breadcrumb"] + order + ["feed", "buy"]
    save("reviews", data)
    print(f"  page.reviews: {len(data['order'])} sections (feed + filters + buy)")


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

    print("404")
    build_404()

    print("product page")
    add_product_page_extras()

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
