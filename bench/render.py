"""MyST's parse, rendered to HTML: the one renderer every page of the book goes through.

The input is **MyST's own parse output** — the JSON under ``_build/site/content/`` that
``myst build`` writes — and not the markdown. Directives are already resolved in it, so every
``{literalinclude}`` carries the real code from the working tree and every ``{include}`` carries
the real generated table, with no second implementation of either to drift.
``scripts/build-site.py`` wraps what this returns in the site's chrome and writes the pages.

A node type the renderer does not know about **raises**. It is never skipped. A renderer that
quietly ignores what it does not recognise drops content from the page, and the only symptom is
a paragraph nobody notices is missing — which is precisely the class of failure this book spends
its length complaining about. When a page starts using a new directive this fails loudly and
earns one more branch.

It was written to print a PDF the book no longer publishes. The models are things a reader
drags, and paper cannot hold one, so a service worker (``scripts/build-offline.py``) keeps the
site readable with no network instead. What the PDF left behind is the decision to render from
the parse rather than from MyST's theme, and it is why the whole site builds with no network.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import yaml

from bench.outline import APPENDICES, CHAPTERS
from bench.stamp import ROOT, shown

#: Every chapter and appendix by the anchor a cross-reference carries.
BY_ANCHOR = {item.anchor: item for item in (*CHAPTERS, *APPENDICES)}

#: A reference whose text opens with the chapter's label. The label and nothing after it: what
#: follows is the separator and the title, and both are the author's to keep.
LABELLED = re.compile(r"^(ch\d+|Appendix [A-Z])\b")


def _relabel(node: dict, text: str) -> str | None:
    """The current label for the chapter a reference points at, if its text carries one.

    ``Chapter.anchor`` already states the rule: a chapter number is a number, so it is derived
    and never typed. The prose types it anyway, because MyST resolves the *target* from the slug
    but will only fill in the whole heading, and this book says ``ch13`` inline. So the renderer
    has the last word. A reference reading ``ch13``, or ``ch13 · Monte Carlo``, is re-derived
    from the outline and cannot go stale when a chapter moves; the rest of the text is left
    exactly as written, which keeps MyST's typography in the part that is prose.
    """
    item = BY_ANCHOR.get(str(node.get("identifier") or ""))
    if item is None:
        return None
    found = LABELLED.match(text.strip())
    return item.label + text.strip()[found.end() :] if found else None


CONTENT = ROOT / "_build" / "site" / "content"
#: Where MyST writes the assets it has content-hashed. An image URL in the parsed content points
#: here, not at the path the author wrote, which is the whole reason :func:`_image` has to look.
PUBLIC = ROOT / "_build" / "site" / "public"


#: The three provenance marks, and the class each renders with. The page's font has none of
#: the geometric shapes, so a browser borrows each glyph from whatever system font has it, and
#: on a phone the full and empty circles came from one font and the half circle from another,
#: at another size. The span keeps the glyph for a screen reader and for copy-and-paste, and the
#: stylesheet draws the shape itself, so the three are the same size everywhere.
MARKS = {"\u25cf": "fact", "\u25d0": "vendor_claim", "\u25cb": "assumption"}


def _marked(text: str) -> str:
    for glyph, kind in MARKS.items():
        if glyph in text:
            text = text.replace(glyph, f'<span class="mark" data-mark="{kind}">{glyph}</span>')
    return text


class UnknownNodeError(Exception):
    """A node type the renderer does not handle. Raised, never skipped."""


#: Where a caller may splice a run control in. The caller marks the node it should follow with
#: `_runner_here`, and this comes out in its place.
RUNNER_SLOT = "<!-- runner -->"

#: What the site calls each page, keyed by the slug a site-root URL ends in. The site build fills
#: it in before it renders anything; while it is empty, a cross-reference renders as its text.
PAGES: dict[str, str] = {}


def _published(url: str) -> str | None:
    """The page this build is publishing for a site-root URL, if it is publishing one.

    One segment only. This used to take the last segment of any path, which meant
    ``/playground/capacity/`` resolved to the *chapter* named capacity — the playground
    directories are named after the chapters they belong to, so every one of them collided with
    the page it was built from. Nothing linked to one in prose, so nothing broke; a link saying
    "run it in your browser" would have gone quietly to the wrong place.

    A root-relative link into ``/models/`` or ``/playground/`` is left as written. The site is
    served under a base path this module is not told, and ``scripts/build-icons.py`` gives those
    links the base path when it injects the icons — which also leaves them where
    ``scripts/check-built-links.py`` can see them, as an absolute URL would not be.
    """
    if not url.startswith("/"):
        return None
    path, _, anchor = url.partition("#")
    segments = [part for part in path.split("/") if part]
    if len(segments) > 1:
        return None
    target = PAGES.get(segments[0] if segments else "index")
    return None if target is None else target + (f"#{anchor}" if anchor else "")


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


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
        return _marked(html.escape(node.get("value", "")))
    if kind in ("root", "block"):
        return children()
    if kind == "paragraph":
        return f"<p>{children()}</p>"
    if kind == "heading":
        level = min(int(node.get("depth", 2)), 6)
        # Every heading carries an id: the contents list beside the page and the search index
        # both link to it, and both take the id from here rather than from a second slug
        # function that agrees with this one most of the time.
        return f'<h{level} id="{heading_id(node)}">{children()}</h{level}>'
    if kind == "strong":
        return f"<strong>{children()}</strong>"
    if kind == "emphasis":
        return f"<em>{children()}</em>"
    if kind == "inlineCode":
        return f"<code>{html.escape(node.get('value', ''))}</code>"
    if kind == "code" and node.get("_editable"):
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
        # Which kind of panel this is comes from where it points, not from an option an author
        # has to remember: a viewer needs more height than a playground. The caption beside it
        # is prose and renders as prose.
        src = str(node.get("src", ""))
        kind_class = "viewer" if src.startswith("/models/") else "playground"
        return f'<iframe class="{kind_class}" src="{html.escape(src)}" loading="lazy"></iframe>'
    if kind == "link":
        url = str(node.get("url", ""))
        href = html.escape(_published(url) or url)
        if node.get("_term"):
            # A glossary term the site linked: its meaning rides as the title, which a desktop
            # shows on hover and a tablet reaches by following the link.
            return f'<a class="term" href="{href}" title="{html.escape(str(node["_term"]))}">{children()}</a>'
        return f'<a href="{href}">{children()}</a>'
    if kind == "crossReference":
        # The label is re-derived from the outline, and the reference links to the page it names
        # when this build is publishing that page. When it is not — one page built to look at —
        # it stays as text rather than becoming a link to nowhere.
        inner = children()
        if not inner:
            return ""
        plain = "".join(
            str(n.get("value", "")) for n in _walk(node) if n.get("type") in ("text", "inlineCode")
        )
        current = _relabel(node, plain)
        if current and current != plain:
            inner = html.escape(current)
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
        # The kind is a class too, so the stylesheet can tell a note from a warning. MyST keeps
        # it in `kind`, and without this every box rendered in the plain grey of no kind at all.
        classes = " ".join(
            ["admonition", *str(node.get("kind", "")).split(), *node.get("class", "").split()]
        )
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
        f"the renderer does not handle {kind!r}. Add a branch for it rather than letting the "
        "content disappear silently — see this module's docstring."
    )


class MissingImageError(FileNotFoundError):
    """A figure the page would have shown as a broken reference."""


def _image(node: dict) -> str:
    """Inline an SVG, and refuse to publish a reference to a file that is not there.

    MyST rewrites every image URL to a content-hashed name under the site's public directory, so
    the URL in the parsed content is not the path the author wrote. Looking only where the author
    wrote it is how every figure in this book once went missing while the build stayed green:
    the fallback emitted an ``<img>`` pointing at a path nothing served, and a missing picture
    makes no noise.

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
        f"the renderer cannot find the image {url!r}. It is not in the repository and not in "
        f"{shown(PUBLIC)}, so the page would have shipped a broken reference."
    )


def page_order() -> list[str]:
    """Every page in reading order: ``myst.yml``'s table of contents, flattened."""
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
