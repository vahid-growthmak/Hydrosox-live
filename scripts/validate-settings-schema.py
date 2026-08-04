#!/usr/bin/env python3
"""
Validates what Shopify enforces on upload but `theme check` does not.

Two independent failure modes, both silent:

  * An invalid range in settings_schema.json makes Shopify reject the whole
    file and replace it with [], dropping every design token at once.
  * A template setting whose value is not valid for its section schema — a
    select value that is not one of the declared options, a range given a
    string — makes Shopify reject that template. The old one stays live, so
    it reads as a slow sync rather than a rejection.

Run before every push:  python3 scripts/validate-settings-schema.py
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
        # Shopify: "Range settings must have at least 3 steps." A two-value
        # range is rejected outright, and a rejected section takes every
        # template that references it down with it. Use a select instead.
        if steps < 2:
            out.append((origin, sid, f'{steps + 1:.0f} values, needs at least 3 — use a select '
                                     f'(min={mn} max={mx} step={st})'))
        d = s.get('default')
        if d is not None:
            if d < mn or d > mx:
                out.append((origin, sid, f'default {d} outside [{mn},{mx}]'))
            elif abs(((d - mn) / st) - round((d - mn) / st)) > 1e-9:
                out.append((origin, sid, f'default {d} is not on a step boundary'))
        u = s.get('unit')
        if u is not None and (len(u) > 3 or not u.isascii()):
            out.append((origin, sid, f'unit {u!r} must be ascii and at most 3 characters'))


# ---------------------------------------------------------- template values

def _strip(text):
    return re.sub(r"^\s*/\*[\s\S]*?\*/\s*", "", text)


def _section_schemas():
    out = {}
    for path in glob.glob("sections/*.liquid"):
        m = re.search(r"\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}",
                      open(path, encoding="utf-8").read(), re.S)
        if not m:
            continue
        try:
            out[os.path.basename(path)[:-7]] = json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}: schema is not valid JSON: {exc}")
    return out


def _defs(schema, block_type=None):
    if block_type is None:
        return {s["id"]: s for s in schema.get("settings", []) if s.get("id")}
    for block in schema.get("blocks") or []:
        if block["type"] == block_type:
            return {s["id"]: s for s in block.get("settings", []) if s.get("id")}
    return {}


def check_values(where, definitions, values, out):
    """A value Shopify cannot accept for its declared setting type."""
    for sid, val in (values or {}).items():
        if val is None:
            # Shopify refuses the whole template and keeps the old one live.
            out.append((where, sid, "is null; omit the setting instead"))
            continue
        spec = definitions.get(sid)
        if spec is None:
            out.append((where, sid, "not declared in the section schema"))
            continue
        kind = spec.get("type")
        if kind == "select":
            options = [o["value"] for o in spec.get("options", [])]
            if str(val) not in options:
                out.append((where, sid, f"{val!r} is not one of {options}"))
        elif kind == "checkbox":
            if not isinstance(val, bool):
                out.append((where, sid, f"{val!r} must be true or false"))
        elif kind == "richtext":
            # Shopify refuses a template whose richtext is not inside a
            # block-level tag, and keeps the old version of the page live.
            if isinstance(val, str) and val.strip() and not val.lstrip().startswith(
                ("<p", "<ul", "<ol", "<h", "<blockquote", "<div", "<br")
            ):
                out.append((where, sid, "richtext must be wrapped in a block tag such as <p>"))
        elif kind == "range":
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                out.append((where, sid, f"{val!r} must be a number, not a string"))
            else:
                mn, mx, step = spec["min"], spec["max"], spec.get("step", 1)
                if val < mn or val > mx:
                    out.append((where, sid, f"{val} is outside [{mn}, {mx}]"))
                elif abs(((val - mn) / step) - round((val - mn) / step)) > 1e-9:
                    out.append((where, sid, f"{val} is not on a step of {step}"))


def audit_templates(out):
    schemas = _section_schemas()
    files = sorted(glob.glob("templates/**/*.json", recursive=True))
    files += sorted(glob.glob("sections/*-group.json"))
    for path in files:
        try:
            data = json.loads(_strip(open(path, encoding="utf-8").read()))
        except json.JSONDecodeError as exc:
            out.append((os.path.basename(path), "-", f"not valid JSON: {exc}")); continue
        name = os.path.basename(path)
        for key, section in (data.get("sections") or {}).items():
            schema = schemas.get(section.get("type"))
            if schema is None:
                out.append((name, key, f"unknown section '{section.get('type')}'")); continue
            check_values(f"{name} [{key}]", _defs(schema), section.get("settings"), out)
            for bkey, block in (section.get("blocks") or {}).items():
                btype = block.get("type")
                if not _defs(schema, btype):
                    out.append((name, f"{key}/{bkey}", f"block '{btype}' not declared")); continue
                check_values(f"{name} [{key}/{bkey}]", _defs(schema, btype), block.get("settings"), out)


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
    name = os.path.basename(f)

    # A section may declare presets or a default, never both.
    if 'presets' in sc and 'default' in sc:
        bad.append((name, '-', "has both 'presets' and 'default'"))

    for b in sc.get('blocks', []):
        bt = b.get('type', '?')
        # Shopify reads a block type beginning with "app" as one of its own app
        # blocks, which may carry neither settings nor a limit, and rejects the
        # section: "Invalid block 'app_embed': 'limit' is not a valid attribute".
        if bt.startswith('app') or bt.startswith('@'):
            bad.append((name, bt, "block type collides with Shopify's app blocks — rename it"))
        if b.get('settings') and not b.get('name'):
            bad.append((name, bt, 'block has settings but no name'))
        audit(b.get('settings', []), f"{name} > block:{bt}", bad)

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

audit_templates(bad)

if bad:
    print(f"{len(bad)} schema problem(s):\n")
    for origin, sid, why in bad:
        print(f"  {origin:52s} {sid:24s} {why}")
    sys.exit(1)
print("settings schema and every template value are valid for Shopify")
