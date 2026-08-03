#!/usr/bin/env python3
"""
Generates templates/page.<handle>.json for the pages the design deliberately
leaves unwritten.

These are not filler. The reference states the position plainly — "Nothing has
been written here as a placeholder — when it ships it will carry real detail,
not filler" — and each page still gives the reader its title, what it will
cover, a pointer to the nearest thing that is answered, and a way back. Writing
invented shipping windows, warranty terms or return policies into them would be
worse than leaving them honest.

Run from the theme root with the path to the parsed stub content.
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = sys.argv[1] if len(sys.argv) > 1 else 'stubs.json'
PRODUCT_URL = '/products/hydrosox-waterproof-socks'


def od(*pairs):
    return collections.OrderedDict(pairs)


def rt(text):
    return '<p>%s</p>' % text if text else ''


def build(rec):
    settings = od(
        ('color_scheme', 'paper'),
        ('hide_rule', True),
        ('max_width', 46),
        ('eyebrow', rec.get('eyebrow', 'Being written')),
        ('heading', rec.get('heading', '')),
        ('heading_tag', 'h1'),
        ('heading_size', 'h2'),
        ('body', rt(rec.get('body', ''))),
        ('footnote', rt(rec.get('footnote', ''))),
        ('pointer_label', rec.get('pointer_label', '')),
        ('pointer_link_label', rec.get('pointer_link_text', '')),
        ('pointer_url', rec.get('pointer_href', '')),
    )

    buttons = rec.get('buttons', [])
    if buttons:
        settings['cta_label'] = buttons[0]['label']
        settings['cta_url'] = PRODUCT_URL if 'Buy' in buttons[0]['label'] else buttons[0]['href']
    if len(buttons) > 1:
        settings['link_label'] = buttons[1]['label']
        settings['link_url'] = buttons[1]['href'] or '/'

    tail = rec.get('tail', '')
    # The closing line only reads as a closing line when it is not the same
    # sentence as the footnote above it.
    if tail and tail != rec.get('footnote', ''):
        settings['tail_note'] = rt(tail)

    return od(
        ('sections', od(('intro', od(('type', 'centre-note'), ('settings', settings))))),
        ('order', ['intro']),
    )


def main():
    with open(CONTENT) as fh:
        stubs = json.load(fh)
    for handle in sorted(stubs):
        tpl = build(stubs[handle])
        path = os.path.join(ROOT, 'templates', 'page.%s.json' % handle)
        with open(path, 'w') as fh:
            json.dump(tpl, fh, indent=2, ensure_ascii=False)
            fh.write('\n')
        print('wrote templates/page.%s.json' % handle)
    print('%d placeholder templates' % len(stubs))


if __name__ == '__main__':
    main()
