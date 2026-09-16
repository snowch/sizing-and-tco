#!/usr/bin/env python3
"""Assemble the whole book as one PDF.

    python3 scripts/build-pdf.py                 # HTML + PDF
    python3 scripts/build-pdf.py --html-only     # just the HTML, to print yourself
    python3 scripts/build-pdf.py --no-myst       # reuse the existing _build/site content

The input is **MyST's own parse output** — the JSON under ``_build/site/content/`` that
``myst build`` writes — and not the markdown. That is the point: the PDF and the website render
the same tree, so they cannot disagree about what a page says. Directives are already resolved in
it, so every ``{literalinclude}`` carries the real code from the working tree and every
``{include}`` carries the real generated table, with no second implementation of either to drift.

``myst build --pdf`` is not used because it wants a LaTeX or Typst template fetched from GitHub
plus a TeX toolchain, neither of which exists in a network-restricted environment. This path needs
only Chromium, which is also what a reader gets by pressing Print on the website.

A node type the renderer does not know about **raises**. It is never skipped. A renderer that
quietly ignores what it does not recognise drops content from the PDF, and the only symptom is a
paragraph nobody notices is missing — which is precisely the class of failure this book spends its
length complaining about. When a page starts using a new directive this fails loudly and earns one
more branch.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "_build" / "site" / "content"
OUT_DIR = ROOT / "_build" / "exports"
STEM = "sizing-and-tco"

#: Where to look for a browser, in order.
CHROMIUM = (
    "chromium",
    "/opt/pw-browsers/chromium/chrome-linux/chrome",
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "chromium-browser",
    "google-chrome",
    "google-chrome-stable",
)

STYLE = """
@page { size: A4; margin: 18mm 16mm; }
body { font: 10.5pt/1.5 Georgia, "Times New Roman", serif; color: #1f2933; margin: 0; }
h1 { font-size: 20pt; margin: 0 0 6pt; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h2 { font-size: 14pt; margin: 18pt 0 5pt; }
h3 { font-size: 11.5pt; margin: 13pt 0 4pt; }
h1, h2, h3 { font-family: Helvetica, Arial, sans-serif; page-break-after: avoid; }
p { margin: 0 0 7pt; }
code, pre { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 8.6pt; }
pre { background: #f5f7fa; border: 1px solid #cbd2d9; border-radius: 3px; padding: 7pt 9pt;
      overflow-x: auto; page-break-inside: avoid; white-space: pre-wrap; }
code { background: #f5f7fa; padding: 0 2pt; border-radius: 2px; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; font-size: 8.8pt; margin: 8pt 0;
        page-break-inside: avoid; font-family: Helvetica, Arial, sans-serif; }
th, td { border-bottom: 0.5pt solid #cbd2d9; padding: 3pt 5pt; text-align: left;
         vertical-align: top; }
th { border-bottom: 1pt solid #52606d; }
blockquote { margin: 8pt 0 8pt 12pt; padding-left: 10pt; border-left: 2pt solid #cbd2d9;
             color: #3e4c59; }
img, svg { max-width: 100%; height: auto; page-break-inside: avoid; }
.admonition { border-left: 3pt solid #4a7ba7; background: #f5f7fa; padding: 6pt 9pt; margin: 9pt 0;
              page-break-inside: avoid; font-size: 9.6pt; }
.admonition.warning { border-left-color: #b3413a; background: #fdeeed; }
.admonition-title { font-weight: 700; font-family: Helvetica, Arial, sans-serif; margin: 0 0 4pt; }
.frontpage { text-align: center; padding-top: 70mm; page-break-after: always; }
.frontpage h1 { font-size: 30pt; page-break-before: avoid; border: 0; }
.frontpage p { color: #52606d; }
a { color: inherit; text-decoration: none; }
"""


class UnknownNodeError(Exception):
    """A node type the renderer does not handle. Raised, never skipped."""


def render(node: dict) -> str:
    kind = node.get("type")
    children = lambda: "".join(render(child) for child in node.get("children", []))  # noqa: E731

    if kind == "text":
        return html.escape(node.get("value", ""))
    if kind in ("root", "block"):
        return children()
    if kind == "paragraph":
        return f"<p>{children()}</p>"
    if kind == "heading":
        level = min(int(node.get("depth", 2)), 6)
        return f"<h{level}>{children()}</h{level}>"
    if kind == "strong":
        return f"<strong>{children()}</strong>"
    if kind == "emphasis":
        return f"<em>{children()}</em>"
    if kind == "inlineCode":
        return f"<code>{html.escape(node.get('value', ''))}</code>"
    if kind == "code":
        return f"<pre><code>{html.escape(node.get('value', ''))}</code></pre>"
    if kind == "break":
        return "<br>"
    if kind == "thematicBreak":
        return "<hr>"
    if kind == "blockquote":
        return f"<blockquote>{children()}</blockquote>"
    if kind == "list":
        tag = "ol" if node.get("ordered") else "ul"
        return f"<{tag}>{children()}</{tag}>"
    if kind == "listItem":
        return f"<li>{children()}</li>"
    if kind == "table":
        return f"<table>{children()}</table>"
    if kind == "tableRow":
        return f"<tr>{children()}</tr>"
    if kind == "tableCell":
        tag = "th" if node.get("header") else "td"
        return f"<{tag}>{children()}</{tag}>"
    if kind == "link":
        return f'<a href="{html.escape(str(node.get("url", "")))}">{children()}</a>'
    if kind == "crossReference":
        # Rendered as its own text: a PDF has no site to link into, and the chapter label the
        # reference carries is what a reader on paper needs anyway.
        return f"<em>{children()}</em>" if node.get("children") else ""
    if kind == "cite":
        return f"[{children()}]" if node.get("children") else ""
    if kind == "admonition":
        classes = " ".join(["admonition", *node.get("class", "").split()])
        return f'<div class="{classes}">{children()}</div>'
    if kind == "admonitionTitle":
        return f'<p class="admonition-title">{children()}</p>'
    if kind == "image":
        return _image(node)
    if kind in ("inlineMath", "math"):
        return f"<code>{html.escape(node.get('value', ''))}</code>"
    if kind == "include":
        return children()
    if kind == "comment":
        return ""
    raise UnknownNodeError(
        f"the PDF renderer does not handle {kind!r}. Add a branch for it rather than letting the "
        "content disappear silently — see this module's docstring."
    )


def _image(node: dict) -> str:
    """Inline an SVG; leave anything else as a reference the browser will resolve."""
    url = str(node.get("url", ""))
    candidate = (ROOT / url.lstrip("/")).resolve()
    if not candidate.exists():
        candidate = (ROOT / "chapters" / url.lstrip("./")).resolve()
    if candidate.exists() and candidate.suffix == ".svg":
        return f"<div>{candidate.read_text()}</div>"
    return f'<img src="{html.escape(url)}" alt="{html.escape(str(node.get("alt", "")))}">'


def page_order() -> list[str]:
    config = yaml.safe_load((ROOT / "myst.yml").read_text())
    out = []
    for entry in config["project"]["toc"]:
        if "file" in entry:
            out.append(entry["file"])
        for child in entry.get("children", ()):
            out.append(child["file"])
    return out


def parsed_pages() -> dict[str, dict]:
    """Every parsed page, indexed by the source file it came from.

    MyST names its output by *slug* rather than by path — ``a-tco-for-finance.json`` for
    ``chapters/a_tco_for_finance.md`` — so matching on the filename works right up until two
    pages share a stem or a title changes. Each file records the source it came from, and that is
    what this indexes on.
    """
    index: dict[str, dict] = {}
    for path in sorted(CONTENT.rglob("*.json")):
        payload = json.loads(path.read_text())
        location = str(payload.get("location") or "").lstrip("/")
        if location:
            index[location] = payload
    return index


def load(page: str, index: dict[str, dict]) -> dict:
    if page not in index:
        raise FileNotFoundError(
            f"no parsed content for {page}; run `myst build` first. Parsed: {sorted(index)[:3]}..."
        )
    return index[page]


def assemble() -> str:
    config = yaml.safe_load((ROOT / "myst.yml").read_text())["project"]
    body = [
        '<div class="frontpage">',
        f"<h1>{html.escape(config['title'])}</h1>",
        f"<p>{html.escape(' '.join(config['description'].split()))}</p>",
        f"<p>{html.escape(config['authors'][0]['name'])} · "
        f"{datetime.now(UTC).date().isoformat()}</p>",
        "</div>",
    ]
    index = parsed_pages()
    for page in page_order():
        body.append(render(load(page, index).get("mdast", {})))
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{html.escape(config['title'])}</title><style>{STYLE}</style></head>"
        f"<body>{''.join(body)}</body></html>"
    )


def find_browser() -> str | None:
    for candidate in CHROMIUM:
        found = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if found:
            return found
    return None


def _shown(path: Path) -> str:
    """A path as a reader should see it: relative to the repository where it can be."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-myst", action="store_true", help="reuse _build/site content")
    parser.add_argument("--html-only", action="store_true", help="skip the browser step")
    parser.add_argument("--out", type=Path, default=OUT_DIR / f"{STEM}.pdf")
    args = parser.parse_args()
    # A relative --out is relative to the repository, not to wherever the shell happens to be.
    args.out = (ROOT / args.out).resolve() if not args.out.is_absolute() else args.out

    if not args.no_myst:
        subprocess.run(["myst", "build"], cwd=ROOT, check=True)
    if not CONTENT.exists():
        print("no parsed content under _build/site — run `myst build` first", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    page = args.out.with_suffix(".html")
    page.write_text(assemble())
    print(f"  wrote {_shown(page)} ({page.stat().st_size / 1024:.0f} KB)")
    if args.html_only:
        return 0

    browser = find_browser()
    if browser is None:
        print(
            "  no Chromium found; wrote the HTML only. `pip install playwright && "
            "playwright install chromium`, or open the HTML and print it."
        )
        return 0
    subprocess.run(
        [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={args.out}",
            page.as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    print(f"  wrote {_shown(args.out)} ({args.out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
