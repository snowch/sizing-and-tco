#!/usr/bin/env python3
"""Bring every chapter and appendix reference in the prose back in step with the outline.

    python3 scripts/relabel-references.py            # rewrite what has gone stale
    python3 scripts/relabel-references.py --check    # say what would change, touch nothing

Moving a chapter is one edit to ``bench/outline.py``. The pages render correctly straight away,
because the renderer derives every label from the outline rather than trusting the text it was
given. What it cannot do is edit the markdown, and the markdown still says ``ch03`` in the
sentence an author is reading — so this catches the source up, and
``tests/test_book.py::test_a_chapter_reference_names_the_chapter_the_outline_names`` is what
notices if nobody ran it.

Only the label moves. The rest of a reference's text is left exactly as written, because a
chapter's title carries MyST's typography and the outline's does not.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.outline import APPENDICES, CHAPTERS  # noqa: E402
from bench.stamp import shown  # noqa: E402

#: Where prose lives. Generated fragments are excluded: they are rebuilt, not edited.
PAGES = ("chapters/*.md", "appendices/*.md", "parts/*.md", "index.md")

#: A markdown link whose text opens with a chapter or appendix label.
REFERENCE = re.compile(r"\[(ch\d+|Appendix [A-Z])([^\]]*)\]\(#([a-z0-9-]+)\)")

#: A page's own label, in the two places it writes it: its front matter and its title heading.
OWN = (
    re.compile(r'^(short_title: ")(ch\d+|Appendix [A-Z])', re.M),
    re.compile(r"^(# )(ch\d+|Appendix [A-Z])", re.M),
)


def outline() -> dict[str, str]:
    """Every chapter and appendix anchor, and the label the outline currently gives it."""
    return {item.anchor: item.label for item in (*CHAPTERS, *APPENDICES)}


def owner() -> dict[str, str]:
    """Which label each page writes for itself, keyed by the file it lives in."""
    return {item.path: item.label for item in (*CHAPTERS, *APPENDICES)}


def restate(text: str, labels: dict[str, str], own: str | None) -> tuple[str, list[str]]:
    """The text with every stale label corrected, and a note of each correction.

    Two kinds: the labels this page uses to point at other pages, and the label it writes for
    itself in its front matter and its title heading. Both are the chapter's number, and the
    chapter's number is derived from the outline.
    """
    changed: list[str] = []

    def one(found: re.Match[str]) -> str:
        label, rest, anchor = found.groups()
        current = labels.get(anchor)
        if current is None or current == label:
            return found.group(0)
        changed.append(f"{label} -> {current} (#{anchor})")
        return f"[{current}{rest}](#{anchor})"

    text = REFERENCE.sub(one, text)
    if own:
        for pattern in OWN:

            def mine(found: re.Match[str]) -> str:
                if found.group(2) == own:
                    return found.group(0)
                changed.append(f"its own {found.group(2)} -> {own}")
                return found.group(1) + own

            text = pattern.sub(mine, text)
    return text, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report, and change nothing")
    args = parser.parse_args()

    labels = outline()
    mine = owner()
    stale = 0
    for pattern in PAGES:
        for page in sorted(ROOT.glob(pattern)):
            before = page.read_text()
            after, changed = restate(before, labels, mine.get(str(page.relative_to(ROOT))))
            if not changed:
                continue
            stale += len(changed)
            print(f"  {shown(page)}: {', '.join(sorted(set(changed)))}")
            if not args.check:
                page.write_text(after)

    if not stale:
        print("relabel-references: OK (every reference already names what the outline names)")
        return 0
    if args.check:
        print(f"relabel-references: {stale} stale reference(s). Run without --check to fix.")
        return 1
    print(f"relabel-references: rewrote {stale} reference(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
