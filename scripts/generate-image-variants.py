#!/usr/bin/env python3
"""Pre-generates responsive variants for the bundled photo assets.

Shopify resizes uploaded images on the fly but serves theme assets as-is, so
the -480w and -960w files that snippets/hs-image.liquid puts in its fallback
srcset have to exist on disk. Run this after adding or replacing any photo in
assets/; it skips what already exists and never upscales. Where a re-encode
would come out larger than its source, the source bytes are copied instead so
the variant is never the worse choice.

Idempotent.
"""
import pathlib
import re
import shutil

from PIL import Image

ASSETS = pathlib.Path(__file__).resolve().parent.parent / "assets"
SKIP = ("hs-layer-frame", "favicon", "hydrosox-logo")
VARIANT = re.compile(r"-(?:480|960)w\.\w+$")


def main():
    made = 0
    for f in sorted(ASSETS.iterdir()):
        if f.suffix.lower() not in (".webp", ".jpg"):
            continue
        if any(f.name.startswith(s) for s in SKIP) or VARIANT.search(f.name):
            continue
        im = Image.open(f)
        for target in (480, 960):
            out = f.with_name(f"{f.stem}-{target}w{f.suffix}")
            if out.exists():
                continue
            w = min(target, im.width)
            h = round(im.height * w / im.width)
            v = im.resize((w, h), Image.LANCZOS)
            if f.suffix.lower() == ".webp":
                v.save(out, "WEBP", quality=82, method=6)
            else:
                v.convert("RGB").save(out, "JPEG", quality=80, progressive=True, optimize=True)
            if out.stat().st_size > f.stat().st_size and w >= im.width * 0.9:
                shutil.copyfile(f, out)
            made += 1
    print(f"variants written: {made}")


if __name__ == "__main__":
    main()
