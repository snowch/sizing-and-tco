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
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _site() -> str:
    """Where the published book lives, derived rather than typed.

    A link written ``/models/storage_cluster-reference.html`` resolves on the site and is dead on
    paper: a PDF has no site root, so the browser printing it resolves the path against the local
    filesystem. Five links in the book are written that way, and a reader holding the PDF is
    exactly the reader most likely to want the one that says "run it in your browser".

    The host comes from ``myst.yml``'s ``github``, so it cannot disagree with the repository and
    would follow it if the repository moved.
    """
    config = yaml.safe_load((ROOT / "myst.yml").read_text())
    owner, repo = config["project"]["github"].rstrip("/").split("/")[-2:]
    return f"https://{owner}.github.io/{repo}"


def _absolute(url: str) -> str:
    """A site-root link, made to work for somebody holding the PDF."""
    return _site() + url if url.startswith("/") else url


sys.path.insert(0, str(ROOT))

from bench.stamp import shown  # noqa: E402

CONTENT = ROOT / "_build" / "site" / "content"
#: Where MyST writes the assets it has content-hashed. An image URL in the parsed content points
#: here, not at the path the author wrote, which is the whole reason :func:`_image` has to look.
PUBLIC = ROOT / "_build" / "site" / "public"
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


#: Which medium is being rendered. The node types are the same; two of them are not the same
#: thing on paper as on a screen, and this is how they find out which they are.
MEDIUM = "print"

#: Where a caller may splice a run control in. The caller marks the node it should follow with
#: `_runner_here`, and this comes out in its place.
RUNNER_SLOT = "<!-- runner -->"

#: What a renderer publishing a site calls each page, keyed by the slug a site-root URL ends in.
#: Empty on paper, where there is no site to link into.
PAGES: dict[str, str] = {}


def _published(url: str) -> str | None:
    """The page this renderer is publishing for a site-root URL, if it is publishing one."""
    if MEDIUM != "web" or not url.startswith("/"):
        return None
    path, _, anchor = url.partition("#")
    target = PAGES.get(path.strip("/").rsplit("/", 1)[-1] or "index")
    return None if target is None else target + (f"#{anchor}" if anchor else "")


def heading_id(node: dict) -> str:
    """A heading's anchor, from its text, so a page's own contents can link to it."""
    words = []

    def text_of(n):
        if isinstance(n, dict):
            if n.get("type") == "text":
                words.append(str(n.get("value", "")))
            for v in n.values():
                text_of(v)
        elif isinstance(n, list):
            for x in n:
                text_of(x)

    text_of(node)
    keep = "".join(c.lower() if c.isalnum() else "-" for c in "".join(words))
    return "-".join(part for part in keep.split("-") if part)


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
        # An id only earns its place on a site, where something links to it. In one bound
        # document every heading would carry one and nothing would ever follow it.
        at = f' id="{heading_id(node)}"' if MEDIUM == "web" else ""
        return f"<h{level}{at}>{children()}</h{level}>"
    if kind == "strong":
        return f"<strong>{children()}</strong>"
    if kind == "emphasis":
        return f"<em>{children()}</em>"
    if kind == "inlineCode":
        return f"<code>{html.escape(node.get('value', ''))}</code>"
    if kind == "code" and node.get("_editable") and MEDIUM == "web":
        # The piece of the model the chapter is quoting, made editable where the chapter shows
        # it. `data-start`/`data-end` are where it sits in the whole file, so an edit here can be
        # spliced back into the document the toolkit is handed. The bar above it is the only
        # thing that says so: a block a reader may type into has to look unlike one they may not.
        span = node["_editable"]
        name = html.escape(str(node.get("filename") or "model.yaml"))
        return (
            '<div class="editable-block">'
            f'<div class="editable-bar"><span class="file">{name}</span>'
            '<span class="hint">yours to edit</span>'
            '<button class="run-here" type="button">Run</button></div>'
            '<pre class="editable" contenteditable="plaintext-only" spellcheck="false"'
            f' data-start="{span["start"]}" data-end="{span["end"]}">'
            f"<code>{html.escape(str(node.get('value', '')))}</code></pre></div>"
            + (RUNNER_SLOT if node.get("_runner_here") else "")
        )
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
    if kind == "caption":
        return f"<figcaption>{children()}</figcaption>"
    if kind == "container":
        # What `{iframe}` and `{figure}` wrap their content in: the thing itself and a caption.
        classes = " ".join(["container", *str(node.get("kind", "")).split()])
        return f'<figure class="{classes}">{children()}</figure>'
    if kind == "iframe":
        if node.get("_suppressed"):
            return RUNNER_SLOT if node.get("_runner_here") else ""
        # A panel a reader presses is nothing on paper, so in print it becomes the link it
        # embeds; on a site it is the thing itself. The caption beside it is prose either way.
        src = str(node.get("src", ""))
        if MEDIUM == "web":
            return f'<iframe src="{html.escape(src)}" loading="lazy"></iframe>'
        url = _absolute(src)
        return f'<p class="iframe-fallback">Run it at <a href="{html.escape(url)}">{html.escape(url)}</a></p>'
    if kind == "link":
        url = str(node.get("url", ""))
        return f'<a href="{html.escape(_published(url) or _absolute(url))}">{children()}</a>'
    if kind == "crossReference":
        # On paper this is its own text: there is no site to link into, and the chapter label
        # the reference carries is what a reader holding the book needs anyway. On a site it is
        # the only way across the book, so it becomes the link it always meant.
        inner = children()
        if not inner:
            return ""
        url = str(node.get("url") or "")
        anchor = str(node.get("html_id") or "")
        page = url.strip("/").rsplit("/", 1)[-1]
        target = _published(url if anchor in ("", page) else f"{url}#{anchor}")
        return (
            f'<a class="xref" href="{html.escape(target)}">{inner}</a>'
            if target
            else f"<em>{inner}</em>"
        )
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


class MissingImageError(FileNotFoundError):
    """A figure the PDF would have printed as a broken reference."""


def _image(node: dict) -> str:
    """Inline an SVG, and refuse to print a reference to a file that is not there.

    MyST rewrites every image URL to a content-hashed name under the site's public directory, so
    the URL in the parsed content is not the path the author wrote. Looking only where the author
    wrote it is how every figure in this book came to be missing from the PDF while the build
    stayed green: the fallback emitted an ``<img>`` with an absolute URL, which resolves to
    nothing when the file is printed from disk, and a missing picture makes no noise.

    Same rule as :class:`UnknownNodeError`, one node type along: content does not disappear
    quietly.
    """
    url = str(node.get("url", ""))
    for candidate in (
        ROOT / url.lstrip("/"),
        ROOT / "chapters" / url.lstrip("./"),
        PUBLIC / Path(url).name,
    ):
        if candidate.exists():
            if candidate.suffix == ".svg":
                return f"<div>{candidate.read_text()}</div>"
            return f'<img src="{html.escape(str(candidate))}" alt="{html.escape(str(node.get("alt", "")))}">'
    raise MissingImageError(
        f"the PDF renderer cannot find the image {url!r}. It is not in the repository and not "
        f"in {shown(PUBLIC)}, so the PDF would have printed a broken reference."
    )


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
        # A precondition rather than a defect: the page is in the table of contents and MyST has
        # not parsed it, which is what a stale `_build/site` looks like after a page is added.
        # Said in a sentence, like the empty-index case, because a traceback here reads as a bug
        # in the renderer and is not one.
        raise SystemExit(
            f"no parsed content for {page} — run `myst build` first. "
            f"Parsed: {', '.join(sorted(index)[:3])}..."
        )
    return index[page]


def without_repeated_tagline(page: str, description: str) -> str:
    """Drop the first page's opening line when the front page has just printed it.

    On the site the two never meet: the description is metadata there, and the preface's opening
    line is the only place a reader sees it. Bound into one document they land three lines apart,
    which reads like a mistake because it is one.
    """
    match = re.match(r"<p><em>(.*?)</em></p>", page)
    if match and description.startswith(html.unescape(match.group(1))):
        return page[match.end() :]
    return page


def assemble() -> str:
    config = yaml.safe_load((ROOT / "myst.yml").read_text())["project"]
    description = " ".join(config["description"].split())
    body = [
        '<div class="frontpage">',
        f"<h1>{html.escape(config['title'])}</h1>",
        f"<p>{html.escape(description)}</p>",
        f"<p>{html.escape(config['authors'][0]['name'])} · "
        f"{datetime.now(UTC).date().isoformat()}</p>",
        "</div>",
    ]
    index = parsed_pages()
    for position, page in enumerate(page_order()):
        rendered = render(load(page, index).get("mdast", {}))
        body.append(without_repeated_tagline(rendered, description) if position == 0 else rendered)
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
    print(f"  wrote {shown(page)} ({page.stat().st_size / 1024:.0f} KB)")
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
    print(f"  wrote {shown(args.out)} ({args.out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
