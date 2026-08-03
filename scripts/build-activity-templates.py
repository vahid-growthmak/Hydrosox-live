#!/usr/bin/env python3
"""
Generates templates/page.<activity>.json for the five activity pages.

Copy comes from the parsed reference content; the sibling-card row is taken
from the homepage's own activity blocks so the two can never disagree about a
title, a problem line or a link. Run from the theme root.
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = sys.argv[1] if len(sys.argv) > 1 else 'activity-content.json'

ORDER = ['hiking', 'walking', 'all-day-in-boots', 'cycling-and-commuting', 'running-and-trail']
PRODUCT_URL = '/products/hydrosox-waterproof-socks'


def od(*pairs):
    return collections.OrderedDict(pairs)


def rt(text):
    """Wraps plain text as the rich text Shopify stores for a richtext setting."""
    return '<p>%s</p>' % text if text else ''


def split_eyebrow(raw):
    """'01 — Shop by activity' -> ('01', 'Shop by activity')"""
    m = re.match(r'^\s*(\d+)\s*[—–-]\s*(.+)$', raw or '')
    return (m.group(1), m.group(2).strip()) if m else ('', (raw or '').strip())


def load_homepage_activities():
    with open(os.path.join(ROOT, 'templates/index.json')) as fh:
        idx = json.load(fh)
    sec = idx['sections']['activity']
    out = collections.OrderedDict()
    for key in sec.get('block_order', []):
        st = sec['blocks'][key].get('settings', {})
        link = st.get('link', '')
        handle = link.rstrip('/').split('/')[-1] if link else ''
        if handle:
            out[handle] = {
                'title': st.get('title', ''),
                'problem': st.get('problem', ''),
                'meta': st.get('meta', ''),
                'link': link,
            }
    return out


# Four of the five reference pages carry a note to the photographer where the
# caption should be. Anything of that shape is replaced with the line the
# finished page uses.
PLACEHOLDER_NOTE = re.compile(r'^\s*\d+\s+of these four frames', re.I)
GALLERY_NOTE = ('Product imagery rather than a documentary shoot, so read it for what the sock '
                'is and where it goes — not as evidence. The checkable claim is the membrane.')


def gallery_note(text):
    return GALLERY_NOTE if PLACEHOLDER_NOTE.match(text or '') else text


def section(stype, settings, blocks=None, block_order=None):
    rec = od(('type', stype), ('settings', settings))
    if blocks:
        rec['blocks'] = blocks
        rec['block_order'] = block_order
    return rec


def gallery_blocks(handle, rows):
    blocks, order = collections.OrderedDict(), []
    for i, row in enumerate(rows, start=1):
        key = 'g%d' % i
        asset = 'activity-%s-%02d.webp' % (handle, i)
        exists = os.path.exists(os.path.join(ROOT, 'assets', asset))
        st = od(('caption', row.get('caption', '')))
        if exists:
            st['image_fallback'] = asset
            st['image_alt'] = row.get('caption', '')
        blocks[key] = od(('type', 'image'), ('settings', st))
        order.append(key)
    return blocks, order


def item_blocks(rows, prefix='i'):
    blocks, order = collections.OrderedDict(), []
    for i, row in enumerate(rows, start=1):
        key = '%s%d' % (prefix, i)
        blocks[key] = od(('type', 'item'), ('settings', od(
            ('title', row.get('title', '')),
            ('body', rt(row.get('body', ''))),
        )))
        order.append(key)
    return blocks, order


def sibling_blocks(handle, activities):
    blocks, order = collections.OrderedDict(), []
    n = 0
    for other, info in activities.items():
        if other == handle:
            continue
        n += 1
        key = 's%d' % n
        blocks[key] = od(('type', 'card'), ('settings', od(
            ('title', info['title']),
            ('body', info['problem']),
            ('link', info['link']),
        )))
        order.append(key)
    return blocks, order


def build(handle, page, activities):
    secs = page['sections']
    hero, specs, problem, answers, gal, practice, limits, _sib, close = secs[:9]
    index, eyebrow = split_eyebrow(hero['eyebrow'])
    hero_actions = hero.get('actions', [])
    close_actions = close.get('actions', [])
    practice_links = practice.get('actions', [])

    sections = collections.OrderedDict()
    order = []

    def add(key, rec):
        sections[key] = rec
        order.append(key)

    # 1 — hero over a full-bleed photograph
    add('hero', section('page-hero', od(
        ('color_scheme', 'ink'),
        ('min_height', 36),
        ('index_label', index),
        ('eyebrow', eyebrow),
        ('heading', hero['heading']),
        ('lede', rt(hero['ledes'][0] if hero['ledes'] else '')),
        ('image_fallback', 'activity-%s.webp' % handle),
        ('image_alt', '%s in HydroSox waterproof socks' % activities[handle]['title']),
        ('focal_point', 'center'),
        ('scrim_vertical', 70),
        ('scrim_horizontal', 55),
        ('cta_label', hero_actions[0]['label'] if hero_actions else 'Buy a pair'),
        ('cta_url', PRODUCT_URL),
        ('link_label', hero_actions[1]['label'] if len(hero_actions) > 1 else ''),
        ('link_url', hero_actions[1]['href'] if len(hero_actions) > 1 else ''),
    )))

    # 2 — the four hard facts
    sb, so = collections.OrderedDict(), []
    for i, cell in enumerate(specs['specs'], start=1):
        key = 'f%d' % i
        sb[key] = od(('type', 'spec'), ('settings', od(
            ('label', cell['label']), ('value', cell['value']))))
        so.append(key)
    add('specs', section('spec-strip', od(
        ('color_scheme', 'ink'), ('hidden_heading', 'Product facts')), sb, so))

    # 3 — the problem this activity has
    b, o = item_blocks(problem['rows'], 'p')
    add('problem', section('content-columns', od(
        ('color_scheme', 'paper'), ('layout', 'list'), ('numbered', False),
        ('row_density', 'compact'),
        ('eyebrow', problem['eyebrow']), ('heading', problem['heading']),
        ('lede', rt(problem['ledes'][0] if problem['ledes'] else '')),
    ), b, o))

    # 4 — what answers it, numbered. Its opening line belongs beside the
    # heading rather than above the list, which is where the design puts it.
    b, o = item_blocks(answers['rows'], 'a')
    ans_links = answers.get('actions', [])
    add('answers', section('content-columns', od(
        ('color_scheme', 'ink'), ('layout', 'list'), ('numbered', True),
        ('eyebrow', answers['eyebrow']), ('heading', answers['heading']),
        ('head_note', rt(answers['ledes'][0] if answers['ledes'] else '')),
        ('link_label', ans_links[0]['label'] if ans_links else ''),
        ('link_url', ans_links[0]['href'] if ans_links else ''),
    ), b, o))

    # 5 — the same pair in these conditions
    b, o = gallery_blocks(handle, gal['rows'])
    add('inuse', section('content-columns', od(
        ('color_scheme', 'wash'), ('layout', 'gallery'),
        ('eyebrow', gal['eyebrow']), ('heading', gal['heading']),
        ('head_note', rt(gallery_note(gal['ledes'][0] if gal['ledes'] else ''))),
        ('gallery_aspect', '4 / 5'),
    ), b, o))

    # 6 — practical notes, with the two support links
    b, o = item_blocks(practice['rows'], 'w')
    add('practice', section('content-columns', od(
        ('color_scheme', 'paper'), ('layout', 'list'), ('numbered', False),
        ('eyebrow', practice['eyebrow']), ('heading', practice['heading']),
        ('link_label', practice_links[0]['label'] if practice_links else ''),
        ('link_url', practice_links[0]['href'] if practice_links else ''),
        ('link2_label', practice_links[1]['label'] if len(practice_links) > 1 else ''),
        ('link2_url', practice_links[1]['href'] if len(practice_links) > 1 else ''),
    ), b, o))

    # 7 — where it stops
    foot = limits['ledes'][1] if len(limits['ledes']) > 1 else ''
    if foot and limits.get('actions'):
        label = limits['actions'][-1]['label']
        href = limits['actions'][-1]['href']
        foot = foot.replace(label, '<a href="%s">%s</a>' % (href, label))
    add('limits', section('centre-note', od(
        ('color_scheme', 'blue'), ('max_width', 46),
        ('eyebrow', limits['eyebrow']), ('heading', limits['heading']),
        ('body', rt(limits['ledes'][0] if limits['ledes'] else '')),
        ('footnote', rt(foot)),
    )))

    # 8 — the other four activities
    b, o = sibling_blocks(handle, activities)
    add('siblings', section('link-cards', od(
        ('color_scheme', 'paper'), ('columns', 4),
        ('eyebrow', 'Not your problem?'), ('heading', 'Same sock, different day.'),
    ), b, o))

    # 9 — closing line
    add('close', section('closing-cta', od(
        ('color_scheme', 'paper'), ('show_rule', False),
        ('heading', close['heading']),
        ('cta_label', close_actions[0]['label'] if close_actions else 'Buy a pair'),
        ('cta_url', PRODUCT_URL),
        ('alt_label', close_actions[1]['label'] if len(close_actions) > 1 else ''),
        ('alt_url', close_actions[1]['href'] if len(close_actions) > 1 else ''),
    )))

    return od(('sections', sections), ('order', order))


def main():
    with open(CONTENT) as fh:
        content = json.load(fh)
    activities = load_homepage_activities()
    missing = [h for h in ORDER if h not in activities]
    if missing:
        sys.exit('homepage has no activity block for: %s' % ', '.join(missing))

    for handle in ORDER:
        tpl = build(handle, content[handle], activities)
        path = os.path.join(ROOT, 'templates', 'page.%s.json' % handle)
        with open(path, 'w') as fh:
            json.dump(tpl, fh, indent=2, ensure_ascii=False)
            fh.write('\n')
        print('wrote templates/page.%s.json  (%d sections)' % (handle, len(tpl['order'])))


if __name__ == '__main__':
    main()
