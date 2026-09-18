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
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.outline import APPENDICES, CHAPTERS, PART_PAGES  # noqa: E402
from bench.stages import stages  # noqa: E402
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


def stage_for(source: str):
    """The stage of the storage model a chapter leaves the reader with, if it has one."""
    slug = Path(source).stem
    for stage in stages():
        if stage.chapter == slug and not stage.is_the_finished_model:
            return stage
    return None


def editable_excerpts(page: dict, stage) -> list[dict]:
    """The quoted pieces of the model, marked with where each sits inside the whole file.

    The chapter shows the model in pieces, with prose between them. Those pieces are the reader's
    natural place to edit it — not a fourth copy of the file in a box below. MyST keeps the
    resolved text of a literalinclude but not its anchors, so each piece is located by finding it
    in the file the chapter's stage points at. Locating it by content alone would not do: the
    stages are subsets of one another, so the same node text appears in five files.
    """
    whole = stage.path.read_text()
    found = []
    for node in walk(page.get("mdast", page)):
        if node.get("type") != "code" or not str(node.get("filename", "")).endswith(".yaml"):
            continue
        text = str(node.get("value", ""))
        at = whole.find(text)
        if at < 0 or whole.find(text, at + 1) >= 0:
            # Not in this stage, or in it twice. Either way it is not safe to splice an edit
            # back, so the piece stays read-only rather than silently editing the wrong lines.
            continue
        node["_editable"] = {"start": at, "end": at + len(text)}
        found.append(node)
    return found


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


#: The pages whose leading heading is their own title, written out with the chapter number.
TITLED_PAGES = frozenset(c.path for c in (*CHAPTERS, *APPENDICES))


def promote_headings(page: dict) -> None:
    """Make a chapter's leading heading the page's `h1`, and move its sections up to match.

    MyST parses a chapter's title as a depth-2 heading, so without this every page has sections
    at `h3` and no `h1` at all: the document has no outline, and nothing in the type scale can
    tell a section from a subsection because they sit one step apart at the bottom of it.
    Call it after the contents list has been taken, which reads the depths as MyST wrote them.
    """
    for node in walk(page.get("mdast", page)):
        if node.get("type") == "heading":
            node["depth"] = max(1, int(node.get("depth", 1)) - 1)


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


RUNNER = r"""
<script type="application/json" id="model-whole">{whole}</script>
<script type="application/json" id="model-modules">{modules}</script>
<div id="runner" class="runner">
  <div class="bar">
    <button id="run" class="primary" type="button">Run the model</button>
    <span id="status">Change any block above, then press Run. The first press fetches Python.</span>
  </div>
  <div id="results" aria-live="polite"></div>
</div>
<script type="module">
const WHOLE = JSON.parse(document.getElementById("model-whole").textContent);
const MODULES = JSON.parse(document.getElementById("model-modules").textContent);
const $ = (id) => document.getElementById(id);
let pyodide = null, booting = null;

// The document the toolkit is handed: the file on disk, with each edited block spliced back
// into the range it came from. Later ranges first, so earlier offsets stay valid.
function assemble() {{
  const blocks = [...document.querySelectorAll("pre.editable")]
    .map((el) => ({{start: +el.dataset.start, end: +el.dataset.end, text: el.innerText}}))
    .sort((a, b) => b.start - a.start);
  let out = WHOLE;
  for (const b of blocks) out = out.slice(0, b.start) + b.text.replace(/\n$/, "") + out.slice(b.end);
  return out;
}}

async function boot() {{
  $("status").textContent = "Starting Python\u2026 about ten megabytes, once.";
  const {{ loadPyodide }} = await import("{pyodide}pyodide.mjs");
  pyodide = await loadPyodide({{ indexURL: "{pyodide}" }});
  await pyodide.loadPackage(["numpy", "micropip"]);
  await pyodide.pyimport("micropip").install(["Pint", "PyYAML"]);
  pyodide.FS.mkdirTree("/sizing/playground");
  for (const [name, source] of Object.entries(MODULES)) {{
    pyodide.FS.writeFile("/sizing/" + name, source);
  }}
  await pyodide.runPythonAsync(
    "import sys\nsys.path.insert(0, '/')\nfrom sizing.playground.driver import check");
}}

function show(result) {{
  const r = $("results");
  if (result.stage === "ok") {{
    r.innerHTML = '<p class="verdict good">It runs. These are your numbers, not the book\u2019s '
      + '\u2014 the tables above are what this repository stamped.</p>'
      + '<div class="outputs">' + result.outputs.map((name) => {{
          const n = result.nodes.find((x) => x.name === name) || {{}};
          const v = n.value == null ? "\u2014"
            : n.value.toLocaleString(undefined, {{maximumFractionDigits: Math.abs(n.value) >= 100 ? 0 : 2}});
          return `<div class="output"><div class="figure">${{v}}</div>`
               + `<div class="unit">${{n.unit || ""}}</div>`
               + `<div class="what">${{n.label || name}}</div></div>`;
        }}).join("") + "</div>";
  }} else {{
    r.textContent = "";
    const head = document.createElement("p");
    head.className = "verdict bad";
    head.textContent = result.stage === "load"
      ? "It does not load." : "It loads, and the units do not work out.";
    const list = document.createElement("ul");
    for (const problem of result.problems) {{
      const item = document.createElement("li");
      item.textContent = problem;   // a message about the reader's file is text, never markup
      list.appendChild(item);
    }}
    r.append(head, list);
  }}
}}

// A block the reader has typed in says so, so that the page shows which of its own numbers
// are no longer the book's.
for (const block of document.querySelectorAll(".editable-block")) {{
  block.querySelector("pre.editable").addEventListener("input", () => {{
    block.classList.add("changed");
    block.querySelector(".hint").textContent = "edited";
  }}, {{once: true}});
}}

async function run(from) {{
  for (const b of document.querySelectorAll("#run, .run-here")) b.disabled = true;
  try {{
    booting = booting || boot();
    await booting;
    const began = performance.now();
    pyodide.globals.set("_source", assemble());
    const result = (await pyodide.runPythonAsync("check(_source)"))
      .toJs({{dict_converter: Object.fromEntries}});
    show(result);
    $("status").textContent = "checked in " + Math.round(performance.now() - began) + "ms";
  }} catch (error) {{
    $("status").textContent = "Python did not start: " + error;
  }} finally {{
    for (const b of document.querySelectorAll("#run, .run-here")) b.disabled = false;
    // Pressed from a block, the answer is further down the page than the block is. Take the
    // reader to it rather than leaving them looking at what they typed.
    if (from === "block") $("runner").scrollIntoView({{behavior: "smooth", block: "center"}});
  }}
}}

$("run").addEventListener("click", () => run("runner"));
for (const button of document.querySelectorAll(".run-here")) {{
  button.addEventListener("click", () => run("block"));
}}
</script>
"""

#: Pinned, because an unpinned runtime changes what a reader sees without changing a line here.
PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/"

#: Every module the toolkit needs to load, typecheck and evaluate a model.
MODULES = ("__init__", "units", "expr", "dsl", "normal", "mc", "evaluate", "graph")


def toolkit() -> dict[str, str]:
    out = {f"{name}.py": (ROOT / "sizing" / f"{name}.py").read_text() for name in MODULES}
    out["playground/__init__.py"] = ""
    out["playground/driver.py"] = (ROOT / "sizing" / "playground" / "driver.py").read_text()
    return out


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
<a class="skip" href="#main">Skip to the chapter</a>
<header class="top">
  <a class="brand" href="index.html">Sizing and TCO</a>
  <button id="menu" type="button" aria-label="Contents" aria-controls="nav">☰</button>
</header>
<div class="shell">
  <nav id="nav" class="nav" aria-label="Chapters">{nav}</nav>
  <main id="main" tabindex="-1">
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
/* The figures in this book are drawn by `bench/diagrams.py`: blue-grey, with four accents that
   each mean something. The page borrows that palette so a diagram sits on the page rather than
   on top of it. Prose is a serif and every piece of furniture is a sans, which is what keeps a
   bold lead-in inside a paragraph from reading as a heading. */
:root {
  color-scheme: light dark;
  --ink: #263238; --muted: #546e7a; --faint: #8da2ac;
  --edge: #dfe5e8; --rule: #c4d0d6;
  --bg: #fdfdfc; --panel: #f2f6f7; --code: #f0f4f6; --raise: rgba(38,50,56,.06);
  --accent: #35648f; --on-accent: #ffffff; --wash: rgba(53,100,143,.09);
  --warn: #c8791a; --stop: #b3413a; --go: #2e7d32;
  --measure: 36rem;
  --top: 3.1rem;
  --chrome: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --text: Charter, "Bitstream Charter", "Sitka Text", Cambria, Georgia, serif;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, "DejaVu Sans Mono", monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #dde4e8; --muted: #9db0ba; --faint: #768993;
    --edge: #2b363c; --rule: #3d4b53;
    --bg: #14191c; --panel: #1b2327; --code: #1b2327; --raise: rgba(0,0,0,.4);
    --accent: #7fb2dd; --on-accent: #10171b; --wash: rgba(127,178,221,.14);
    --warn: #e0a34e; --stop: #e8756c; --go: #81c784;
  }
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 18px/1.62 var(--text); text-rendering: optimizeLegibility;
       -webkit-font-smoothing: antialiased; }
a { color: var(--accent); text-decoration-thickness: from-font; text-underline-offset: 2px; }
/* A cross-reference is a link the reader steps over 259 times. Underlining every one of them
   would turn the prose into a rash, so it keeps the italic it has on paper and takes a rule
   only when the reader is pointing at it. */
a.xref { font-style: italic; text-decoration: none; }
a.xref:hover { text-decoration: underline; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }
.skip { position: absolute; left: -9999px; }
.skip:focus { left: .6rem; top: .5rem; z-index: 20; background: var(--bg); padding: .4rem .7rem;
              border: 1px solid var(--accent); border-radius: 4px; font-family: var(--chrome); }

/* Header */
.top { display: flex; align-items: center; gap: 12px; height: var(--top); padding: 0 1rem;
       border-bottom: 1px solid var(--edge); position: sticky; top: 0; z-index: 5;
       background: color-mix(in srgb, var(--bg) 97%, transparent);
       backdrop-filter: saturate(1.6) blur(8px); }
.brand { font-family: var(--chrome); font-weight: 600; font-size: 15px; letter-spacing: -.01em;
         text-decoration: none; color: var(--ink); }
#menu { margin-left: auto; font: 16px/1 var(--chrome); background: none; color: var(--muted);
        border: 1px solid var(--edge); border-radius: 5px; cursor: pointer; padding: .4rem .6rem; }

/* Frame */
.shell { display: grid; grid-template-columns: minmax(0, 1fr); max-width: 82rem;
         margin-inline: auto; }
@media (min-width: 1040px) {
  .shell { grid-template-columns: 17rem minmax(0, 1fr) 14rem; }
  #menu { display: none; }
  .nav, .toc { display: block !important; position: sticky; top: var(--top);
               max-height: calc(100vh - var(--top)); overflow-y: auto;
               overscroll-behavior: contain; }
}
.nav, .toc { display: none; font: 14px/1.45 var(--chrome); padding: 1.4rem 1rem 3rem; }
.nav.open { display: block; }
.nav { border-right: 1px solid var(--edge); }
.toc { border-left: 1px solid var(--edge); }
.nav .part, .toc .part { font-size: 11.5px; font-weight: 600; letter-spacing: .08em;
                         text-transform: uppercase; color: var(--faint);
                         margin: 1.5rem 0 .45rem; }
.nav .part:first-child, .toc .part { margin-top: 0; }
.nav .part a { color: inherit; text-decoration: none; }
.nav ul, .toc ul { list-style: none; margin: 0; padding: 0; }
.nav a, .toc a { display: block; text-decoration: none; color: var(--muted);
                 border-radius: 4px; }
.nav a { padding: .28rem .5rem .28rem .7rem; border-left: 2px solid transparent;
         margin-left: -.2rem; }
.nav a:hover, .toc a:hover { color: var(--ink); background: var(--panel); }
.nav a.here { color: var(--accent); font-weight: 600; border-left-color: var(--accent);
              background: var(--wash); }
.toc a { padding: .26rem .45rem; }
.toc .d3 a { padding-left: 1.2rem; font-size: 13.5px; }

/* Prose */
main { padding: 1rem clamp(1rem, 4vw, 2.6rem) 6rem; max-width: calc(var(--measure) + 5rem);
       min-width: 0; }
main :is(h1, h2, h3, h4) { font-family: var(--chrome); letter-spacing: -.012em;
                           scroll-margin-top: calc(var(--top) + 1rem); }
h1 { font-size: clamp(1.6rem, 5.4vw, 2rem); font-weight: 700; line-height: 1.18;
     margin: 1.6rem 0 1.4rem; }
h2 { font-size: 1.35rem; font-weight: 650; line-height: 1.25; margin: 2.5rem 0 .9rem;
     padding-top: 1.1rem; border-top: 1px solid var(--edge); }
h3 { font-size: 1.04rem; font-weight: 700; line-height: 1.3; margin: 1.9rem 0 .6rem; }
h4 { font-size: .95rem; font-weight: 600; color: var(--muted); margin: 1.6rem 0 .4rem; }
p, li { max-width: var(--measure); }
p { margin: 0 0 1.05rem; }
ul, ol { padding-left: 1.4rem; }
li { margin-bottom: .35rem; }
blockquote { margin: 1.4rem 0; padding: .1rem 0 .1rem 1.1rem;
             border-left: 2px solid var(--rule); color: var(--muted); }
hr { border: 0; border-top: 1px solid var(--edge); margin: 2.4rem 0; }

/* Code */
code, pre, kbd { font-family: var(--mono); }
code { font-size: .85em; background: var(--code); padding: .08em .3em; border-radius: 3px;
       overflow-wrap: break-word; }   /* a test path is one long token, and phones are narrow */
pre { font-size: 13.5px; line-height: 1.55; background: var(--code); color: var(--ink);
      padding: .85rem 1rem; border-radius: 6px; border: 1px solid var(--edge);
      margin: 1.3rem 0; white-space: pre; overflow-x: auto; overscroll-behavior-x: contain; }
pre code { background: none; border: 0; padding: 0; font-size: inherit; }

/* Tables are data, not prose, so they take the furniture face and lining figures. */
table { display: block; width: max-content; max-width: 100%; overflow-x: auto;
        overscroll-behavior-x: contain; border-collapse: collapse; margin: 1.3rem 0;
        font: 14.5px/1.45 var(--chrome); font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: .42rem .7rem; border-bottom: 1px solid var(--edge);
         vertical-align: top; }
/* MyST writes bare rows, with no `thead` for a header-row selector to hang off. */
th { font-size: 11.5px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase;
     color: var(--faint); border-bottom: 1px solid var(--rule); padding-bottom: .3rem; }
tr:last-child td { border-bottom: 1px solid var(--rule); }

/* Pictures */
figure { margin: 1.8rem 0; }
figcaption { font: 14px/1.45 var(--chrome); color: var(--muted); margin-top: .5rem;
             max-width: var(--measure); }
img, svg { max-width: 100%; height: auto; }
figure img { background: #fff; border-radius: 4px; }
.admonition { border: 1px solid var(--edge); border-left: 3px solid var(--rule); border-radius: 6px;
              padding: .8rem 1rem; margin: 1.5rem 0; background: var(--panel); font-size: .94em; }
.admonition > :last-child { margin-bottom: 0; }
.admonition-title { font: 600 13px/1.4 var(--chrome); letter-spacing: .04em;
                    text-transform: uppercase; color: var(--muted); margin: 0 0 .4rem; }
.admonition.note { border-left-color: var(--accent); }
.admonition.tip { border-left-color: var(--go); }
.admonition.important { border-left-color: var(--stop); }
iframe { width: 100%; border: 1px solid var(--rule); border-radius: 6px; height: 680px; }
@media (max-width: 720px) { iframe { height: 80vh; min-height: 540px; } }

/* A quoted piece of the model the reader may edit where the chapter shows it. Nothing but the
   bar above it says so, so the bar has to carry its weight: what file this is, that it is
   theirs, and the button that acts on it. */
.editable-block { margin: 1.4rem 0; border: 1px solid var(--rule); border-radius: 6px;
                  background: var(--bg); overflow: hidden; }
.editable-block:focus-within { border-color: var(--accent);
                               box-shadow: 0 0 0 3px var(--wash); }
.editable-bar { display: flex; align-items: center; gap: .6rem; padding: .3rem .4rem .3rem .9rem;
                background: var(--panel); border-bottom: 1px solid var(--edge);
                font: 12.5px/1.6 var(--chrome); }
.editable-bar .file { font-family: var(--mono); font-size: 11.5px; color: var(--muted); }
.editable-bar .hint { color: var(--faint); }
.editable-block.changed .editable-bar { background: var(--wash); }
.editable-block.changed .editable-bar .hint { color: var(--accent); font-weight: 600; }
pre.editable { margin: 0; border: 0; border-radius: 0; background: var(--bg);
               caret-color: var(--accent); white-space: pre-wrap; overflow-wrap: break-word; }
pre.editable:focus { outline: none; }

/* Buttons */
button { font: 14px/1 var(--chrome); cursor: pointer; border-radius: 5px;
         border: 1px solid var(--rule); background: var(--bg); color: var(--ink);
         padding: .45rem .8rem; }
button:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
button:disabled { opacity: .45; cursor: progress; }
button.primary { background: var(--accent); border-color: transparent; color: var(--on-accent);
                 font-weight: 600; padding: .55rem 1.1rem; }
button.primary:hover:not(:disabled) { color: var(--on-accent); filter: brightness(1.1); }
.run-here { margin-left: auto; padding: .25rem .7rem; font-size: 12.5px; }

/* The run control, spliced in after the last block of the model the chapter quotes. */
.runner { margin: 1.8rem 0 2.4rem; border: 1px solid var(--rule); border-radius: 8px;
          background: var(--panel); padding: 1rem 1.1rem; }
.runner .bar { display: flex; gap: .9rem; align-items: center; flex-wrap: wrap; }
#status { font: 13.5px/1.4 var(--chrome); color: var(--muted); }
.verdict { font: 600 15px/1.4 var(--chrome); margin: 1rem 0 .3rem; }
.verdict.good { color: var(--go); }
.verdict.bad { color: var(--stop); }
#results > .verdict + * { margin-top: .5rem; }
.outputs { display: grid; gap: .9rem; margin-top: .9rem;
           grid-template-columns: repeat(auto-fill, minmax(8.5rem, 1fr)); }
.output { border-top: 2px solid var(--rule); padding-top: .45rem; }
.output .figure { font: 700 26px/1.1 var(--chrome); font-variant-numeric: tabular-nums;
                  letter-spacing: -.02em; }
.output .unit { font: 12px/1.4 var(--chrome); color: var(--faint); }
.output .what { font: 13px/1.35 var(--chrome); color: var(--muted); margin-top: .15rem; }
#results ul { margin: 0; padding: .7rem 1rem .7rem 2rem; list-style: square;
              background: var(--bg); border: 1px solid var(--edge); border-radius: 6px; }
#results li { font-family: var(--mono); font-size: 12.5px; line-height: 1.5; color: var(--stop);
              margin-bottom: .3rem; }
#results li::marker { color: var(--stop); }

figure > .runner { margin: 0; }

/* On paper the furniture is noise and the controls do nothing. */
@media print {
  .top, .nav, .toc, .runner, .editable-bar { display: none; }
  .shell { display: block; }
  main { max-width: none; padding: 0; }
  .editable-block { border: 1px solid #ccc; }
  a { color: inherit; }
}
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
    # Editable excerpts have to be marked before the body is rendered, because the renderer
    # decides from the mark whether a quoted block is a picture of the file or the file itself.
    stage = stage_for(source)
    blocks = editable_excerpts(page, stage) if stage else []
    if blocks:
        # The chapter's `{iframe}` is the same toolkit in a box, so with the model editable in
        # place it comes out: two Run buttons is worse than one. The run control takes its slot
        # rather than the end of the page, because the prose around the panel already introduces
        # it — press this, change a number, watch the total move. Failing a panel, the control
        # goes after the last piece of the file, which is where the reader has all of it.
        panels = [n for n in walk(page.get("mdast", page)) if n.get("type") == "iframe"]
        for node in panels:
            node["_suppressed"] = True
        (panels[0] if panels else blocks[-1])["_runner_here"] = True
    toc = toc_html(page)  # taken before the promotion below, which renumbers what it reads
    if source in TITLED_PAGES:
        promote_headings(page)
    body = PDF.render(page.get("mdast", page))
    if source not in TITLED_PAGES:
        # The introduction and the part pages carry their name in the front matter and nowhere
        # in the text, so the page opens on a blockquote with nothing above it saying where
        # the reader is.
        body = f"<h1>{html.escape(str(page.get('frontmatter', {}).get('title') or ''))}</h1>" + body
    if blocks:
        runner = RUNNER.format(
            whole=json.dumps(stage.path.read_text()),
            modules=json.dumps(toolkit()),
            pyodide=PYODIDE,
        )
        body = body.replace(PDF.RUNNER_SLOT, runner, 1)
    title = str(page.get("frontmatter", {}).get("title") or page.get("title") or "Sizing and TCO")
    return PAGE.format(
        title=html.escape(title),
        css=CSS,
        nav=nav_html(href_for(source)),
        toc=toc,
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

    # What each page is called here, so a cross-reference resolves to this build rather than to
    # the themed site it was parsed for.
    PDF.PAGES = {Path(href_for(s)).stem: href_for(s) for s in wanted}

    args.out.mkdir(parents=True, exist_ok=True)
    favicon = ROOT / "public" / "favicon.svg"
    if favicon.exists():
        (args.out / "favicon.svg").write_text(favicon.read_text())
    for source in wanted:
        if source not in index:
            continue
        target = args.out / href_for(source)
        target.write_text(render_page(source, index[source]))
        print(f"  wrote {shown(target)} ({len(target.read_text()):,} bytes)")
    return 0


if __name__ == "__main__":  # pragma: no cover - a thin wrapper around main()
    raise SystemExit(main())
