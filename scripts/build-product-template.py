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

    # Three levels again: Home › Waterproof socks › the product. The client's
    # v4 content document (8 Aug 2026) states the breadcrumb explicitly,
    # which supersedes their 2026-08-07 request for the two-level trail — the
    # newest instruction wins, and the history stays in git.
    add('breadcrumb', od(('type', 'breadcrumb'), ('settings', od(
        ('color_scheme', 'paper'),
        ('home_label', 'Home'),
        ('parent_label', 'Waterproof socks'),
        ('parent_url', '/pages/waterproof-socks'),
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
        # v4: the sub-line under the product H1, and this page's own line
        # under the quantity ladder. The trust rows arrive correct from the
        # homepage copy — Delivery / Sent from / Returns / Pay with.
        ('lede', '<p>Waterproof socks for hiking, work, cycling, running and '
                 'wudu. Four colours, four sizes, from £20 a pair.</p>'),
        ('ladder_note', 'Two is the most common order. A pair needs a day to '
                        'air dry, so a second one means there is always a dry '
                        'pair ready.'),
    ))
    add('buy', buy)

    # 2 — what it is, rebuilt 2026-08-07 to the client's live mockup
    # (hydrosox-website.vercel.app): the detail-folds dossier. Two captioned
    # diagrams under the heading, then the construction and the limits behind
    # two <details> folds, then the buy button with its back-to-the-top note.
    # Every word below is lifted verbatim from the mockup — including the fold
    # copy the page did not previously carry, and the two intro paragraphs
    # that replaced the old single-paragraph summary.
    #
    # The diagram files themselves were pulled from the mockup's own assets
    # into assets/, so the image_fallback pattern renders them with no editor
    # step; the pickers still win the moment a merchant fills one.
    fold_rows = [
        ('f1', 'fold', {'title': 'Three-layer construction',
                        'note': 'The mechanism behind the waterproof claim, '
                                'layer by layer.'}),
        ('w1', 'row', {'title': 'Inner layer',
                       'body': '<p>A soft knitted lining that moves sweat off the '
                               'foot and stops the membrane sitting against the '
                               'skin.</p>'}),
        # The PFOA clause came off 2026-08-08: the v4 documents remove the
        # claim site-wide until it can be evidenced in writing.
        ('w2', 'row', {'title': 'Porelle® membrane',
                       'body': '<p>A licensed third-party waterproof-breathable '
                               'membrane — not a name we invented. Water cannot '
                               'get in; vapour from the foot can get out.</p>'}),
        ('w3', 'row', {'title': 'Outer layer',
                       'body': '<p>The knitted face that takes the abrasion '
                               'inside a boot or shoe, and holds the sock\'s '
                               'shape when it is not being worn.</p>'}),
        ('f2', 'fold', {'title': 'What it will not do',
                        'note': 'The limits are real and physical. No competitor '
                                'in the mapped set states theirs.'}),
        ('w4', 'row', {'title': 'They are not a boot replacement.',
                       'body': '<p>One component of a system. If your footwear is '
                               'wrong for the ground, this will not fix it.</p>'}),
        ('w5', 'row', {'title': 'Water over the cuff gets in.',
                       'body': '<p>A sock is open at the top. Go deeper than the '
                               'cuff and you are wet, and no waterproof sock '
                               'behaves otherwise.</p>'}),
        ('w6', 'row', {'title': 'They are not indestructible.',
                       'body': '<p>A membrane is a membrane. Abrasion, toenails '
                               'and the wrong wash cycle will eventually end '
                               'one.</p>'}),
        ('w7', 'row', {'title': 'Breathable does not mean dry inside.',
                       'body': '<p>Work hard enough and you will sweat faster '
                               'than any membrane can move vapour. Breathability '
                               'slows that. It does not repeal it.</p>'}),
    ]
    about_blocks = od(
        ('d1', od(('type', 'image'), ('settings', od(
            ('image_fallback', 'diagram-anatomy.jpg'),
            ('image_alt', 'Anatomy diagram of a HydroSox sock labelling the '
                          'ribbed cuff, breathable mesh panel, seamless toe, '
                          'heel-fit shaping and non-slip sole.'),
            ('caption', 'Anatomy — cuff, mesh panel, seamless toe, heel-fit'))))),
        ('d2', od(('type', 'image'), ('settings', od(
            ('image_fallback', 'diagram-layers.jpg'),
            ('image_alt', 'Cutaway diagram of the three-layer fabric: the '
                          'Porelle® waterproof barrier, the moisture-management '
                          'layer, and the breathable inner face.'),
            ('caption', 'The three layers, in section'))))),
    )
    for key, btype, settings in fold_rows:
        about_blocks[key] = od(('type', btype),
                               ('settings', od(*settings.items())))
    add('about', od(('type', 'detail-folds'), ('settings', od(
        ('color_scheme', 'paper'),
        ('anchor_id', 'what-it-is'),
        # v4 words in the mockup's design: the doc's S2 heading and single
        # paragraph carry the section; the diagrams and folds stay.
        ('eyebrow', 'What it is'),
        ('heading', 'What it is'),
        ('head_note',
         '<p>A crew-height waterproof sock built in three layers: a knitted '
         'lining against your skin, a Porelle® waterproof layer in the middle, '
         'and a tough knit on the outside. One height, one build, four colours, '
         'four sizes. The same sock whether you bought it for a hill, a '
         'commute, a shift or for wudu.</p>'),
        # Square, because the diagram files are square: a 4:3 frame either
        # crops the callouts or letterboxes on the sides.
        ('shots_aspect', '1 / 1'),
        ('cta_label', 'Buy a pair'),
        ('cta_url', '#buy'),
        ('cta_note', 'Back to the top of the page — size, colour and quantity '
                     'are all there.'),
    )), ('blocks', about_blocks),
        ('block_order', list(about_blocks.keys()))))

    # 3 — the full specification, reopened 2026-08-07 to the client's live
    # mockup: an open definition table under a band header, not an accordion.
    # The mockup also states four figures the accordion never carried — as
    # "Not published yet" rows, because the honest state of a figure is itself
    # the content. A plausible-sounding value in any of them would be a guess
    # published as a fact, and the flag renders where the value would sit.
    # The mockup's Price row spells out the whole per-pair ladder, matching
    # the verified automatic discounts to the penny.
    # v4, doc-exact at the client's instruction (8 Aug 2026): the ten rows the
    # document lists, in its words and order. The four unconfirmed figures
    # stay absent per the document's own red block — not filled, not flagged.
    spec_rows = [
        ('Build', 'Three layers: knitted lining, waterproof layer, outer knit'),
        ('Waterproof layer', 'Porelle® membrane'),
        ('Height', 'Crew'),
        ('Sizes', 'S (UK 3–5) · M (UK 6–8) · L (UK 9–11) · XL (UK 12–14)'),
        ('Sized by', 'Foot length in centimetres, not shoe size'),
        ('Colours', 'Black · Black / Grey · Black / Navy · White'),
        ('Care', 'Cool wash, no softener, no bleach, air dry, never tumble dry or iron'),
        ('Warranty', 'Your statutory rights apply in full. No extra warranty at present.'),
        ('Sent from', 'Our UK warehouse'),
        ('Price', '£20.00 a pair, or £16.00 each in a five-pack'),
    ]
    spec, spec_order = collections.OrderedDict(), []
    for n, (label, value) in enumerate(spec_rows, 1):
        k = 'sp%d' % n
        spec[k] = od(('type', 'item'), ('settings', od(
            ('title', label), ('body', '<p>%s</p>' % value))))
        spec_order.append(k)
    add('specification', od(('type', 'content-columns'), ('settings', od(
        ('color_scheme', 'wash'),
        ('layout', 'definition'),
        ('numbered', False),
        ('anchor_id', 'specification'),
        ('eyebrow', 'Specification'),
        ('heading', 'The full specification'),
        ('lede', ''),
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
         'Disappears under work trousers and inside a boot. The most forgiving '
         'on wet ground.'),
        ('Black / Grey', 'colour-black-grey.webp',
         'The everyday pair. Enough contrast to look deliberate with trainers, '
         'dark enough to survive a muddy day.'),
        ('Black / Navy', 'colour-black-navy.webp',
         'The same idea in a colder tone. Sits better with blue and grey kit.'),
        ('White', 'colour-white.webp',
         'The running and cycling pair. Shows the dirt, and it’s the one '
         'people photograph.'),
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
        ('heading', 'The four colours'),
    )), ('blocks', colours), ('block_order', colours_order)))

    # 5 — sizing
    sizing, sizing_order = collections.OrderedDict(), []
    for n, (title, body) in enumerate([
        ('Four sizes',
         'S fits UK 3–5, M fits UK 6–8, L fits UK 9–11, XL fits '
         'UK 12–14. Each one is set by foot length in centimetres, '
         'published in full on the size guide.'),
        ('Between two sizes',
         'Take the bigger one. The fit is close and stretchy, so the larger '
         'size will not feel loose — and a size down puts constant tension '
         'on the waterproof layer.'),
        ('Inside boots and cycling shoes',
         'They add roughly the bulk of a mid-weight sock. If your footwear is '
         'already tight with a thick sock, it’ll be tight with these.'),
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
        ('heading', 'Getting the size right'),
        ('lede', '<p>Shoe sizes aren’t consistent between brands. Foot '
                 'length is, and it’s what actually has to fit inside the '
                 'sock.</p>'),
        ('link_label', 'Open the size guide'),
        ('link_url', '/pages/size-guide'),
    )), ('blocks', sizing), ('block_order', sizing_order)))

    # 6 — care, returns and warranty, each row linking to the page that owns it
    after, after_order = collections.OrderedDict(), []
    for n, (title, body, label, url) in enumerate([
        ('Washing them won’t ruin them. Heat will.',
         'Cool wash, no fabric softener, no bleach, air dry. A waterproof '
         'layer fails from heat, softener and rubbing long before it fails '
         'from age.',
         'How to wash them', '/pages/care-and-washing'),
        ('Fourteen days, no reason needed.',
         'Unworn and in the original packaging. Your statutory rights are the '
         'floor here, not the ceiling — the returns page sets out both.',
         # The designed page, as the mockup links it — not the bare /policies/
         # twin, which stays the checkout-linked legal copy of the same text.
         'The returns policy', '/pages/returns-and-refunds'),
        ('A fault isn’t the same as wear.',
         'A seam letting water through in the first few weeks is a fault. '
         'Thinning at the heel after months is wear. The warranty page draws '
         'that line honestly.',
         'The warranty page', '/pages/warranty'),
    ], 1):
        k = 'ab%d' % n
        after[k] = od(('type', 'item'), ('settings', od(
            ('title', title), ('body', '<p>%s</p>' % body),
            ('link_label', label), ('link_url', url))))
        after_order.append(k)
    add('aftercare', od(('type', 'content-columns'), ('settings', od(
        ('color_scheme', 'ink'),
        # The mockup's shape: the heading top-left, then the three commitments
        # as outlined cards running the full width — band on ink already draws
        # cards as bordered boxes, and each card's link holds its bottom edge.
        ('layout', 'band'),
        ('mirror', False),
        ('numbered', False),
        ('anchor_id', 'after-you-buy'),
        ('eyebrow', 'After you buy'),
        ('heading', 'Three things worth knowing now'),
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
         'They run true to the foot-length sizes on the size guide, and '
         'they’re a close stretchy fit rather than a loose one. Between '
         'two sizes, take the bigger — going down grips your toes and is '
         'hard on the waterproof layer.'),
        ('Do they come in different heights?',
         'No. One height, crew, in every colour and size. Having one build is '
         'part of why they’re £20 and not £35.'),
        ('Are they unisex?',
         'Yes. The sizes run from UK 3 to UK 14 and the sock is the same for '
         'everyone. Go by foot length rather than the men’s or '
         'women’s size you’re used to.'),
        ('How many pairs do most people buy?',
         'Two or three. They need washing and air drying between wears, and '
         'air drying takes longer than a tumble dryer, so one pair rarely '
         'keeps up with a daily problem.'),
        ('Can I put them in the washing machine?',
         'Cool wash, gentle cycle, inside out, no fabric softener and no '
         'bleach. Then air dry away from a radiator. Never tumble dry and '
         'never iron — both are heat straight onto the waterproof layer.'),
        ('What arrives in the parcel?',
         'The pairs you chose, in the colour and size you picked. No boxes, '
         'no printed inserts. Keeping the packaging simple is part of what '
         'keeps postage out of the price.'),
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

    # 9 — the reviews empty state, stated rather than hidden. The mockup sets
    # it as a two-column band on the pale blue scheme — heading left, the
    # paragraph bottom-right — and carries no link; the client's mockup is the
    # authority here, and the reviews-standard page stays reachable from the
    # footer. Blue is this theme's stating-a-limit scheme, and "there are none
    # yet" is exactly that kind of statement; it also hands the page off into
    # the dark footer with one colour step instead of none.
    add('reviews_note', od(('type', 'content-columns'), ('settings', od(
        ('color_scheme', 'blue'),
        ('layout', 'list'),
        ('numbered', False),
        ('eyebrow', 'Reviews'),
        ('heading', 'Nothing here yet'),
        ('lede', '<p>No customer has reviewed this product so far, so there is '
                 'nothing to show. Reviews will appear in this space once real '
                 'orders have been placed and used. The standard we will hold '
                 'them to is set out on its own page.</p>'),
        ('link_label', 'The standard we’ll hold this to'),
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
