#!/usr/bin/env python3
"""
Validates Shopify range settings against constraints that `theme check` does
not enforce. A single violation makes Shopify reject the whole settings file
and replace it with [], silently dropping every design token.

Run before every push:  python3 .claude-validate-schema.py
"""
import json, glob, re, os, sys

def audit(settings, origin, out):
    for s in settings:
        if s.get('type') != 'range':
            continue
        sid = s.get('id', '?')
        mn, mx, st = s.get('min'), s.get('max'), s.get('step', 1)
        if None in (mn, mx) or not st:
            out.append((origin, sid, 'missing min/max/step')); continue
        steps = (mx - mn) / st
        if steps > 101:
            out.append((origin, sid, f'{steps:.0f} steps, max is 101 (min={mn} max={mx} step={st})'))
        d = s.get('default')
        if d is not None:
            if d < mn or d > mx:
                out.append((origin, sid, f'default {d} outside [{mn},{mx}]'))
            elif abs(((d - mn) / st) - round((d - mn) / st)) > 1e-9:
                out.append((origin, sid, f'default {d} is not on a step boundary'))
        u = s.get('unit')
        if u is not None and (len(u) > 3 or not u.isascii()):
            out.append((origin, sid, f'unit {u!r} must be ascii and at most 3 characters'))

bad = []
for g in json.load(open('config/settings_schema.json')):
    if 'settings' in g:
        audit(g['settings'], f"settings_schema[{g.get('name','?')}]", bad)

for f in sorted(glob.glob('sections/*.liquid')):
    m = re.search(r'\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}', open(f, encoding='utf-8').read(), re.S)
    if not m:
        continue
    try:
        sc = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        bad.append((os.path.basename(f), '-', f'schema is not valid JSON: {e}')); continue
    audit(sc.get('settings', []), os.path.basename(f), bad)
    for b in sc.get('blocks', []):
        audit(b.get('settings', []), f"{os.path.basename(f)} > block:{b['type']}", bad)

# Defaults in settings_data.json must satisfy the schema too.
valid = {}
for g in json.load(open('config/settings_schema.json')):
    for s in g.get('settings', []):
        if 'id' in s:
            valid[s['id']] = s
data = json.load(open('config/settings_data.json'))['current']
for k, v in data.items():
    s = valid.get(k)
    if s is None:
        bad.append(('settings_data.json', k, 'not declared in settings_schema')); continue
    if s.get('type') == 'range' and isinstance(v, (int, float)):
        mn, mx, st = s['min'], s['max'], s.get('step', 1)
        if v < mn or v > mx:
            bad.append(('settings_data.json', k, f'value {v} outside [{mn},{mx}]'))
        elif abs(((v - mn) / st) - round((v - mn) / st)) > 1e-9:
            bad.append(('settings_data.json', k, f'value {v} is not on a step boundary (step={st})'))

if bad:
    print(f"{len(bad)} schema problem(s):\n")
    for origin, sid, why in bad:
        print(f"  {origin:52s} {sid:24s} {why}")
    sys.exit(1)
print("settings schema is valid for Shopify")
