#!/usr/bin/env python3
"""Every file the built pages link to was actually built.

    python3 scripts/check-built-links.py _build/html "$BASE_URL"

A broken link to a page is caught by ``myst build --strict``, because MyST resolves
cross-references. A broken link to a *file* is not: a download link to a PDF that the build did
not produce, or an interactive model page that was never copied into place, resolves perfectly as
markup and 404s for the reader. That is the failure this catches, and it can only be caught after
the site has been assembled.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

#: Anything local the pages point at. Schemes and anchors are somebody else's problem.
LINK = re.compile(r'(?:href|src)="([^"#?]+)"')


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
    for page in sorted(root.rglob("*.html")):
        for target in LINK.findall(page.read_text(errors="ignore")):
            if target.startswith(("http://", "https://", "data:", "mailto:", "//")):
                continue
            checked += 1
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
            if not candidate.exists() and not candidate.with_suffix(".html").exists():
                missing.append(f"{page.relative_to(root)} -> {target}")

    if missing:
        print("check-built-links: FAILED")
        for line in sorted(set(missing)):
            print(f"  - {line}")
        return 1
    print(f"check-built-links: OK ({checked} local link(s) across the built site)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
