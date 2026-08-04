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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCT = 'hydrosox-waterproof-socks'


def od(*pairs):
    return collections.OrderedDict(pairs)


def load_index():
    with open(os.path.join(ROOT, 'templates/index.json')) as fh:
        return json.load(fh, object_pairs_hook=collections.OrderedDict)


def copy_section(idx, key, overrides=None):
    """Deep-copies a homepage section, applying setting overrides."""
    src = json.loads(json.dumps(idx['sections'][key]), object_pairs_hook=collections.OrderedDict)
    if overrides:
        src.setdefault('settings', collections.OrderedDict()).update(overrides)
    return src


def activity_cards(idx):
    sec = idx['sections']['activity']
    blocks, order = collections.OrderedDict(), []
    for n, key in enumerate(sec.get('block_order', []), start=1):
        st = sec['blocks'][key].get('settings', {})
        k = 'a%d' % n
        blocks[k] = od(('type', 'card'), ('settings', od(
            ('title', st.get('title', '')),
            ('body', st.get('problem', '')),
            ('link', st.get('link', '')),
        )))
        order.append(k)
    return blocks, order


def main():
    idx = load_index()
    sections = collections.OrderedDict()
    order = []

    def add(key, rec):
        sections[key] = rec
        order.append(key)

    # 1 — the buy area, identical to the homepage's including the price ladder
    add('buy', copy_section(idx, 'buy', od(
        ('anchor_id', 'buy'),
        ('eyebrow', 'What it is'),
        ('heading', 'Two decisions and a quantity.'),
    )))

    # 2 — what the product is, beside the colourway shot
    add('about', od(('type', 'content-columns'), ('settings', od(
        ('color_scheme', 'wash'),
        ('layout', 'media'),
        ('anchor_id', 'what-it-is'),
        ('eyebrow', 'What it is'),
        ('heading', 'A membrane, sealed inside a knitted sock.'),
        ('head_note',
         '<p>A crew-height sock with a waterproof-breathable membrane sealed between two knitted '
         'layers. One height, one construction, sized in bands rather than by gender.</p>'),
        ('link_label', 'The three layers, in section'),
        ('link_url', '/#construction'),
        ('media_fallback', 'hydrosox-colourways.jpg'),
        ('media_alt', 'Four HydroSox colourways standing unsupported'),
    ))))

    # 3 — the detail, folded away so the page stays short
    spec = collections.OrderedDict()
    spec_order = []
    for n, (q, a) in enumerate([
        ('Three-layer construction',
         '<p>A knitted lining next to the skin, a licensed Porelle® waterproof-breathable membrane, '
         'and a knitted outer that takes the abrasion. Bonded, not stitched together.</p>'),
        ('What it will not do',
         '<p>Water over the cuff still gets in, and no waterproof sock behaves otherwise. Every '
         'limit we know about is published rather than left for you to find.</p>'),
        ('Materials and care',
         '<p>A cool machine wash. No fabric conditioner and no tumble dryer — one coats a membrane '
         'and the other degrades it.</p>'),
        ('Shipping, returns and warranty',
         '<p>Free UK delivery on two pairs or more. The full terms are published on their own pages '
         'as each one is confirmed rather than stated early.</p>'),
    ], start=1):
        k = 's%d' % n
        spec[k] = od(('type', 'question'), ('settings', od(('question', q), ('answer', a))))
        spec_order.append(k)

    add('detail', od(('type', 'faq-accordion'), ('settings', od(
        ('color_scheme', 'paper'),
        ('anchor_id', 'detail'),
        ('eyebrow', 'In detail'),
        ('heading', 'The specification, in full.'),
        ('lede', '<p>Folded away so the page stays short. Nothing here contradicts anything above '
                 'it.</p>'),
    )), ('blocks', spec), ('block_order', spec_order)))

    # 4 — where it gets used
    b, o = activity_cards(idx)
    add('activities', od(('type', 'link-cards'), ('settings', od(
        ('color_scheme', 'paper'),
        # One column per activity, so the row comes out even. At 3 the fourth
        # activity dropped onto a second row on its own.
        ('columns', len(o)),
        ('anchor_id', 'activities'),
        ('eyebrow', 'Where it gets used'),
        ('heading', 'Same sock, different problem.'),
    )), ('blocks', b), ('block_order', o)))

    # 5 — the questions, same answers as the homepage
    add('questions', copy_section(idx, 'faq', od(('anchor_id', 'questions'))))

    tpl = od(('sections', sections), ('order', order))
    path = os.path.join(ROOT, 'templates', 'product.json')
    with open(path, 'w') as fh:
        json.dump(tpl, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    print('wrote templates/product.json  (%d sections: %s)' % (len(order), ', '.join(order)))


if __name__ == '__main__':
    main()
