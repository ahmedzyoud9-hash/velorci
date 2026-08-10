#!/usr/bin/env python3
"""Generate velorci-standalone.html from index.html.

The standalone file is the same site with support.js inlined and every
assets/ reference replaced by a data: URI, so it can be imported or opened
as a single file. Regenerate it after any change to index.html, and after
build-pages.py (which rewrites index.html's head):

    python3 build-pages.py && python3 build-standalone.py

Since the site became multi-page, the links inside this file point at the
sibling page files (about.html, terms.html, ...), so navigation only works
when it sits alongside them. On its own it still renders the home page.
"""

import base64
import mimetypes
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "index.html"
RUNTIME = ROOT / "support.js"
OUT = ROOT / "velorci-standalone.html"

RUNTIME_TAG = '<script src="./support.js"></script>'

# Inlining the runtime puts its source into the document, and that source
# contains the literal text "<x-dc>" inside an error message. On boot the
# runtime re-fetches its own URL and re-parses the template from the first
# "<x-dc>" it finds — which, in the single-file build, is that error string
# rather than the real template, so the page renders the runtime's source as
# text. Declaring an (empty) resource map makes boot() skip that re-fetch;
# every other __resources lookup already falls back to the network when a key
# is missing, so behaviour is otherwise unchanged.
SELF_CONTAINED_GUARD = "<script>window.__resources = window.__resources || {};</script>"


def data_uri(path: pathlib.Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> int:
    html = SRC.read_text(encoding="utf-8")

    if RUNTIME_TAG not in html:
        print(f"error: {RUNTIME_TAG} not found in {SRC.name}", file=sys.stderr)
        return 1
    html = html.replace(
        RUNTIME_TAG,
        SELF_CONTAINED_GUARD + "\n<script>\n" + RUNTIME.read_text(encoding="utf-8") + "\n</script>",
    )

    refs = sorted(set(re.findall(r"assets/[\w.-]+", html)))
    missing = [r for r in refs if not (ROOT / r).exists()]
    if missing:
        print("error: missing assets: " + ", ".join(missing), file=sys.stderr)
        return 1
    for ref in refs:
        html = html.replace(ref, data_uri(ROOT / ref))

    left = re.findall(r"assets/[\w.-]+", html)
    if left:
        print("error: unresolved asset references remain: " + ", ".join(sorted(set(left))), file=sys.stderr)
        return 1

    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.name} ({len(html):,} chars, {len(refs)} assets inlined)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
