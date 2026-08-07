#!/usr/bin/env python3
"""
Generates templates/product.json.

The product page is composed from sections the homepage already uses. The buy
widget and the question list are copied from templates/index.json rather than
restated, so the price ladder and the answers cannot drift between the two
pages. The activity cross-links come from the homepage's activity blocks for
the same reason.

Run from the theme root.
"""
import collections
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCT = 'hydrosox-waterproof-socks'


def od(*pairs):
    return collections.OrderedDict(pairs)


def _lead_comments(raw):
    """Length of every leading /* */ block, not just the first.

    The moment the theme editor touches a file, Shopify prepends its own
    banner above whatever header is already there — index.json gained one on
    2026-08-07 and a bare json.load stopped dead at character zero. Same trap
    as every other script that reads a template; same shared cure.
    """
    pos = 0
    while True:
        m = re.match(r"\s*/\*[\s\S]*?\*/\s*", raw[pos:])
        if not m or m.end() == 0:
            return pos
        pos += m.end()


def load_index():
    with open(os.path.join(ROOT, 'templates/index.json')) as fh:
        raw = fh.read()
    return json.loads(raw[_lead_comments(raw):],
                      object_pairs_hook=collections.OrderedDict)


#  Settings that describe a claim about the *page*, not about the section, and so
#  must never ride along on a copy. Structured data is page-scoped: two pages
#  publishing FAQPage for the same questions compete for one rich result.
PAGE_SCOPED = ('emit_schema',)


def copy_section(idx, key, overrides=None):
    """Deep-copies a homepage section, applying setting overrides."""
    src = json.loads(json.dumps(idx['sections'][key]), object_pairs_hook=collections.OrderedDict)
    settings = src.setdefault('settings', collections.OrderedDict())
    for k in PAGE_SCOPED:
        if k in settings:
            settings[k] = False
    if overrides:
        settings.update(overrides)
    return src


def main():
    idx = load_index()
    sections = collections.OrderedDict()
    order = []

    def add(key, rec):
        sections[key] = rec
        order.append(key)

    # Two levels: Home, then the product. Owned here, because this script
    # rebuilds the file from scratch and the sitemap pass only adds a bare
    # breadcrumb when none exists.
    #
    # This reverses brief 3.1, which nested the product under the hub so the two
    # pages could not be mistaken for each other and so hub authority passed
    # down the trail. The client asked for it directly on 2026-08-07: the
    # product is the destination, and a trail that puts a category above it
    # reads as though the reader is still on the way somewhere.
    #
    # The hub is not orphaned by this — it is in the header, the footer and the
    # five use-case pages' own breadcrumbs, which still nest under it.
    add('breadcrumb', od(('type', 'breadcrumb'), ('settings', od(
        ('color_scheme', 'paper'),
        ('home_label', 'Home'),
        ('current_label', 'HydroSox Waterproof Socks'),
    ))))

    # 1 — the buy area stays at the top: the one page where that is correct.
    # The widget renders the product's own title as the H1 on this template,
    # and the lede is the sub-line beneath it. One trust row changes from the
    # homepage copy: Checkout becomes Returns, because guest checkout removes
    # no purchase anxiety and the returns position removes a great deal, at
    # exactly the moment the visitor feels it.
    buy = copy_section(idx, 'buy', od(
        ('anchor_id', 'buy'),
        ('eyebrow', 'Order'),
        ('lede', '<p>Three-layer waterproof socks with a licensed Porelle® '
                 'membrane. Four colours, four sizes, from £20 a pair.</p>'),
    ))
    for block in buy.get('blocks', {}).values():
        if block.get('type') == 'trust' and block['settings'].get('label') == 'Checkout':
            block['settings']['label'] = 'Returns'
            block['settings']['value'] = 'Fourteen days, no reason needed'
    add('buy', buy)

    # 2 — what it is. The heading is the best sentence on the page and stays;
    # the body extends to carry the specification summary the category page
    # must NOT contain.
    # The client's mockup: the section's two callout diagrams side by side
    # under the heading — the sock with its construction labelled, and the
    # layer infographic. Gallery is the layout that runs image blocks across
    # the full width under a band-style header.
    #
    # The pickers ship empty because the two diagram files exist only in the
    # client's mockup so far — they are not in Downloads, the theme's assets or
    # Shopify Files. Until they are chosen in the theme editor the slots render
    # the neutral placeholder; nothing else about the section waits for them.
    add('about', od(('type', 'content-columns'), ('settings', od(
        ('color_scheme', 'wash'),
        ('layout', 'gallery'),
        ('gallery_aspect', '1 / 1'),
        ('anchor_id', 'what-it-is'),
        ('eyebrow', 'What it is'),
        ('heading', 'A membrane, sealed inside a knitted sock.'),
        ('head_note',
         '<p>A crew-height waterproof sock built in three layers: a knitted lining '
         'against the skin, a licensed Porelle® waterproof-breathable membrane in '
         'the middle, and a knitted wear face on the outside. One height, one '
         'construction, four colours, four sizes. The same sock whether you bought '
         'it for a hill, a commute, a shift or for wudu.</p>'),
        ('link_label', 'The three layers, in section'),
        ('link_url', '/pages/technology'),
    )), ('blocks', od(
        ('d1', od(('type', 'image'), ('settings', od(
            ('image_alt', 'HydroSox construction, labelled: ribbed cuff, '
                          'breathable mesh, heel-fit design, non-slip sole, '
                          'seamless toe'))))),
        ('d2', od(('type', 'image'), ('settings', od(
            ('image_alt', 'The three layers in section: waterproof barrier, '
                          'moisture management, comfort and durability'))))),
    )), ('block_order', ['d1', 'd2'])))

    # 3 — the full specification: the section that makes this page distinct
    # from the category hub. Four rows are deliberately absent until the client
    # confirms them — weight, height in centimetres, fibre composition and
    # country of manufacture. A plausible-sounding value in any of them would
    # be a guess published as a fact.
    # The same eleven rows, as collapsible rows — the client's mockup shows
    # the specification folded behind plus-marks rather than laid out in full.
    # Word-for-word the same content; each row's label is the summary and its
    # value the panel. The section's own CTA and help line are suppressed so
    # the fold stays a fold and not another call to action.
    spec_rows = [
        ('Construction', 'Three layers: knitted lining, membrane, knitted wear face.'),
        ('Membrane', 'Porelle®, licensed third-party waterproof-breathable laminate.'),
        ('Height', 'Crew.'),
        ('Sizes', 'S (UK 3–5) · M (UK 6–8) · L (UK 9–11) · XL (UK 12–14).'),
        ('Sized on', 'Foot length in centimetres, not shoe size.'),
        ('Colours', 'Black · Black / Grey · Black / Navy · White.'),
        ('Chemistry', 'PFOA free.'),
        ('Care', 'Cool wash, no softener, no bleach, air dry, never tumble dry or iron.'),
        ('Warranty', 'Statutory rights apply in full; no additional warranty offered at present.'),
        ('Origin', 'UK company, UK warehouse.'),
        ('Price', '£20.00 a pair, £16.00 a pair in a five-pack.'),
    ]
    spec, spec_order = collections.OrderedDict(), []
    for n, (label, value) in enumerate(spec_rows, 1):
        k = 'sp%d' % n
        spec[k] = od(('type', 'question'), ('settings', od(
            ('question', label), ('answer', '<p>%s</p>' % value))))
        spec_order.append(k)
    add('specification', od(('type', 'faq-accordion'), ('settings', od(
        ('color_scheme', 'paper'),
        ('anchor_id', 'specification'),
        ('one_at_a_time', False),
        ('emit_schema', False),
        ('eyebrow', 'Specification'),
        ('heading', 'Everything we can state.'),
        ('lede', '<p>Every figure here is checkable, and every gap is a fact we '
                 'are still confirming rather than a guess. Weight, height in '
                 'centimetres, fibre composition and country of manufacture are '
                 'published the moment they are.</p>'),
        ('help_label', ''),
        ('cta_label', ''),
    )), ('blocks', spec), ('block_order', spec_order)))

    # 4 — colourways, one photograph per colour.
    #
    # The bundled webp is the fallback, not the image itself: `image` is an
    # image_picker that stays empty and wins whenever it is filled, so a
    # merchant can swap any swatch from the theme editor without touching a
    # file, and the theme still ships with the right photograph out of the box.
    #
    # Alt text carries the product keyword deliberately — a colour swatch is one
    # of the few places it still sits naturally. It also describes the shot
    # accurately: these are the socks standing upright and unworn.
    colours, colours_order = collections.OrderedDict(), []
    for n, (name, asset, body) in enumerate([
        ('Black', 'colour-black.webp',
         'The one that disappears under work trousers and inside a boot. The '
         'most forgiving on wet ground.'),
        ('Black / Grey', 'colour-black-grey.webp',
         'The everyday pair. Enough contrast to look deliberate with trainers, '
         'dark enough not to show a muddy day.'),
        ('Black / Navy', 'colour-black-navy.webp',
         'The same idea in a colder tone. Sits better with blue and grey kit.'),
        ('White', 'colour-white.webp',
         'The running and cycling pair. Shows dirt, and is the one most people '
         'photograph.'),
    ], 1):
        k = 'cw%d' % n
        colours[k] = od(('type', 'item'), ('settings', od(
            ('title', name),
            ('body', '<p>%s</p>' % body),
            ('image_fallback', asset),
            ('image_alt', 'HydroSox waterproof socks in %s, crew height, shown '
                          'upright' % name.lower()))))
        colours_order.append(k)
    add('colourways', od(('type', 'content-columns'), ('settings', od(
        ('color_scheme', 'paper'),
        # Stack: the heading centred over the four photograph cards, which
        # gives the page its one centred moment between two side-headed
        # sections. (Cards, never gallery — gallery iterates `image` blocks
        # and would render these `item` blocks as nothing at all.)
        ('layout', 'stack'),
        ('numbered', False),
        ('gallery_aspect', '4 / 5'),
        ('anchor_id', 'colourways'),
        ('eyebrow', 'Colours'),
        ('heading', 'Four, and what each is for.'),
    )), ('blocks', colours), ('block_order', colours_order)))

    # 5 — sizing
    sizing, sizing_order = collections.OrderedDict(), []
    for n, (title, body) in enumerate([
        ('Four bands',
         'S fits UK 3–5, M fits UK 6–8, L fits UK 9–11, XL fits UK 12–14. Each '
         'band is set by foot length in centimetres, published in full on the '
         'size guide.'),
        ('Between two bands',
         'Take the larger one. These are a close, stretchy fit, and a size down '
         'grips the toes and shortens the life of the membrane.'),
        ('Inside a boot or a cycling shoe',
         'They add roughly the bulk of a mid-weight sock. If your footwear is '
         'already tight with a thick sock, it will be tight with these.'),
    ], 1):
        k = 'sz%d' % n
        sizing[k] = od(('type', 'item'), ('settings', od(
            ('title', title), ('body', '<p>%s</p>' % body))))
        sizing_order.append(k)
    add('sizing', od(('type', 'content-columns'), ('settings', od(
        ('color_scheme', 'wash'),
        # The panel treatment: the heading column becomes an ink card and the
        # size-guide link becomes its button — the same shape the hiking fit
        # section uses, because both sections are doing the same job.
        ('layout', 'panel'),
        ('numbered', False),
        ('anchor_id', 'sizing'),
        ('eyebrow', 'Sizing'),
        ('heading', 'Measure the foot, not the shoe.'),
        ('lede', '<p>Shoe sizing is not consistent between brands. Foot length is, '
                 'and it is the thing that actually has to fit inside the sock.</p>'),
        ('link_label', 'Open the size guide'),
        ('link_url', '/pages/size-guide'),
    )), ('blocks', sizing), ('block_order', sizing_order)))

    # 6 — care, returns and warranty, each row linking to the page that owns it
    after, after_order = collections.OrderedDict(), []
    for n, (title, body, label, url) in enumerate([
        ('Washing them will not ruin them. Heat will.',
         'Cool wash, no fabric softener, no bleach, air dry. A membrane fails '
         'from heat, softener and abrasion long before it fails from age.',
         'How to wash them', '/pages/care-and-washing'),
        ('Fourteen days, no reason needed.',
         'Unworn and in the original packaging. Your statutory rights are the '
         'floor here, not the ceiling — the returns page sets out both.',
         'The returns policy', '/policies/refund-policy'),
        ('A fault is not the same as wear.',
         'A seam that lets water through in the first weeks of normal use is a '
         'fault. Thinning at the heel after months is wear. The warranty page '
         'draws the line honestly.',
         'The warranty page', '/pages/warranty'),
    ], 1):
        k = 'ab%d' % n
        after[k] = od(('type', 'item'), ('settings', od(
            ('title', title), ('body', '<p>%s</p>' % body),
            ('link_label', label), ('link_url', url))))
        after_order.append(k)
    add('aftercare', od(('type', 'content-columns'), ('settings', od(
        ('color_scheme', 'ink'),
        # Focus on ink, heading right: the emphasis treatment for the three
        # commitments — washing, returns, warranty — each keeping its link.
        ('layout', 'focus'),
        ('mirror', True),
        ('numbered', False),
        ('anchor_id', 'after-you-buy'),
        ('eyebrow', 'After you buy'),
        ('heading', 'Three things worth knowing now.'),
    )), ('blocks', after), ('block_order', after_order)))

    # 7 — the activity cross-link strip is deliberately absent. The content
    # brief is explicit that this page must not carry activity-specific benefit
    # copy: it answers "is this the right sock, in my size, at this price?",
    # and the case for each use is won on the hub and the four use-case pages.
    # Those pages link here; this one does not link back and restate them.

    # 8 — six product-level questions. None repeats the homepage, the hub or
    # the FAQ page in the same wording — the validator holds that line.
    QUESTIONS = [
        ('Do HydroSox come up big or small?',
         'They run true to the foot-length bands published on the size guide, and '
         'they are a close, stretchy fit rather than a loose one. If you are '
         'between two bands, take the larger — a size down grips the toes and '
         'shortens the life of the membrane.'),
        ('Do HydroSox come in different heights?',
         'No. One height, crew, in every colour and size. A single construction '
         'is the reason the price is £20 rather than £35.'),
        ('Are HydroSox suitable for women?',
         'Yes. The bands run from UK 3, and the sock is unisex. Size on foot '
         'length rather than on the men\'s or women\'s label you are used to.'),
        ('How many pairs do most people buy?',
         'Two or three. They need washing and air drying between wears, and air '
         'drying takes longer than a tumble dryer would, so one pair rarely keeps '
         'up with a daily problem.'),
        ('Can I wash HydroSox in a machine?',
         'Cool wash, gentle cycle, inside out, no fabric softener and no bleach. '
         'Then air dry away from a radiator. Never tumble dry and never iron — '
         'both are heat applied directly to a laminate.'),
        ('What is included when I order?',
         'The pairs you selected, in the colour and size you chose, and nothing '
         'else. No boxes, no printed inserts.'),
    ]
    qs, qs_order = collections.OrderedDict(), []
    for n, (q, a) in enumerate(QUESTIONS, 1):
        k = 'q%d' % n
        qs[k] = od(('type', 'question'), ('settings', od(
            ('question', q), ('answer', '<p>%s</p>' % a))))
        qs_order.append(k)
    add('questions', od(('type', 'faq-accordion'), ('settings', od(
        ('color_scheme', 'paper'),
        ('anchor_id', 'questions'),
        ('one_at_a_time', False),
        ('emit_schema', False),
        ('eyebrow', 'Questions'),
        ('heading', 'About this sock, specifically.'),
        ('help_prefix', 'Something not here?'),
        ('help_label', 'Phone or email us'),
        ('help_link', '/pages/contact'),
    )), ('blocks', qs), ('block_order', qs_order)))

    # 9 — the reviews empty state, stated rather than hidden. The review module
    # after it renders nothing until real reviews exist; this note is why.
    add('reviews_note', od(('type', 'centre-note'), ('settings', od(
        # Blue is this theme's stating-a-limit scheme, and "there are none yet"
        # is exactly that kind of statement. It also hands the page off into
        # the dark footer with one colour step instead of none.
        ('color_scheme', 'blue'),
        ('hide_rule', True),
        ('max_width', 46),
        ('eyebrow', 'Reviews'),
        ('heading', 'There are none yet, and we are not going to invent any.'),
        ('heading_size', 'h3'),
        ('body', '<p>HydroSox is new. A rating with nothing behind it is worth '
                 'nothing, and a feed of five-star reviews with no negatives in it '
                 'reads as filtered to exactly the person who is reading it '
                 'carefully.</p>'),
        ('link_label', 'The standard this feed will be held to'),
        ('link_url', '/pages/reviews'),
    ))))

    tpl = od(('sections', sections), ('order', order))
    path = os.path.join(ROOT, 'templates', 'product.json')
    with open(path, 'w') as fh:
        json.dump(tpl, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    print('wrote templates/product.json  (%d sections: %s)' % (len(order), ', '.join(order)))


if __name__ == '__main__':
    main()
