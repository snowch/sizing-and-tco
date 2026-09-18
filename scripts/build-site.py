#!/usr/bin/env python3
"""The book as static pages, rendered from MyST's parse rather than MyST's theme.

    python3 scripts/build-site.py                    # every page, into _build/static/
    python3 scripts/build-site.py --only ch01        # one page, to look at
    python3 scripts/build-site.py --out DIR

A proof, not a replacement. The question it answers is whether this repository can own the page
its readers look at, and the answer turns on two facts that were already true before this file
existed:

**The renderer is not new.** ``scripts/build-pdf.py`` walks MyST's AST and emits HTML, and it
handles every node type this book contains — twenty-six branches against twenty-seven types in
the parse, the two extras being structural wrappers. It raises on anything it does not know, so
content cannot silently disappear. This module imports that renderer rather than growing a
second one.

**The half of MyST that matters runs offline.** ``myst build --strict`` without ``--html``
produces the AST and resolves all of the book's cross-references; only the *theme* needs the
template registry. So keeping MyST as a parser costs nothing and keeps the check that catches a
broken reference, while rendering here makes the published page buildable and inspectable on a
laptop — which the themed build is not.

What that buys, beyond weight: the page stops being somebody else's React application. Nothing
hydrates, so a script in the page can read and write it, which is what the interactive work has
been fighting.
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.outline import APPENDICES, CHAPTERS, PART_PAGES  # noqa: E402
from bench.stamp import shown  # noqa: E402


def _pdf():
    """The existing renderer, imported rather than copied. Its name has a dash in it."""
    spec = importlib.util.spec_from_file_location("build_pdf", ROOT / "scripts/build-pdf.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PDF = _pdf()
PDF.MEDIUM = "web"  # same renderer, different medium
DEFAULT_OUT = ROOT / "_build" / "static"


def nav() -> list[dict]:
    """The book's structure, from the outline rather than from the table of contents.

    bench/outline.py is where this book keeps what it is: parts, the chapters under them, and the
    appendices. The theme derived the same tree from myst.yml; deriving it here from the outline
    means a chapter cannot appear in the navigation without appearing in the tests that check it.
    """
    out = []
    for part in PART_PAGES:
        out.append(
            {
                "title": part.title,
                "href": href_for(part.path),
                "children": [
                    {"title": f"{c.label} · {c.title}", "href": href_for(c.path)}
                    for c in CHAPTERS
                    if c.part == part.title
                ],
            }
        )
    out.append(
        {
            "title": "Appendices",
            "href": None,
            "children": [
                {"title": f"{a.label} · {a.title}", "href": href_for(a.path)} for a in APPENDICES
            ],
        }
    )
    return out


def href_for(source: str) -> str:
    """Where a source file is published. Flat, and named for the slug a reader sees."""
    stem = Path(source).stem
    return "index.html" if source == "index.md" else f"{stem.replace('_', '-')}.html"


def contents_of(page: dict) -> list[dict]:
    """The headings on one page, for the sidebar on the right."""
    out = []
    for node in walk(page.get("mdast", page)):
        if node.get("type") == "heading" and node.get("depth") in (2, 3):
            text = "".join(t.get("value", "") for t in walk(node) if t.get("type") == "text")
            if text:
                out.append({"depth": node["depth"], "text": text, "id": slug(text)})
    return out


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def slug(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text]
    return "-".join("".join(keep).split("-")).strip("-")


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Sizing and TCO</title>
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<style>{css}</style>
</head>
<body>
<header class="top">
  <a class="brand" href="index.html">Sizing and TCO</a>
  <button id="menu" aria-label="Contents">☰</button>
</header>
<div class="shell">
  <nav id="nav" class="nav">{nav}</nav>
  <main>
{body}
  </main>
  <aside class="toc">{toc}</aside>
</div>
<script>
document.getElementById("menu").addEventListener("click", () =>
  document.getElementById("nav").classList.toggle("open"));
</script>
</body>
</html>
"""

CSS = """
:root {
  color-scheme: light dark;
  --ink: #1f2933; --muted: #52606d; --edge: #dfe3e8; --bg: #ffffff;
  --panel: #f7f9fa; --link: #1f6feb; --code: #f3f5f7;
  --measure: 46rem;
}
@media (prefers-color-scheme: dark) {
  :root { --ink: #e4e7eb; --muted: #9aa5b1; --edge: #323d47; --bg: #12181d;
          --panel: #1a2229; --link: #79b8ff; --code: #1a2229; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 17px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
a { color: var(--link); }
.top { display: flex; align-items: center; gap: 12px; padding: 10px 16px;
       border-bottom: 1px solid var(--edge); position: sticky; top: 0; background: var(--bg);
       z-index: 5; }
.brand { font-weight: 600; text-decoration: none; color: var(--ink); }
#menu { margin-left: auto; font-size: 20px; background: none; border: 1px solid var(--edge);
        border-radius: 4px; color: var(--ink); cursor: pointer; padding: 2px 10px; }
.shell { display: grid; grid-template-columns: 1fr; max-width: 1400px; margin-inline: auto; }
@media (min-width: 1000px) {
  .shell { grid-template-columns: 17rem minmax(0, 1fr) 15rem; }
  #menu { display: none; }
  .nav, .toc { display: block !important; }
}
.nav, .toc { display: none; padding: 20px 16px; font-size: 14px; }
.nav.open { display: block; }
.nav { border-right: 1px solid var(--edge); }
.toc { border-left: 1px solid var(--edge); color: var(--muted); }
.nav .part { font-weight: 600; margin: 14px 0 4px; }
.nav a, .toc a { display: block; padding: 3px 0; text-decoration: none; color: var(--muted); }
.nav a:hover, .toc a:hover { color: var(--link); }
.nav a.here { color: var(--link); font-weight: 600; }
.nav ul, .toc ul { list-style: none; margin: 0; padding: 0 0 0 10px; }
.toc .d3 { padding-left: 12px; }
main { padding: 8px 20px 80px; max-width: var(--measure); }
h1 { font-size: 1.75rem; line-height: 1.25; margin: 24px 0 8px; }
h2 { font-size: 1.3rem; margin: 32px 0 8px; }
h3 { font-size: 1.08rem; margin: 24px 0 6px; }
p, li { max-width: var(--measure); }
code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13.5px; }
code { background: var(--code); padding: 1px 4px; border-radius: 3px; }
pre { background: var(--code); padding: 12px 14px; border-radius: 4px; overflow-x: auto;
      border: 1px solid var(--edge); }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; font-size: 14.5px; margin: 14px 0; }
th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--edge);
         vertical-align: top; }
th { color: var(--muted); }
blockquote { margin: 16px 0; padding: 2px 16px; border-left: 3px solid var(--edge);
             color: var(--muted); }
figure { margin: 20px 0; }
figcaption { color: var(--muted); font-size: 14px; margin-top: 6px; }
img, svg { max-width: 100%; height: auto; }
.admonition { border: 1px solid var(--edge); border-left-width: 4px; border-radius: 4px;
              padding: 10px 14px; margin: 18px 0; background: var(--panel); font-size: 15.5px; }
.admonition-title { font-weight: 600; margin: 0 0 6px; }
.admonition.note { border-left-color: var(--link); }
.admonition.tip { border-left-color: #2e7d32; }
.admonition.important { border-left-color: #b3413a; }
iframe { width: 100%; border: 1px solid var(--edge); border-radius: 4px; height: 680px; }
@media (max-width: 720px) { iframe { height: 80vh; min-height: 540px; } }
"""


def nav_html(here: str) -> str:
    out = []
    for group in nav():
        title = html.escape(group["title"])
        head = (
            f'<div class="part"><a href="{group["href"]}">{title}</a></div>'
            if group["href"]
            else f'<div class="part">{title}</div>'
        )
        items = "".join(
            f'<li><a class="{"here" if child["href"] == here else ""}" '
            f'href="{child["href"]}">{html.escape(child["title"])}</a></li>'
            for child in group["children"]
        )
        out.append(f"{head}<ul>{items}</ul>")
    return "".join(out)


def toc_html(page: dict) -> str:
    items = contents_of(page)[1:]  # the first heading is the page's own title
    if not items:
        return ""
    body = "".join(
        f'<li class="d{item["depth"]}"><a href="#{item["id"]}">{html.escape(item["text"])}</a></li>'
        for item in items
    )
    return f'<div class="part">On this page</div><ul>{body}</ul>'


def render_page(source: str, page: dict) -> str:
    body = PDF.render(page.get("mdast", page))
    title = str(page.get("frontmatter", {}).get("title") or page.get("title") or "Sizing and TCO")
    return PAGE.format(
        title=html.escape(title),
        css=CSS,
        nav=nav_html(href_for(source)),
        toc=toc_html(page),
        body=body,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--only", help="one page, by chapter label or slug")
    args = parser.parse_args()

    index = PDF.parsed_pages()
    if not index:
        raise SystemExit("no parsed content — run `myst build` first")

    wanted = PDF.page_order()
    if args.only:
        wanted = [
            s
            for s in wanted
            if args.only in s
            or any(args.only in (c.label, c.slug) and c.path == s for c in CHAPTERS)
        ]
        if not wanted:
            raise SystemExit(f"no page matching {args.only!r}")

    args.out.mkdir(parents=True, exist_ok=True)
    for source in wanted:
        if source not in index:
            continue
        target = args.out / href_for(source)
        target.write_text(render_page(source, index[source]))
        print(f"  wrote {shown(target)} ({len(target.read_text()):,} bytes)")
    return 0


if __name__ == "__main__":  # pragma: no cover - a thin wrapper around main()
    raise SystemExit(main())
