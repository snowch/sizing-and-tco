#!/usr/bin/env python3
"""Every file the built pages link to was actually built.

    python3 scripts/check-built-links.py _build/html "$BASE_URL"

A broken link to a page is caught by ``myst build --strict``, because MyST resolves
cross-references. A broken link to a *file* is not: an interactive model page or a playground
that was never copied into place resolves perfectly as markup and 404s for the reader. That is
the failure this catches, and it can only be caught after the site has been assembled.

A fragment is the quieter version of the same thing, and it shipped: four "On this page" entries
pointed at ids nobody wrote, because the contents list and the renderer disagreed about what a
comma does to a heading. Nothing 404s — the reader simply arrives at the top of the page and
does not know why.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

#: Anything local the pages point at, with the fragment kept: a link to a heading that was never
#: written resolves as markup and lands the reader at the top of the page instead.
LINK = re.compile(r'(?:href|src)="([^"?]+)"')
#: Every anchor the built pages offer.
ANCHOR = re.compile(r'id="([^"]+)"')


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    base = (sys.argv[2] if len(sys.argv) > 2 else "").rstrip("/")
    if not root.is_dir():
        print(f"{root} is not a directory — did the build run?", file=sys.stderr)
        return 1

    missing: list[str] = []
    checked = 0
    anchors: dict[Path, set[str]] = {}

    def offers(path: Path) -> set[str]:
        if path not in anchors:
            anchors[path] = set(ANCHOR.findall(path.read_text(errors="ignore")))
        return anchors[path]

    for page in sorted(root.rglob("*.html")):
        for target in LINK.findall(page.read_text(errors="ignore")):
            if target.startswith(("http://", "https://", "data:", "mailto:", "//")):
                continue
            checked += 1
            target, _, fragment = target.partition("#")
            if not target:
                # Same page. The anchor is the whole of the link, so it is the whole of the check.
                if fragment and fragment not in offers(page):
                    missing.append(f"{page.relative_to(root)} -> #{fragment} (no such id)")
                continue
            if target.startswith("/"):
                # A root-relative URL on a project site has to carry the base path, or the
                # browser asks the wrong origin-relative address and gets a 404 — even though
                # the file is sitting in the build exactly where this check would look for it.
                # That is how a broken embed shipped: the file existed, the URL did not.
                if base and not target.startswith(base + "/"):
                    missing.append(
                        f"{page.relative_to(root)} -> {target} (missing the base path {base!r}; "
                        f"a reader would ask for {target} and this site is served from {base}/)"
                    )
                    continue
                relative = target[len(base) :] if base and target.startswith(base) else target
                candidate = root / relative.lstrip("/")
            else:
                candidate = page.parent / target
            if target.endswith("/"):
                # A trailing slash asks for a directory, and Pages answers with its index.html
                # or a 404. Path() drops the slash, so without this a link to `/models/x/` was
                # passed on the strength of `models/x.html` existing — a page the browser would
                # never be sent to.
                candidate = candidate / "index.html"
            if not candidate.exists() and not candidate.with_suffix(".html").exists():
                missing.append(f"{page.relative_to(root)} -> {target}")
            elif (
                fragment
                and candidate.suffix == ".html"
                and candidate.exists()
                and fragment not in offers(candidate)
            ):
                missing.append(f"{page.relative_to(root)} -> {target}#{fragment} (no such id)")

    # The search index is a second set of links into the same pages, written by a different code
    # path and read by nobody until a reader types. Three hundred of them, checked by nothing.
    catalogue = root / "search.json"
    records = 0
    if catalogue.exists():
        import json

        for record in json.loads(catalogue.read_text()):
            records += 1
            page, _, fragment = str(record.get("u", "")).partition("#")
            target = root / page
            if not page or not target.exists():
                missing.append(f"search.json -> {record.get('u')} (no such page)")
            elif fragment and fragment not in offers(target):
                missing.append(f"search.json -> {record.get('u')} (no such id)")

    if missing:
        print("check-built-links: FAILED")
        for line in sorted(set(missing)):
            print(f"  - {line}")
        return 1
    print(
        f"check-built-links: OK ({checked} local link(s), {records} search record(s) and "
        f"{sum(len(v) for v in anchors.values())} anchor(s) across the built site)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
