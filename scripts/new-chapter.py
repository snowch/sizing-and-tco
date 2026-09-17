#!/usr/bin/env python3
"""Create a chapter or appendix stub with the book's standard shape.

    python3 scripts/new-chapter.py monte_carlo      # one, by slug
    python3 scripts/new-chapter.py --all            # every one that does not exist yet
    python3 scripts/new-chapter.py --all --force    # regenerate stubs, refusing written pages

A stub is not a placeholder. It carries the chapter's question, its prerequisites and the
measurements it owes the reader, all taken from ``bench/outline.py`` — so the table of contents
of work not yet done is visible from the published site, and a chapter cannot acquire a
dependency without recording it.

``--force`` refuses to touch a page that is no longer a stub. Losing prose to a regeneration is
the kind of mistake that only has to happen once.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.outline import APPENDICES, CHAPTERS, Appendix, Chapter  # noqa: E402
from bench.stamp import shown  # noqa: E402

MARKER = "[To write"


def chapter_stub(chapter: Chapter) -> str:
    previous = [c for c in CHAPTERS if c.number < chapter.number]
    # Title as well as number. A cell reading "ch13" tells a reader where to click and nothing
    # about what they are expected to know, and unlike a reference in a sentence there is no
    # surrounding prose to say. tests/test_book.py pins the title to bench/outline.py.
    needs = ", ".join(
        f"[{c.label} \u00b7 {c.title}](#{c.anchor})" for c in CHAPTERS if c.slug in chapter.needs
    ) or (
        f"[{previous[-1].label} \u00b7 {previous[-1].title}](#{previous[-1].anchor})"
        if previous
        else "none"
    )
    owes = chapter.owes or "[To write: what this chapter must produce.]"
    consumes = (
        "\n| **Built from** | " + ", ".join(f"`{source}`" for source in chapter.consumes) + " |"
        if chapter.consumes
        else ""
    )
    return f"""---
title: "{chapter.title} [DRAFT]"
short_title: "{chapter.label} {chapter.title}"
---

({chapter.anchor})=
# {chapter.label} · {chapter.title} [DRAFT]

:::{{note}} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | {needs} |
| **What it produces** | {owes} |{consumes}
:::

## The question

{chapter.question}

[To write: one paragraph. State the question this chapter answers and why the previous chapter
leaves it open. No summary of what is to come — the reader can see the headings.]

## The material

[To write: the body. Short sections. Code is quoted from the working tree with
`{{literalinclude}}` and text anchors, never pasted; model files are quoted the same way. See
AUTHORING_GUIDE.md.]

[To write: `{{include}}` the generated fragments declared in `bench/figures.py`, where the prose
needs them. No number is ever typed here. A figure that depends on a constant nobody has measured
renders as *not yet measured* on its own — the state propagates down the graph, and nothing has to
be marked by hand.

There is no trailing "What the model says" section. There used to be, in every chapter, and in
twenty-one of twenty-three it reprinted a table the reader had already seen a few hundred words
earlier with nothing new said about it. Show a figure where the argument needs it. If a chapter
genuinely ends on its numbers, give the section a name that says what is in it.]

## What this cannot tell you

[To write. **Mandatory.** What the model, the measurement or the method could not show, and what
was done instead. For a chapter with a model in it this must name what the model's *structure*
omits, because that is the error no amount of sampling can see. This chapter is not finished
while this section is missing.]

## Problems

[To write: each problem is a stub under `{chapter.tests_dir}/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content.]
"""


def appendix_stub(appendix: Appendix) -> str:
    consumes = (
        "\n| **Built from** | " + ", ".join(f"`{source}`" for source in appendix.consumes) + " |"
        if appendix.consumes
        else ""
    )
    return f"""---
title: "{appendix.title} [DRAFT]"
short_title: "{appendix.label} {appendix.title}"
---

({appendix.anchor})=
# {appendix.label} · {appendix.title} [DRAFT]

:::{{note}} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | {appendix.purpose} |{consumes}
:::

[To write: {appendix.purpose}]
"""


def write(path: Path, body: str, force: bool) -> bool:
    if path.exists():
        current = path.read_text()
        if MARKER not in current and not force:
            return False
        if MARKER not in current and force:
            print(f"  refusing to overwrite {shown(path)} — it is no longer a stub")
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    print(f"  wrote {shown(path)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", nargs="?", help="chapter or appendix slug")
    parser.add_argument("--all", action="store_true", help="every page that does not exist yet")
    parser.add_argument("--force", action="store_true", help="regenerate stubs, never prose")
    args = parser.parse_args()

    targets: list[tuple[Path, str]] = []
    for chapter in CHAPTERS:
        if args.all or chapter.slug == args.slug:
            targets.append((ROOT / chapter.path, chapter_stub(chapter)))
    for appendix in APPENDICES:
        if args.all or appendix.slug == args.slug:
            targets.append((ROOT / appendix.path, appendix_stub(appendix)))

    if not targets:
        print(f"no chapter or appendix with slug {args.slug!r}")
        return 1
    written = sum(write(path, body, args.force) for path, body in targets)
    print(f"\nnew-chapter: {written} page(s) written, {len(targets) - written} left alone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
