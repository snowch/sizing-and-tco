#!/usr/bin/env python3
"""The model file as a chapter leaves it, shown whole in a panel beside the chapter's graph.

    python3 scripts/build-playground.py                # into _build/playground/
    python3 scripts/build-playground.py --out DIR

A chapter that does not quote its model file in pieces embeds this instead, so a reader can see
what the graph is drawn from. It is read-only: the graph beside it is the thing a reader moves,
and `make check` is what loads the file and checks every unit. It used to run the toolkit here
too, which was the only way to move a number before the chapters embedded the graph.

Named for the playground it was, because the address is in every chapter that embeds it and in
the offline worker's list, and the reader never sees the word.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.stages import label_of, stages  # noqa: E402
from bench.stamp import shown  # noqa: E402
from bench.theme import FRAME, both_ways  # noqa: E402

DEFAULT_OUT = ROOT / "_build" / "playground"


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &mdash; Sizing and TCO</title>
<style>{css}</style>
{theme}
</head>
<body>
<header>
  <h1>The model file &mdash; {title}</h1>
  <p>As this chapter leaves it. The chapter’s graph is drawn from this file.</p>
</header>
<pre>{model}</pre>
<footer><p>Built from <code>{stage}</code>.</p></footer>
</body>
</html>
"""


CSS = """
:root { color-scheme: light dark; --edge: #cfd8dc; --ink: #263238; --muted: #546e7a;
        --panel: #fafafa; --bg: #ffffff; }
@media (prefers-color-scheme: dark) {
  :root { --edge: #37474f; --ink: #eceff1; --muted: #b0bec5; --panel: #1c262b; --bg: #11181c; }
}
* { box-sizing: border-box; }
/* The file fills whatever the frame gives it and scrolls inside, so the chapter decides how
   tall the panel is and the header stays in view. */
html, body { height: 100%; }
body { font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
       color: var(--ink); background: var(--bg); margin: 0; padding: 16px;
       display: flex; flex-direction: column; gap: 10px; }
/* Clear of the Expand control a chapter floats over this panel's top right corner. */
header h1 { font-size: 20px; margin: 0 0 4px; padding-right: 6.5rem; }
header p, footer p { color: var(--muted); margin: 4px 0; }
pre { flex: 1; min-height: 12rem; margin: 0; overflow: auto; padding: 10px;
      font: 13px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
      border: 1px solid var(--edge); border-radius: 4px; background: var(--panel); }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
footer { font-size: 13px; }
"""


def build(stage) -> str:
    """One page for one stage of the running example."""
    return PAGE.format(
        css=both_ways(CSS),
        theme=FRAME,
        title=html.escape(f"{label_of(stage.chapter)} \u00b7 {stage.title}"),
        model=html.escape(stage.path.read_text()),
        stage=html.escape(shown(stage.path)),
    )


def embedded() -> set[str]:
    """The directories the chapters embed, which is the whole list of pages worth building."""
    return {
        directory
        for path in (ROOT / "chapters").glob("*.md")
        for directory in re.findall(r"\{iframe\}\s+/playground/([a-z0-9-]+)/", path.read_text())
    }


def pages() -> dict[str, object]:
    """Where each embedded stage's page goes, keyed by the directory its chapter embeds.

    Named for the chapter rather than the stage, because the chapter is what a reader is in, and
    a URL in a book should say where it belongs.
    """
    wanted = embedded()
    return {
        slug: stage
        for stage in stages()
        if not stage.is_the_finished_model and (slug := stage.chapter.replace("_", "-")) in wanted
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    for slug, stage in pages().items():
        target = args.out / slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build(stage))
        print(f"  wrote {shown(target)} ({len(target.read_text()):,} bytes)")
    return 0


if __name__ == "__main__":  # pragma: no cover - a thin wrapper around main()
    raise SystemExit(main())
