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
            stype = section.get("type")
            # 'apps' is Shopify's own app-block host section. It has no file in
            # the theme and appears whenever a merchant drops an app block in.
            if stype in ("apps",):
                continue
            schema = schemas.get(stype)
            if schema is None:
                out.append((name, key, f"unknown section '{stype}'")); continue
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
# Shopify rewrites this file and prepends its own /* */ banner, so it is not
# plain JSON once the theme has been edited in admin or synced back.
data = json.loads(_strip(open('config/settings_data.json', encoding='utf-8').read()))['current']
# Keys Shopify owns in this file. They appear the moment the theme is edited in
# admin — section settings, the legacy index content, and theme blocks — and are
# not theme settings, so they have no entry in settings_schema and never will.
SHOPIFY_OWNED = {'sections', 'content_for_index', 'blocks', 'current', 'presets'}
for k, v in data.items():
    if k in SHOPIFY_OWNED:
        continue
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


def audit_page_scoped_claims(out):
    """Structured data is a claim about one page, so only one page may make it.

    Two pages publishing FAQPage for identically worded questions compete for a
    single rich result rather than reinforcing each other, and several
    Organization blocks hand a search engine competing descriptions of one
    business. Both flags default off and are switched on per template, which is
    easy to get right by hand and impossible to keep right once a generator
    deep-copies a section — the homepage FAQ propagated its flag to six other
    templates the first time it was set.
    """
    claims = {"faq-accordion": "FAQPage", "company-details": "Organization"}
    seen = {v: [] for v in claims.values()}
    for path in sorted(glob.glob("templates/**/*.json", recursive=True)):
        try:
            data = json.loads(_strip(open(path, encoding="utf-8").read()))
        except json.JSONDecodeError:
            continue
        for section in (data.get("sections") or {}).values():
            claim = claims.get(section.get("type"))
            if claim and (section.get("settings") or {}).get("emit_schema"):
                seen[claim].append(os.path.basename(path))
    for claim, files in seen.items():
        if len(files) > 1:
            out.append((", ".join(sorted(files)), claim,
                        f"{len(files)} templates publish {claim} — only one may"))


def audit_generator_order(out):
    """Two builders write templates/product.json and the order matters.

    build-product-template.py writes the file from scratch; the sitemap builder's
    add_product_page_extras() then adds the breadcrumb, the review module and the
    related guides. Run product last and all three are silently dropped — the
    file stays valid, deploys cleanly, and the page quietly loses its trail and
    its reviews. That shipped once. This makes it fail here instead.
    """
    path = "templates/product.json"
    if not os.path.exists(path):
        return
    try:
        data = json.loads(_strip(open(path, encoding="utf-8").read()))
    except json.JSONDecodeError:
        return
    order = data.get("order") or []
    types = {k: (data.get("sections") or {}).get(k, {}).get("type") for k in order}
    for wanted in ("breadcrumb", "review-module", "related-guides"):
        if wanted not in types.values():
            out.append((path, wanted,
                        "missing — run build-product-template.py BEFORE "
                        "build-sitemap-templates.py, not after"))


audit_generator_order(bad)

audit_page_scoped_claims(bad)

if bad:
    print(f"{len(bad)} schema problem(s):\n")
    for origin, sid, why in bad:
        print(f"  {origin:52s} {sid:24s} {why}")
    sys.exit(1)
print("settings schema and every template value are valid for Shopify")
