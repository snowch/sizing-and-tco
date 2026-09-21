#!/usr/bin/env python3
"""The book as static pages, rendered from MyST's parse rather than MyST's theme.

    python3 scripts/build-site.py                    # every page, into _build/static/
    python3 scripts/build-site.py --only ch02        # one page, to look at
    python3 scripts/build-site.py --out DIR

This is the published site, not a preview of one: the deploy runs this file against the same
parse ``make check`` does. It rests on two facts:

**The renderer is ``bench/render.py``.** It walks MyST's AST and emits HTML, and it raises on a
node type it does not know, so content cannot silently disappear. This module wraps what it
returns in the site's chrome — navigation, contents, search, the run control — and writes the
pages.

**The half of MyST that matters runs offline.** ``myst build --strict`` without ``--html``
produces the AST and resolves all of the book's cross-references; only the *theme* needs the
template registry. So keeping MyST as a parser costs nothing and keeps the check that catches a
broken reference, while rendering here makes the published page buildable and inspectable on a
laptop — which the themed build was not.

What that buys, beyond weight: the page is not somebody else's React application. Nothing
hydrates, so a script in the page can read and write it, which is what every interactive part of
the book depends on.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench import render as renderer  # noqa: E402
from bench.outline import APPENDICES, BY_SLUG, CHAPTERS, PART_PAGES  # noqa: E402
from bench.stages import stages  # noqa: E402
from bench.stamp import shown  # noqa: E402
from bench.tables import GLOSSARY  # noqa: E402
from sizing.dsl import load_model  # noqa: E402
from sizing.playground.toolkit import (  # noqa: E402
    BOOT,
    PYODIDE,
    offline_manifest,
    problem_chapters,
    problem_files,
    problem_pieces,
    problem_wheels,
    results_for,
    sources,
    wheels,
)

DEFAULT_OUT = ROOT / "_build" / "static"


def stage_for(source: str):
    """The stage of the running example a chapter leaves the reader with, if it has one."""
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


#: The command under a tested problem, as every chapter writes it. ``-m problem`` is part of the
#: form rather than optional: it runs the reader's tests and deselects the book's own, which is
#: what the Check on the page counts, so a desk and the page give the same verdict. A command
#: written without it does not match, and the problem loses its Check, which a test catches.
COMMAND = re.compile(r"python3 -m pytest (tests/[a-z_]+/test_problem_\d+_[a-z_]+\.py) -m problem")


def problem_excerpts(source: str, page: dict) -> list[dict]:
    """The command under each tested problem, marked with the piece of the stubs file it grades.

    A chapter's problems are tests, and under each one the chapter writes the command that runs
    it. The command names the test file; the test file imports what it grades from the stubs
    file beside it; so the page can put that piece under the problem, editable, with a button
    that runs the same test here. The command stays on the page as a one-line note under the
    Check, because at a desk it is the same check. The last problem in every chapter has no
    test, so no command, and gets nothing.
    """
    slug = Path(source).stem
    if slug not in problem_chapters():
        return []
    graded = {block["test"]: block for block in problem_pieces(slug)}
    whole = (ROOT / "tests" / slug / "stubs.py").read_text()
    found = []
    for node in walk(page.get("mdast", page)):
        if node.get("type") != "code":
            continue
        match = COMMAND.fullmatch(str(node.get("value", "")).strip())
        if not match or match.group(1) not in graded:
            continue
        block = graded[match.group(1)]
        node["_problem"] = {
            "test": block["test"],
            "stubs": block["stubs"],
            "pieces": [
                {**piece, "text": whole[piece["start"] : piece["end"]]} for piece in block["pieces"]
            ],
            "files": block["files"],
        }
        found.append(node)
    return found


def problem_set(slug: str) -> str:
    """What a chapter's Check fetches: the toolkit's modules and every file its tests read.

    A file beside the pages rather than a script inside one, because a test that reads a stamped
    model result reads half a megabyte of it, and a reader who never presses Check should not
    carry that in the page. The worker keeps it with the pages, so it is there offline.
    """
    return json.dumps(
        {"modules": sources(), "files": problem_files(slug)},
        ensure_ascii=False,
        separators=(",", ":"),
    )


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
#: The glossary: the page term links point at, and the one page they are never added to.
GLOSSARY_PAGE = next(a.path for a in APPENDICES if a.anchor == "appendix-g-glossary")


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


def title_for(source: str, page: dict) -> str:
    """What this page is called: in the navigation, in the tab, and in a search result."""
    for item in (*CHAPTERS, *APPENDICES):
        if item.path == source:
            return f"{item.label} \u00b7 {item.title}"
    return str(page.get("frontmatter", {}).get("title") or "Sizing and TCO")


def href_for(source: str) -> str:
    """Where a source file is published. Flat, and named for the slug a reader sees."""
    stem = Path(source).stem
    return "index.html" if source == "index.md" else f"{stem.replace('_', '-')}.html"


#: Node types whose text is never a glossary link: code, headings, and text that is already a
#: link or a title.
UNLINKED = frozenset(
    {"inlineCode", "code", "link", "crossReference", "heading", "admonitionTitle", "image"}
)


def term_id(term: str) -> str:
    """The anchor a glossary row carries, and a term link points at."""
    return "term-" + re.sub(r"[^a-z]+", "-", term.lower()).strip("-")


def link_terms(source: str, page: dict) -> None:
    """Link the first mention of each glossary term to its entry, on pages after its chapter.

    The vocabulary ration says a term arrives where a model needs it and never as a definition,
    so a page gets the link only when it comes after the chapter that introduces the term in
    the reading order, and the text it links is the page's own. The meaning rides as the link's
    title. Nothing inside code, a heading, an existing link or a box's title is touched, and the
    glossary itself is left alone.
    """
    order = renderer.page_order()
    if source not in order or source == GLOSSARY_PAGE:
        return
    position = order.index(source)
    linkable = {
        term: meaning
        for term, (slug, meaning, _plain) in GLOSSARY.items()
        if order.index(BY_SLUG[slug].path) < position
    }
    if not linkable:
        return
    longest_first = sorted(linkable, key=len, reverse=True)
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(term) for term in longest_first) + r")(s?)\b", re.IGNORECASE
    )
    _link_in(page.get("mdast", page), pattern, linkable, set())


def _link_in(node, pattern: re.Pattern, linkable: dict[str, str], done: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _link_in(item, pattern, linkable, done)
        return
    if not isinstance(node, dict) or node.get("type") in UNLINKED:
        return
    children = node.get("children")
    if not isinstance(children, list):
        return
    out = []
    for child in children:
        if isinstance(child, dict) and child.get("type") == "text":
            out.extend(_split_text(child, pattern, linkable, done))
        else:
            _link_in(child, pattern, linkable, done)
            out.append(child)
    node["children"] = out


def _split_text(text: dict, pattern: re.Pattern, linkable: dict[str, str], done: set[str]) -> list:
    """The text node as it was, or cut around the first mention of each term still unlinked."""
    value = str(text.get("value", ""))
    pieces, last = [], 0
    for match in pattern.finditer(value):
        term = match.group(1).lower()
        if term in done:
            continue
        done.add(term)
        if match.start() > last:
            pieces.append({"type": "text", "value": value[last : match.start()]})
        pieces.append(
            {
                "type": "link",
                "url": f"/{Path(GLOSSARY_PAGE).stem.replace('_', '-')}#{term_id(term)}",
                "_term": linkable[term],
                "children": [{"type": "text", "value": match.group(0)}],
            }
        )
        last = match.end()
    if not pieces:
        return [text]
    if last < len(value):
        pieces.append({"type": "text", "value": value[last:]})
    return pieces


def anchor_glossary_rows(body: str) -> str:
    """Give each row of the rendered glossary table the id its term links point at."""
    return re.sub(
        r"<tr><td><strong>([^<]+)</strong>",
        lambda m: f'<tr id="{term_id(m.group(1))}"><td><strong>{m.group(1)}</strong>',
        body,
    )


def builds_on(source: str) -> str:
    """One line under a chapter's title naming the chapters it assumes, from the outline.

    The outline records what each chapter needs and a test holds it pointing backwards; until
    now nothing showed it to a reader. The line is derived here rather than typed into the
    page, for the reason every chapter number is: typed, it would go stale the first time a
    chapter moved or a dependency changed.
    """
    chapter = next((c for c in CHAPTERS if c.path == source), None)
    if chapter is None or not chapter.needs:
        return ""
    by_slug = {c.slug: c for c in CHAPTERS}
    links = [
        f'<a href="{href_for(by_slug[slug].path)}" title="{html.escape(by_slug[slug].title)}">'
        f"{by_slug[slug].label}</a>"
        for slug in chapter.needs
    ]
    joined = links[0] if len(links) == 1 else ", ".join(links[:-1]) + " and " + links[-1]
    return f'<p class="builds-on">Builds on {joined}.</p>'


def contents_of(page: dict) -> list[dict]:
    """The headings on one page, for the sidebar on the right.

    The anchor comes from the renderer that writes the heading, not from a second slug function
    that agrees with it most of the time. The two did disagree: one collapsed a run of
    punctuation and the other did not, so every heading with a comma or a dash in it had a
    contents entry pointing at an id that was never written.
    """
    out = []
    for node in walk(page.get("mdast", page)):
        if node.get("type") == "heading" and node.get("depth") in (2, 3):
            text = "".join(t.get("value", "") for t in walk(node) if t.get("type") == "text")
            if text:
                out.append({"depth": node["depth"], "text": text, "id": renderer.heading_id(node)})
    return out


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def in_order(node):
    """Every node, in the order a reader meets it. `walk` does not promise that; sections do."""
    if isinstance(node, dict):
        yield node
        for child in node.get("children") or []:
            yield from in_order(child)
    elif isinstance(node, list):
        for item in node:
            yield from in_order(item)


#: Text that belongs to a section rather than describing one. A code block is in: a reader
#: looking for `horizon_periods` is looking for the model file, not for the prose around it.
SEARCHABLE = ("text", "inlineCode", "code")


def sections_of(source: str, page: dict, title: str, href: str) -> list[dict]:
    """One record per section of one page, for the whole-book index.

    Section-level rather than page-level, because a hit in ch13 is no use unless it says *where*
    in ch13. Built before `promote_headings` runs, so the depths are still MyST's.
    """
    out = [{"p": title, "h": "", "u": href, "t": []}]
    # A chapter's leading heading is its own title, and belongs to the page record rather than
    # standing as a section of it. Recognised by position, not by comparing it with the title:
    # MyST curls the apostrophe in "Little's law" and the outline does not.
    skip_first = source in TITLED_PAGES
    titles: set[int] = set()  # nodes inside a heading: they name the section, they are not in it
    for node in in_order(page.get("mdast", page)):
        if id(node) in titles:
            continue
        kind = node.get("type")
        if kind == "heading":
            titles.update(id(n) for n in in_order(node) if n is not node)
            text = "".join(t.get("value", "") for t in in_order(node) if t.get("type") == "text")
            if not text:
                continue
            if skip_first:
                skip_first = False
                continue
            anchor = renderer.heading_id(node)
            out.append({"p": title, "h": text, "u": f"{href}#{anchor}", "t": []})
        elif kind in SEARCHABLE:
            value = str(node.get("value", "")).strip()
            if value:
                out[-1]["t"].append(value)
    for record in out:
        record["t"] = " ".join(record["t"])
    if not out[0]["t"] and len(out) > 1:
        # A chapter opens on its title and then straight into its first section, so the record
        # standing for the whole page has nothing to show. Borrow the opening prose: searching a
        # chapter's name should land on the chapter, not on whichever section says it most often.
        out[0]["t"] = out[1]["t"][:400]
    # A heading with no prose under it is a container for the sections below, and those are
    # indexed in their own right. A result with nothing to quote is not worth offering.
    return [r for r in out if r["t"]]


RUNNER = r"""
<script type="application/json" id="model-whole">{whole}</script>
<script type="application/json" id="model-modules">{modules}</script>
<script type="application/json" id="model-results">{results}</script>
<script type="application/json" id="model-wheels">{wheels}</script>
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
const RESULTS = JSON.parse(document.getElementById("model-results").textContent);
const WHEELS = JSON.parse(document.getElementById("model-wheels").textContent);
const $ = (id) => document.getElementById(id);
let pyodide = null, booting = null;

// The document the toolkit is handed: the file on disk, with each edited block spliced back
// into the range it came from. Later ranges first, so earlier offsets stay valid.
function assemble() {{
  const blocks = [...document.querySelectorAll("pre.model")]
    .map((el) => ({{start: +el.dataset.start, end: +el.dataset.end, text: el.innerText}}))
    .sort((a, b) => b.start - a.start);
  let out = WHOLE;
  for (const b of blocks) out = out.slice(0, b.start) + b.text.replace(/\n$/, "") + out.slice(b.end);
  return out;
}}

async function boot() {{
  pyodide = await shareToolkit({{
    pyodideUrl: "{pyodide}", modules: MODULES, results: RESULTS, wheels: WHEELS,
    status: (text) => {{ $("status").textContent = text; }},
  }});
}}

function show(result) {{
  const r = $("results");
  if (result.stage === "ok") {{
    // Whose numbers these are. Untouched, the file is the chapter's and so are the figures;
    // once a block has been edited, the chapter's tables no longer describe this file.
    const verdict = assemble() === WHOLE
      ? "It runs. This is the file as the chapter left it."
      : "It runs. These numbers are for the file as you have changed it; the chapter\u2019s "
        + "tables are for the file as it left it.";
    r.innerHTML = '<p class="verdict good">' + verdict + '</p>'
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
for (const pre of document.querySelectorAll("pre.model")) {{
  const block = pre.closest(".editable-block");
  pre.addEventListener("input", () => {{
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


#: The runtime URL, the module list and the boot script come from one place,
#: sizing/playground/toolkit.py, and the boot goes into the page's head once, as a plain script,
#: so that the run control and the problems' checks, each a module of its own, share it.
BOOT_SCRIPT = f"<script>\n{BOOT}\n</script>"

#: The check under each tested problem. The chapter's tests, the model files they name and the
#: toolkit's modules come in one fetch on the first Check; pytest and what it imports are exact
#: wheels, pinned beside Pint's; and the verdict is pytest's own, test by test. Passed into the
#: page by replacement rather than through `.format`, so its braces are its own.
PROBLEMS = r"""
<script type="application/json" id="problem-spec">__SPEC__</script>
<script type="module">
// Not "problems": every heading carries an id made from its text, and the chapter's
// "## Problems" heading already has that one.
const SPEC = JSON.parse(document.getElementById("problem-spec").textContent);
let ready = null;

// The stubs file the tests import from: the file as the chapter ships it, with each piece the
// reader has typed into spliced back into the range it came from. Later ranges first, so earlier
// offsets stay valid. The same splice the model's Run does.
function assembleStubs() {
  const pieces = [...document.querySelectorAll("pre.stub")]
    .map((el) => ({start: +el.dataset.start, end: +el.dataset.end, text: el.innerText}))
    .sort((a, b) => b.start - a.start);
  let out = SPEC.whole;
  for (const p of pieces) out = out.slice(0, p.start) + p.text.replace(/\n$/, "") + out.slice(p.end);
  return out;
}

// The files a reader edits whole, a model fragment or a fixture, as the grader writes them:
// path under the tests' root to what the block now holds.
function assembleFiles() {
  const out = {};
  for (const el of document.querySelectorAll("pre.stub-file")) {
    out[el.dataset.path] = el.innerText.replace(/\n$/, "") + "\n";
  }
  return out;
}

// The chapter's problem set, then the runtime this tab may already have started for the model,
// then the test runner. Each once per page, whichever Check is pressed first.
async function boot(say) {
  say("Fetching the chapter\u2019s tests\u2026");
  const response = await fetch(SPEC.set);
  if (!response.ok) throw new Error(SPEC.set + " " + response.status);
  const set = await response.json();
  const pyodide = await shareToolkit({
    pyodideUrl: SPEC.pyodide, modules: set.modules, results: {}, wheels: SPEC.wheels,
    files: set.files, status: say,
  });
  say("Fetching the test runner\u2026");
  await pyodide.loadPackage(SPEC.runner);
  await pyodide.runPythonAsync("from sizing.playground.driver import grade");
  return pyodide;
}

function put(parent, tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text) el.textContent = text;   // a message about the reader's file is text, never markup
  parent.appendChild(el);
  return el;
}

function list(box, tests) {
  const ul = put(box, "ul", "tests");
  for (const t of tests) {
    const item = put(ul, "li", t.outcome);
    put(item, "span", "name", t.name);
    if (t.message) put(item, "pre", "trace", t.message);
    if (t.output) put(item, "pre", "printed", t.output);
  }
}

// A test file holds the reader's tests, marked `problem`, and the book's own scaffolding
// beside them, which asserts that the problem is answerable at all. Only the first kind is
// the reader's to pass, so only that kind is counted: counting both told a reader who had
// typed nothing that four of six tests passed. A scaffolding test that fails is a fault in
// the book, and is shown separately as one. Kept apart from the drawing so a test can run it.
function score(tests) {
  const yours = tests.filter((t) => t.problem);
  const passed = yours.filter((t) => t.outcome === "passed").length;
  const book = tests.filter((t) => !t.problem && t.outcome !== "passed");
  return {yours, passed, book, solved: yours.length > 0 && passed === yours.length};
}

function show(problem, report) {
  const box = problem.querySelector(".verdicts");
  box.textContent = "";
  if (report.problems.length) {
    put(box, "p", "verdict bad", "The tests could not start.");
    for (const p of report.problems) put(box, "pre", "trace", p.message);
  } else {
    const {yours, passed, book, solved} = score(report.tests);
    put(box, "p", "verdict " + (solved ? "good" : "bad"),
        solved ? "Solved. Every test passes." : passed + " of " + yours.length + " tests pass.");
    list(box, yours);
    if (book.length) {
      put(box, "p", "verdict bad",
          "The book's own checks failed here. That is a fault in the book, not in your answer.");
      list(box, book);
    }
  }
  const all = put(box, "details", "all");
  put(all, "summary", "", "Everything pytest said");
  put(all, "pre", "terminal", report.output);
}

async function check(problem) {
  const buttons = document.querySelectorAll(".check-here");
  for (const b of buttons) b.disabled = true;
  const box = problem.querySelector(".verdicts");
  const say = (text) => { box.textContent = text; };
  try {
    ready = ready || boot(say);
    const pyodide = await ready;
    say("Checking\u2026");
    pyodide.globals.set("_stubs", assembleStubs());
    pyodide.globals.set("_test", problem.dataset.test);
    pyodide.globals.set("_files", JSON.stringify(assembleFiles()));
    show(problem, JSON.parse(await pyodide.runPythonAsync("grade(_stubs, _test, files=_files)")));
  } catch (error) {
    box.textContent = "Python did not start: " + error;
  } finally {
    for (const b of buttons) b.disabled = false;
  }
}

for (const problem of document.querySelectorAll(".problem")) {
  for (const pre of problem.querySelectorAll("pre.stub, pre.stub-file")) {
    const block = pre.closest(".editable-block");
    pre.addEventListener("input", () => {
      block.classList.add("changed");
      block.querySelector(".hint").textContent = "edited";
    }, {once: true});
  }
  for (const button of problem.querySelectorAll(".check-here")) {
    button.addEventListener("click", () => check(problem));
  }
}
</script>
"""


#: Whole-book search, over `search.json`. Not an inverted index: the book's prose is 300 KB, so
#: matching the text directly is smaller than an index over it and there is nothing to keep in
#: step. Passed into the page as a value, never through `.format`, so its braces are its own.
SEARCH = r"""<script>
(() => {
  const dialog = document.getElementById("find");
  const box = document.getElementById("find-q");
  const list = document.getElementById("find-results");
  const opener = document.getElementById("find-open");
  let index = null, fetching = null, chosen = 0;
  opener.hidden = false;   // it does nothing without this script, so it is not there without it

  const typing = (el) =>
    !!el && (el.isContentEditable || /^(input|textarea|select)$/i.test(el.tagName));

  function open() {
    if (!dialog.open) dialog.showModal();
    box.focus();
    box.select();
    fetching = fetching || fetch("search.json")
      .then((r) => r.json())
      .then((d) => { index = d; draw(); })
      .catch(() => { index = []; draw(); });
    draw();
  }

  opener.addEventListener("click", open);
  document.addEventListener("keydown", (event) => {
    if (dialog.open || typing(document.activeElement)) return;
    if (event.key === "/" || ((event.metaKey || event.ctrlKey) && event.key === "k")) {
      event.preventDefault();
      open();
    }
  });

  // The book's own prose, so `<` in it is text. Built as nodes rather than markup for that
  // reason, with each matched run wrapped where it falls.
  function into(parent, text, terms) {
    const low = text.toLowerCase();
    let at = 0;
    while (at < text.length) {
      let next = -1, width = 0;
      for (const term of terms) {
        const found = low.indexOf(term, at);
        if (found >= 0 && (next < 0 || found < next)) { next = found; width = term.length; }
      }
      if (next < 0) break;
      parent.appendChild(document.createTextNode(text.slice(at, next)));
      const hit = document.createElement("mark");
      hit.textContent = text.slice(next, next + width);
      parent.appendChild(hit);
      at = next + width;
    }
    parent.appendChild(document.createTextNode(text.slice(at)));
  }

  function excerpt(text, terms) {
    const low = text.toLowerCase();
    let first = -1;
    for (const term of terms) {
      const found = low.indexOf(term);
      if (found >= 0 && (first < 0 || found < first)) first = found;
    }
    const from = first < 0 ? 0 : Math.max(0, first - 60);
    const cut = text.slice(from, from + 200);
    return (from > 0 ? "\u2026" : "") + cut + (from + 200 < text.length ? "\u2026" : "");
  }

  function score(record, terms) {
    const heading = (record.h || "").toLowerCase();
    const body = (record.t || "").toLowerCase();
    const page = record.p.toLowerCase();
    const all = page + " " + heading + " " + body;
    if (!terms.every((term) => all.includes(term))) return 0;
    let points = 1;
    for (const term of terms) {
      if (heading.includes(term)) points += 40;
      if (page.includes(term)) points += record.h ? 25 : 70;
      points += Math.min(8, body.split(term).length - 1);
    }
    return points;
  }

  function say(message) {
    const note = document.createElement("p");
    note.className = "find-note";
    note.textContent = message;
    list.appendChild(note);
  }

  function draw() {
    const query = box.value.trim().toLowerCase();
    list.textContent = "";
    chosen = 0;
    if (!query) { say("Type to search the book. Enter opens, Esc closes."); return; }
    if (!index) { say("Fetching the index\u2026"); return; }
    const terms = query.split(/\s+/).filter(Boolean);
    const hits = index
      .map((record) => [score(record, terms), record])
      .filter(([points]) => points > 0)
      .sort((a, b) => b[0] - a[0])
      .slice(0, 40);
    if (!hits.length) { say("Nothing in the book matches that."); return; }
    for (const [, record] of hits) {
      const link = document.createElement("a");
      link.className = "hit";
      link.href = record.u;
      const where = document.createElement("div");
      where.className = "where";
      where.appendChild(document.createTextNode(record.p));
      if (record.h) {
        where.appendChild(document.createTextNode(" \u203a "));
        const section = document.createElement("strong");
        into(section, record.h, terms);
        where.appendChild(section);
      }
      const line = document.createElement("div");
      line.className = "excerpt";
      into(line, excerpt(record.t || "", terms), terms);
      link.append(where, line);
      list.appendChild(link);
    }
    mark();
  }

  function mark() {
    const hits = [...list.querySelectorAll("a.hit")];
    hits.forEach((hit, i) => hit.classList.toggle("on", i === chosen));
    if (hits[chosen]) hits[chosen].scrollIntoView({block: "nearest"});
  }

  box.addEventListener("input", draw);
  box.addEventListener("keydown", (event) => {
    const hits = [...list.querySelectorAll("a.hit")];
    if (!hits.length) return;
    if (event.key === "ArrowDown") { event.preventDefault(); chosen = (chosen + 1) % hits.length; mark(); }
    else if (event.key === "ArrowUp") { event.preventDefault(); chosen = (chosen + hits.length - 1) % hits.length; mark(); }
    else if (event.key === "Enter") { event.preventDefault(); hits[chosen].click(); }
  });
  dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
})();
</script>"""


#: The two rails, and whether the reader wants them. The chapter list is closed by default on a
#: phone and the button opens it over the page; where there is room it is open by default and the
#: same button closes it. This page's outline is on the right, and exists only where there is room
#: for it, so its button is there and nowhere else. Either choice is remembered — per browser, not
#: per page, and read before the page paints, so a reader who closed a rail does not watch it
#: close again on every chapter. A reader working through a wide graph closes both.
MENU = r"""<script>
try {
  const root = document.documentElement;
  if (localStorage.getItem("nav") === "closed") root.classList.add("nav-closed");
  if (localStorage.getItem("toc") === "closed") root.classList.add("toc-closed");
} catch (e) {}
document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement, nav = document.getElementById("nav"),
        menu = document.getElementById("menu"), wide = matchMedia("(min-width: 58rem)");
  const shown = () =>
    wide.matches ? !root.classList.contains("nav-closed") : nav.classList.contains("open");
  const reflect = () => menu.setAttribute("aria-expanded", String(shown()));
  menu.addEventListener("click", () => {
    if (wide.matches) {
      const closed = root.classList.toggle("nav-closed");
      try {
        if (closed) localStorage.setItem("nav", "closed"); else localStorage.removeItem("nav");
      } catch (e) {}
    } else {
      nav.classList.toggle("open");
    }
    reflect();
  });
  wide.addEventListener("change", reflect);
  reflect();

  const outline = document.getElementById("outline"), roomy = matchMedia("(min-width: 72rem)");
  const reflectOutline = () => {
    // Below the breakpoint the rail is not laid out at all, so neither is the button: a
    // control for something the reader cannot see is worse than no control.
    outline.hidden = !roomy.matches;
    outline.setAttribute("aria-expanded", String(!root.classList.contains("toc-closed")));
  };
  outline.addEventListener("click", () => {
    const closed = root.classList.toggle("toc-closed");
    try {
      if (closed) localStorage.setItem("toc", "closed"); else localStorage.removeItem("toc");
    } catch (e) {}
    reflectOutline();
  });
  roomy.addEventListener("change", reflectOutline);
  reflectOutline();
});
</script>"""

#: The button that takes something the column cannot hold and gives it the window. Every model
#: has one, because a model's graph is drawn at a fixed width and no column holds it. Anything
#: else gets one only when it is actually cut off at the chapter's width -- a wide table, a long
#: line of code, the model file a reader edits -- which the page can only know by measuring. It
#: keeps the same element rather than opening another page, so an edit in progress, a slider
#: already moved and the reader's place in the chapter all survive the trip.
EXPAND = r"""<script>
document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  let scrolled = 0;
  const label = (button, text, open) => {
    button.querySelector("span").textContent = text;
    button.setAttribute("aria-expanded", String(open));
  };
  const close = () => {
    const open = document.querySelector(".expanded");
    if (!open) return;
    const button = open.querySelector(".expand");
    open.classList.remove("expanded");
    root.classList.remove("model-open");
    label(button, "Expand", false);
    // It left the flow while it was open, so the page under it moved. Put the reader back
    // where they were rather than wherever the shorter page ended up.
    window.scrollTo(0, scrolled);
    button.focus();
  };
  const control = () => {
    const button = document.createElement("button");
    button.className = "expand";
    button.type = "button";
    button.setAttribute("aria-expanded", "false");
    button.innerHTML = '<svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">'
      + '<path d="M6 2H2v4M10 14h4v-4M2 10v4h4M14 6V2h-4" fill="none" stroke="currentColor"'
      + ' stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      + "<span>Expand</span>";
    return button;
  };
  const wire = (box, button) => {
    button.addEventListener("click", () => {
      if (box.classList.contains("expanded")) { close(); return; }
      close();
      scrolled = window.scrollY;
      box.classList.add("expanded");
      root.classList.add("model-open");
      label(button, "Close", true);
    });
  };
  // A model: the button is in the page already, drawn beside the frame it belongs to.
  for (const frame of document.querySelectorAll("iframe.viewer, iframe.playground")) {
    const figure = frame.closest("figure");
    const button = figure && figure.querySelector(".expand");
    if (!button) continue;
    button.hidden = false;   // it does nothing without this script, so it is not there without it
    wire(figure, button);
  }
  // Everything else: only where the content is wider than the column it was given. A block
  // with its own bar puts the button in the bar; one without is wrapped so it has somewhere.
  const cut = (el) => el.scrollWidth > el.clientWidth + 1;
  // A table never overflows: `width: max-content` with `max-width: 100%` makes it shrink to
  // the column and wrap every cell instead, so `cut` said no to 65 of the book's 96 tables
  // while a reader saw "USD / TB / month" broken over three lines. Ask each one what it would
  // be if nothing squeezed it.
  const squeezed = (el) => {
    if (el.tagName !== "TABLE") return cut(el);
    const had = el.style.maxWidth;
    el.style.maxWidth = "none";
    const wants = el.scrollWidth;
    el.style.maxWidth = had;
    return wants > el.clientWidth + 1;
  };
  for (const block of document.querySelectorAll("#main .editable-block")) {
    const pre = block.querySelector("pre");
    if (!pre || !cut(pre)) continue;
    const button = control();
    block.querySelector(".editable-bar").appendChild(button);
    wire(block, button);
  }
  for (const el of document.querySelectorAll("#main > pre, #main > table, #main table")) {
    if (!squeezed(el)) continue;
    const box = document.createElement("div");
    box.className = "wide-block";
    el.replaceWith(box);
    box.appendChild(el);
    const button = control();
    box.appendChild(button);
    wire(box, button);
  }
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") close(); });
});
</script>"""


#: The offline control. A Run fetches the Python runtime the first time it is pressed and the
#: worker keeps whatever it fetched; this fetches the same files ahead of need, with a byte count
#: while it does, and says when everything is kept. Every file a Run needs is resolved from the
#: runtime's own lock file when the control is pressed, so a runtime upgrade cannot leave the
#: list stale, and the cache it fills is the one the worker serves a Run from.
OFFLINE = r"""<script>
document.addEventListener("DOMContentLoaded", () => {
  const spec = __SPEC__;
  const button = document.getElementById("offline");
  if (!button || !("caches" in window) || !("serviceWorker" in navigator)) return;
  const label = button.querySelector("span");
  const say = (text, state) => { label.textContent = text; button.dataset.state = state || ""; };
  const mb = (bytes) => Math.round(bytes / 1048576) + " MB";
  const CORE = ["pyodide.mjs", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip",
                "pyodide-lock.json"];
  const lockUrl = spec.pyodide + "pyodide-lock.json";

  // Every file a Run fetches: the runtime's own, the packages resolved from its lock file with
  // what they depend on, and the wheels the toolkit pins.
  function resolve(lock) {
    const wanted = new Set(), queue = [...spec.packages];
    while (queue.length) {
      const name = queue.pop();
      const entry = lock.packages[name];
      if (wanted.has(name) || !entry) continue;
      wanted.add(name);
      queue.push(...(entry.depends || []));
    }
    return [
      ...CORE.map((file) => spec.pyodide + file),
      ...[...wanted].map((name) => spec.pyodide + lock.packages[name].file_name),
      ...spec.wheels,
    ];
  }

  // Whether everything is kept already, answered from the cache alone: opening a page fetches
  // nothing for this control.
  async function kept() {
    const cache = await caches.open(spec.cache);
    const lock = await cache.match(lockUrl);
    if (!lock) return false;
    const found = await Promise.all(resolve(await lock.json()).map((url) => cache.match(url)));
    return found.every(Boolean);
  }

  async function keep() {
    button.disabled = true;
    say("Keeping…", "busy");
    try {
      if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
      const cache = await caches.open(spec.cache);
      const lock = await fetch(lockUrl);
      if (!lock.ok) throw new Error(lockUrl);
      await cache.put(lockUrl, lock.clone());
      let bytes = 0;
      for (const url of resolve(await lock.json())) {
        if (await cache.match(url)) continue;
        const response = await fetch(url);
        if (!response.ok) throw new Error(url);
        await cache.put(url, response.clone());
        bytes += (await response.arrayBuffer()).byteLength;
        say("Keeping… " + mb(bytes), "busy");
      }
      say("Kept offline", "kept");
    } catch (error) {
      say(navigator.onLine ? "Could not keep it; try again" : "No network to keep it from", "failed");
    } finally {
      button.disabled = false;
    }
  }

  async function forget() {
    if (!confirm("Remove the Python runtime this browser keeps for offline use?")) return;
    await caches.delete(spec.cache);
    say("Keep offline", "");
  }

  button.addEventListener("click", () => (button.dataset.state === "kept" ? forget() : keep()));
  button.hidden = false;   // it does nothing without this script, so it is not there without it
  kept().then((yes) => { if (yes) say("Kept offline", "kept"); }).catch(() => {});
});
</script>"""

#: The control's script with what it needs to fetch filled in.
OFFLINE_SCRIPT = OFFLINE.replace("__SPEC__", json.dumps(offline_manifest()))

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Sizing and TCO</title>
<link rel="icon" href="favicon.svg" type="image/svg+xml">
{headlinks}
<style>{css}</style>
{boot}
{menu}
{offline}
</head>
<body>
<a class="skip" href="#main">Skip to the chapter</a>
<header class="top">
  <a class="brand" href="index.html">Sizing and TCO</a>
  <button id="find-open" class="find" type="button" hidden>Search <kbd>/</kbd></button>
  <button id="offline" class="offline" type="button" hidden data-state=""
          title="Fetch the Python runtime now, so the models run with no network"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M8 1.5v8.5m0 0L4.8 6.8M8 10l3.2-3.2M2 11.5v2.5h12v-2.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Keep offline</span></button>
  <button id="outline" type="button" aria-label="On this page" aria-controls="toc" hidden
          title="Show or hide this page’s outline"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><rect x="1.5" y="2.7" width="13" height="10.6" rx="1.3" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M10.7 2.7v10.6" stroke="currentColor" stroke-width="1.4"/></svg></button>
  <button id="menu" type="button" aria-label="Chapters" aria-controls="nav"
          title="Show or hide the chapter list">☰</button>
</header>
<div class="shell">
  <nav id="nav" class="nav" aria-label="Chapters">{nav}</nav>
  <main id="main" tabindex="-1">
{body}
{turn}
  </main>
  <aside id="toc" class="toc" aria-label="On this page">{toc}</aside>
</div>
<dialog id="find" aria-label="Search the book">
  <input id="find-q" type="search" placeholder="Search the book…" autocomplete="off"
         autocorrect="off" spellcheck="false">
  <div id="find-results"></div>
</dialog>
{search}
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
  /* Three greys, each one readable on the page, the panel and a code block. `--faint`
     was a pale #8da2ac, which is 2.4:1 against the paper -- under the 4.5:1 a reader
     needs for text this size, and it carries every table's headings. Darkening it alone
     would have landed it on top of `--muted`, so all three moved and kept their order. */
  --ink: #263238; --muted: #41555e; --faint: #5a707b;
  --edge: #dfe5e8; --rule: #c4d0d6;
  --bg: #fdfdfc; --panel: #f2f6f7; --code: #f0f4f6; --raise: rgba(38,50,56,.06);
  --accent: #35648f; --on-accent: #ffffff; --wash: rgba(53,100,143,.09);
  --warn: #c8791a; --stop: #b3413a; --go: #2e7d32;
  --measure: 36rem;
  /* The two rails. A chapter list that wraps 16 of its 39 entries is hard to scan, and
     the widths below give the room back where there is room to give -- see the rule at
     96rem. Under that, the middle column needs every pixel: at 1512 the wider rails
     would leave an embedded model 853px, under the 861 its own layout needs to put the
     inputs beside the graph, so it would stack. */
  --nav: 17rem; --toc: 14rem;
  --top: 3.1rem;
  --chrome: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --text: Charter, "Bitstream Charter", "Sitka Text", Cambria, Georgia, serif;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, "DejaVu Sans Mono", monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #dde4e8; --muted: #a7b8c1; --faint: #83949d;
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
/* Three controls in the header are written `hidden` and revealed by the script that makes them
   work. Saying so in the markup was not enough: `display` on a class beats the browser's own
   rule for the attribute, so all three showed with scripts off and did nothing when pressed. */
[hidden] { display: none !important; }
:is(#menu, #outline) { font: 16px/1 var(--chrome); background: none; color: var(--muted);
        border: 1px solid var(--edge); border-radius: 5px; cursor: pointer; padding: .4rem .6rem; }
:is(#menu, #outline):hover { border-color: var(--accent); color: var(--accent); }
#outline { display: flex; align-items: center; padding: .45rem .55rem; }

/* Search. The control is hidden in the markup and shown by the script, because without the
   script it does nothing at all. */
.find { margin-left: auto; display: flex; align-items: center; gap: .5rem;
        font: 13.5px/1 var(--chrome); color: var(--muted); background: var(--panel);
        border: 1px solid var(--edge); border-radius: 6px; padding: .45rem .7rem;
        cursor: pointer; }
.find:hover { border-color: var(--accent); color: var(--accent); }
.find kbd { font: 11px/1 var(--mono); border: 1px solid var(--edge); border-radius: 3px;
            padding: .15rem .3rem; background: var(--bg); color: var(--faint); }
/* The provenance marks, drawn rather than typeset: a full, a half and an empty circle of one
   size, whatever fonts the device has. The glyph stays in the span, invisible, for a screen
   reader and for copy-and-paste; on paper it is shown instead, because a printer may drop
   backgrounds. */
.mark { display: inline-block; width: .66em; height: .66em; border-radius: 50%;
        border: 1.5px solid var(--ink); box-sizing: border-box; position: relative;
        vertical-align: -.02em; color: transparent; overflow: hidden; }
.mark::before { content: ""; position: absolute; inset: 0; print-color-adjust: exact; }
.mark[data-mark="fact"]::before { background: var(--ink); }
.mark[data-mark="vendor_claim"]::before { background: linear-gradient(90deg, var(--ink) 50%, transparent 50%); }
@media print {
  .mark { width: auto; height: auto; border: 0; color: var(--ink); overflow: visible; }
  .mark::before { display: none; }
}
/* The offline control. Hidden in the markup and shown by its script, like Search. */
.offline { display: flex; align-items: center; gap: .45rem; font: 13.5px/1 var(--chrome);
           color: var(--muted); background: var(--panel); border: 1px solid var(--edge);
           border-radius: 6px; padding: .45rem .7rem; cursor: pointer; }
.offline:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.offline:disabled { cursor: progress; }
.offline[data-state="kept"] { color: var(--go); border-color: var(--go); }
.offline[data-state="failed"] { color: var(--stop); }
@media (max-width: 40rem) { .offline span { display: none; } .offline { padding: .45rem .5rem; } }
dialog#find { width: min(46rem, calc(100vw - 2rem)); max-height: min(34rem, calc(100vh - 5rem));
              padding: 0; border: 1px solid var(--rule); border-radius: 10px; overflow: hidden;
              background: var(--bg); color: var(--ink); margin-top: 8vh;
              box-shadow: 0 16px 48px rgba(0,0,0,.22); }
dialog#find::backdrop { background: rgba(20,25,28,.44); backdrop-filter: blur(2px); }
#find-q { width: 100%; font: 17px/1.4 var(--chrome); color: var(--ink); background: var(--bg);
          border: 0; border-bottom: 1px solid var(--edge); padding: .9rem 1.1rem; }
#find-q:focus { outline: none; }
#find-results { overflow-y: auto; max-height: calc(min(34rem, 100vh - 5rem) - 3.6rem);
                padding: .4rem; }
.find-note { font: 14px/1.5 var(--chrome); color: var(--faint); margin: .6rem .8rem; }
a.hit { display: block; text-decoration: none; color: inherit; padding: .55rem .75rem;
        border-radius: 6px; }
a.hit.on, a.hit:hover { background: var(--wash); }
a.hit .where { font: 13px/1.4 var(--chrome); color: var(--muted); }
a.hit .where strong { color: var(--ink); font-weight: 600; }
a.hit .excerpt { font: 13.5px/1.5 var(--text); color: var(--muted); margin-top: .15rem;
                 display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
                 overflow: hidden; }
mark { background: var(--wash); color: inherit; border-radius: 2px; padding: 0 .1em;
       font-weight: 600; }

/* Frame */
.shell { display: grid; grid-template-columns: minmax(0, 1fr); max-width: 126rem;
         margin-inline: auto; }
/* Hidden until there is room, and declared before the rules that show them so that those win
   by order rather than by !important. Below the first breakpoint the chapter list opens over
   the page from the ☰ button. */
.nav, .toc { display: none; font: 14px/1.45 var(--chrome); padding: 1.4rem 1rem 3rem; }
.nav.open { display: block; }
/* Two steps, not one. A column of 41rem needs 58rem beside the navigation and 72rem beside both
   sidebars, and a single breakpoint at the larger of those left a 1024px tablet with no
   navigation and a third of its width empty. */
@media (min-width: 58rem) {
  /* The middle column is the widest thing a chapter holds -- a model at 84rem -- and the group
     of columns is what centres. `1fr` instead would make it whatever the window has left, which
     is a column sized by the screen rather than by the book. */
  .shell { grid-template-columns: var(--nav) minmax(0, calc(84rem + 5rem));
           justify-content: center; }
  .nav { display: block; position: sticky; top: var(--top);
         max-height: calc(100vh - var(--top)); overflow-y: auto;
         overscroll-behavior: contain; }
  html.nav-closed .shell { grid-template-columns: minmax(0, calc(84rem + 5rem)); }
  html.nav-closed .nav { display: none; }
}
/* Two rails, and a reader reading a wide graph wants neither. Each has a button of its own, so
   the chapter takes back 272px, 224px, or both -- and with both away the shell's own cap goes
   too, because at that point the reader has asked for the window. */
@media (min-width: 72rem) {
  .shell { grid-template-columns: var(--nav) minmax(0, calc(84rem + 5rem)) var(--toc); }
  html.nav-closed .shell { grid-template-columns: minmax(0, calc(84rem + 5rem)) var(--toc); }
  html.toc-closed .shell { grid-template-columns: var(--nav) minmax(0, calc(84rem + 5rem)); }
  html.nav-closed.toc-closed .shell {
    grid-template-columns: minmax(0, calc(84rem + 5rem)); max-width: none; }
  .toc { display: block; position: sticky; top: var(--top);
         max-height: calc(100vh - var(--top)); overflow-y: auto;
         overscroll-behavior: contain; }
  html.toc-closed .toc { display: none; }
}
/* Wide enough that widening the rails takes nothing from the chapter: the middle column
   still clears the 861px an embedded model needs for its two-column layout, and above
   2016px it reaches the 84rem cap regardless. Every grid rule above reads these. */
@media (min-width: 96rem) {
  :root { --nav: 21rem; --toc: 15rem; }
}
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
/* Centred, because the slack has to go somewhere and all of it on the right reads as a mistake.
   Below the first breakpoint this cap is the whole of the layout; above it, the rule below
   hands the cap to each child instead, so a figure can be wider than a paragraph. */
main { padding: 1rem clamp(1rem, 4vw, 2.6rem) 6rem; max-width: calc(var(--measure) + 5rem);
       min-width: 0; width: 100%; margin-inline: auto; }
/* Above the first breakpoint the measure belongs to each thing in the chapter rather than to
   the column holding them, so the line length is the same at every width -- prose, headings
   and notes keep it and stay centred -- while what a reader came for spreads into whatever
   room there is. This used to apply only with the chapter list closed, which left a model
   573px wide on a 1512px laptop, under the 860px its own layout needs to put the inputs
   beside the graph, with 452px of the window empty.

   Addressed by the id rather than the element, because almost every child of the chapter sets
   its own horizontal margins -- `p`, every heading, `.admonition`, `.editable-block`, the
   turn -- and at equal specificity the later rule wins, which stacked the whole page against
   the left of its column. The rules also sit here, after the cap they undo, because a media
   query adds no specificity of its own.

   Three widths, each what its content needs, all centred on the same middle. Prose keeps the
   measure: 576px is about seventy characters, and a longer line is harder to read however much
   room the window has. Code takes up to 60rem, because the book's own lines stop at 100 columns
   and its widest block wants 942px -- at the measure, 121 blocks over 33 pages were cut off
   mid-word and the bar above them wrapped onto two lines. A model, the runner and a table take
   up to 84rem, which is 2.3 times the prose: wide enough that a model shows its inputs beside
   its graph, near enough that the page still reads as one column. Nothing goes wider in the
   flow; what still does not fit says so and takes the window on a button. */
@media (min-width: 58rem) {
  #main { max-width: none; }
  #main > * { max-width: var(--measure); margin-inline: auto; }
  #main > :is(figure:has(> iframe), figure:has(> .runner), table) { max-width: min(100%, 84rem); }
  #main > :is(pre, .editable-block, .problem, figure:has(> pre)) { max-width: min(100%, 60rem); }
  #main > figure > figcaption { margin-inline: auto; }
}
main :is(h1, h2, h3, h4) { font-family: var(--chrome); letter-spacing: -.012em;
                           scroll-margin-top: calc(var(--top) + 1rem); }
h1 { font-size: clamp(1.6rem, 5.4vw, 2rem); font-weight: 700; line-height: 1.18;
     margin: 1.6rem 0 1.4rem; }
.builds-on { margin: -.9rem 0 1.4rem; font: 14px/1.5 var(--chrome); color: var(--muted); }
a.term { color: inherit; text-decoration: underline dotted var(--muted); text-underline-offset: .18em; }
a.term:hover { color: var(--accent); text-decoration-color: var(--accent); }
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
/* A model is the one thing a chapter's column can never hold: its graph is drawn at a fixed
   width -- 1470px for the widest in the book -- so a narrower card shows less of the graph
   rather than a smaller one. It sits at the chapter's width like everything else, and the
   button over its corner gives it the window and gives it back, in the frame it already has:
   the model is not reloaded, so the sliders the reader has moved stay where they were put,
   and closing it returns them to the paragraph they were reading. The script puts the same
   button on a table or a block of code, but only where one is actually cut off. */
:is(figure.container:has(> iframe), .wide-block) { position: relative; }
.expand { position: absolute; top: .5rem; right: .5rem; z-index: 2; display: flex;
          align-items: center; gap: .35rem; font: 12.5px/1 var(--chrome); color: var(--muted);
          background: var(--bg); border: 1px solid var(--edge); border-radius: 5px;
          padding: .35rem .55rem; cursor: pointer; }
.expand:hover { border-color: var(--accent); color: var(--accent); }
/* A block the script wrapped because its content is wider than the column. The wrapper holds
   the button; the block inside it is untouched, so an editable one is still the same node the
   reader has been typing into. */
.wide-block { margin: 1.4rem 0; }
.wide-block > :is(pre, table) { margin: 0; }
.editable-bar .expand { position: static; }
html.model-open { overflow: hidden; }
html.model-open #main .expanded { position: fixed; inset: 0; z-index: 40; margin: 0;
          max-width: none; border-radius: 0; background: var(--bg); display: flex;
          flex-direction: column; padding: 0; }
html.model-open #main .expanded > :is(iframe, pre, table) { flex: 1 1 auto; height: auto;
          max-height: none; max-width: none; width: auto; border: 0; border-radius: 0;
          overflow: auto; }
html.model-open #main .expanded > table { width: max-content; }
html.model-open #main .expanded > figcaption { display: none; }
html.model-open #main .expanded.editable-block { border-radius: 0; }
iframe { width: 100%; border: 1px solid var(--rule); border-radius: 6px; height: 680px; }
iframe.viewer { height: 780px; }
/* A model lays itself out from its own width: stacked, then the inputs beside the graph at
   860px, then the detail panel too at 1100px. Each of those is a different height, and one
   fixed box fits none of them. The figure is the model's container, so the box follows.
   Measured at 578px and 791px of content; a browser without container queries keeps 780px,
   which is what every browser had before. */
figure:has(> iframe.viewer) { container-type: inline-size; }
@container (min-width: 860px) { iframe.viewer { height: 600px; } }
@container (min-width: 1101px) { iframe.viewer { height: 812px; } }
@media (max-width: 720px) { iframe { height: 80vh; min-height: 540px; } }

/* A quoted piece of the model the reader may edit where the chapter shows it. Nothing but the
   bar above it says so, so the bar has to carry its weight: what file this is, that it is
   theirs, and the button that acts on it. */
.editable-block { margin: 1.4rem 0; border: 1px solid var(--rule); border-radius: 6px;
                  background: var(--bg); overflow: hidden; }
.editable-block:focus-within { border-color: var(--accent);
                               box-shadow: 0 0 0 3px var(--wash); }
.editable-bar { display: flex; flex-wrap: wrap; align-items: center; gap: .1rem .6rem;
                padding: .3rem .4rem .3rem .9rem; background: var(--panel);
                border-bottom: 1px solid var(--edge); font: 12.5px/1.6 var(--chrome); }
.editable-bar .file { font-family: var(--mono); font-size: 11.5px; color: var(--muted); }
.editable-bar .hint { color: var(--faint); white-space: nowrap; }
.editable-block.changed .editable-bar { background: var(--wash); }
.editable-block.changed .editable-bar .hint { color: var(--accent); font-weight: 600; }
pre.editable { margin: 0; border: 0; border-radius: 0; background: var(--bg);
               caret-color: var(--accent); white-space: pre; overflow-x: auto; }
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

/* A problem's stub, editable under the problem it grades, and the verdict under that: one
   line per test, pytest's own message beside the ones that fail, and everything it said for a
   reader who wants all of it. The command the chapter wrote is a one-line note at the end, in
   the bar's small type, for a desk. */
.problem { margin: 1.4rem 0 1.4rem; }
.problem .editable-block { margin: 0 0 .6rem; }
.problem .desk { margin: 0; font: 12.5px/1.5 var(--chrome); color: var(--faint); }
.problem .desk code { font-size: 11.5px; color: var(--muted); background: none; padding: 0;
                      overflow-wrap: anywhere; }
.check-here { margin-left: auto; padding: .25rem .7rem; font-size: 12.5px; }
.verdicts { font: 13.5px/1.4 var(--chrome); color: var(--muted); margin-bottom: .8rem; }
.verdicts:empty { display: none; }
.verdicts .verdict { margin: .2rem 0 .5rem; }
.tests { list-style: none; margin: 0; padding: 0; border: 1px solid var(--edge);
         border-radius: 6px; background: var(--bg); }
.tests li { position: relative; padding: .45rem .8rem .45rem 1.9rem;
            border-top: 1px solid var(--edge); }
.tests li:first-child { border-top: 0; }
.tests li::before { content: ""; position: absolute; left: .75rem; top: .85rem; width: .55rem;
                    height: .55rem; border-radius: 50%; background: var(--faint); }
.tests li.passed::before { background: var(--go); }
.tests li.failed::before, .tests li.error::before { background: var(--stop); }
.tests .name { font-family: var(--mono); font-size: 12.5px; color: var(--ink); }
.verdicts pre { margin: .35rem 0 0; padding: .45rem .7rem; border: 0; border-radius: 4px;
                background: var(--panel); font-size: 12px; line-height: 1.5;
                white-space: pre-wrap; overflow-wrap: anywhere; }
.verdicts pre.trace { color: var(--stop); }
.verdicts details { margin-top: .6rem; }
.verdicts summary { cursor: pointer; color: var(--faint); font-size: 12.5px; }

/* Carrying on reading. Two targets at the foot of every page, because the contents list is a
   place to look something up and this is the one a reader going front to back actually uses. */
.turn { display: flex; gap: .9rem; margin: 3.5rem 0 0; padding-top: 1.4rem;
        border-top: 1px solid var(--edge); }
.turn a { flex: 1 1 0; min-width: 0; display: block; text-decoration: none; color: var(--ink);
          font-family: var(--chrome); border: 1px solid var(--edge); border-radius: 8px;
          padding: .7rem .9rem; }
.turn a:hover { border-color: var(--accent); background: var(--panel); }
.turn .next { margin-left: auto; text-align: right; }
.turn .way { display: block; font-size: 11.5px; font-weight: 600; letter-spacing: .08em;
             text-transform: uppercase; color: var(--faint); margin-bottom: .15rem; }
.turn .what { font-size: 15px; font-weight: 600; line-height: 1.3; }
@media (max-width: 560px) {
  .turn { flex-direction: column; }
  .turn .next { text-align: left; margin-left: 0; }
}

/* On paper the furniture is noise and the controls do nothing. */
@media print {
  .top, .nav, .toc, .runner, .editable-bar, .verdicts, .turn, .find, .offline { display: none; }
  .shell { display: block; }
  main { max-width: none; padding: 0; }
  .editable-block { border: 1px solid #ccc; }
  a { color: inherit; }
}
"""


def dark_figures() -> str:
    """One rule per colour a figure is drawn in, so an inline SVG follows the page into the dark.

    The figures are drawn once, in daylight, by ``bench/diagrams.py``, and every one of them is
    written into the page rather than linked, so the stylesheet can reach each fill and stroke.
    Colour by colour rather than a filter: a ceiling is red because red means a ceiling, and
    inverting the page would make it cyan and say nothing.
    """
    from bench.diagrams import DARK_FIGURE

    rules = "\n".join(
        f'  #main svg [fill="{light}"] {{ fill: {dark}; }}\n'
        f'  #main svg [stroke="{light}"] {{ stroke: {dark}; }}'
        for light, dark in DARK_FIGURE.items()
    )
    return f"@media (prefers-color-scheme: dark) {{\n  figure img {{ background: var(--panel); }}\n{rules}\n}}\n"


CSS += dark_figures()


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


def render_page(source: str, page: dict, before: Neighbour, after: Neighbour) -> str:
    # Editable excerpts have to be marked before the body is rendered, because the renderer
    # decides from the mark whether a quoted block is a picture of the file or the file itself.
    stage = stage_for(source)
    blocks = editable_excerpts(page, stage) if stage else []
    if blocks:
        # The chapter's playground `{iframe}` is the same toolkit in a box, so with the model
        # editable in place it comes out: two Run buttons is worse than one. The run control
        # takes its slot rather than the end of the page, because the prose around the panel
        # already introduces it — press this, change a number, watch the total move. Failing a
        # panel, the control goes after the last piece of the file, which is where the reader
        # has all of it.
        #
        # Only the playground's panel, though. A chapter also embeds its stage's viewer — the
        # graph with a slider on every input — and that is not the toolkit in a box, it is the
        # other half of the lesson. Suppressing every iframe took the viewer out of ch02 and ch03
        # silently, which is how the first version of this shipped.
        panels = [
            n
            for n in walk(page.get("mdast", page))
            if n.get("type") == "iframe" and str(n.get("src", "")).startswith("/playground/")
        ]
        for node in panels:
            node["_suppressed"] = True
        (panels[0] if panels else blocks[-1])["_runner_here"] = True
    problems = problem_excerpts(source, page)
    toc = toc_html(page)  # taken before the promotion below, which renumbers what it reads
    if source in TITLED_PAGES:
        promote_headings(page)
    link_terms(source, page)
    body = renderer.render(page.get("mdast", page))
    if source == GLOSSARY_PAGE:
        body = anchor_glossary_rows(body)
    if builds_on(source):
        body = body.replace("</h1>", "</h1>" + builds_on(source), 1)
    if source not in TITLED_PAGES:
        # The introduction and the part pages carry their name in the front matter and nowhere
        # in the text, so the page opens on a blockquote with nothing above it saying where
        # the reader is.
        body = f"<h1>{html.escape(title_for(source, page))}</h1>" + body
    if blocks:
        runner = RUNNER.format(
            whole=json.dumps(stage.path.read_text()),
            modules=json.dumps(sources()),
            results=json.dumps(results_for(load_model(stage.path))),
            wheels=json.dumps(wheels()),
            pyodide=PYODIDE,
        )
        body = body.replace(renderer.RUNNER_SLOT, runner, 1)
    if problems:
        spec = {
            "pyodide": PYODIDE,
            "wheels": wheels(),
            "runner": problem_wheels(),
            "set": f"problems/{Path(href_for(source)).stem}.json",
            "whole": (ROOT / "tests" / Path(source).stem / "stubs.py").read_text(),
        }
        body += PROBLEMS.replace("__SPEC__", json.dumps(spec))
    headlinks, turn = turning(before, after)
    return PAGE.format(
        title=html.escape(title_for(source, page)),
        css=CSS,
        nav=nav_html(href_for(source)),
        toc=toc,
        body=body,
        search=SEARCH,
        menu=MENU + EXPAND,
        offline=OFFLINE_SCRIPT,
        boot=BOOT_SCRIPT if blocks or problems else "",
        headlinks=headlinks,
        turn=turn,
    )


#: Where a page sits in the reading order, as (href, title). None at either end of the book.
Neighbour = tuple[str, str] | None


def turning(before: Neighbour, after: Neighbour) -> tuple[str, str]:
    """The foot of a page: the two links that carry on reading.

    The order is `page_order()`, which is `myst.yml`'s table of contents and the order this build
    writes the pages in, so the book cannot disagree with itself about what comes next. `rel`
    in the head as well as links in the page: a browser and a crawler both read the first, and
    only a person reads the second.
    """
    head, foot = [], []
    for way, where, label in (("prev", before, "Previous"), ("next", after, "Next")):
        if not where:
            continue
        href, title = where
        head.append(f'<link rel="{way}" href="{html.escape(href)}">')
        foot.append(
            f'<a class="{way}" href="{html.escape(href)}">'
            f'<span class="way">{label}</span>'
            f'<span class="what">{html.escape(title)}</span></a>'
        )
    return "\n".join(head), (f'<nav class="turn">{"".join(foot)}</nav>' if foot else "")


def _site() -> str:
    """Where the published book lives, derived rather than typed.

    The host comes from ``myst.yml``'s ``github``, so it cannot disagree with the repository and
    would follow it if the repository moved. Only the sitemap needs it: every link in a page is
    relative, or root-relative and given the base path by ``build-icons.py``.
    """
    config = yaml.safe_load((ROOT / "myst.yml").read_text())
    owner, repo = config["project"]["github"].rstrip("/").split("/")[-2:]
    return f"https://{owner}.github.io/{repo}"


def crawlables(out: Path, pages: list[str]) -> None:
    """A sitemap and a robots.txt, which the theme used to publish and a reader never sees.

    They are the difference between a book a search engine can find and one it cannot, and the
    site URL is derived from the repository rather than typed.
    """
    site = _site()
    urls = "".join(f"  <url><loc>{site}/{href}</loc></url>\n" for href in pages)
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n"
    )
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site}/sitemap.xml\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--only", help="one page, by chapter label or slug")
    args = parser.parse_args()

    index = renderer.parsed_pages()
    if not index:
        raise SystemExit("no parsed content — run `myst build` first")

    wanted = renderer.page_order()
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
    renderer.PAGES = {Path(href_for(s)).stem: href_for(s) for s in wanted}

    args.out.mkdir(parents=True, exist_ok=True)
    favicon = ROOT / "public" / "favicon.svg"
    if favicon.exists():
        (args.out / "favicon.svg").write_text(favicon.read_text())
    # The index is taken from every page before any page is rendered: rendering promotes the
    # headings, and the index reads the depths MyST wrote.
    records: list[dict] = []
    for source in wanted:
        if source in index:
            page = index[source]
            records += sections_of(source, page, title_for(source, page), href_for(source))
    catalogue = args.out / "search.json"
    catalogue.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")))
    print(
        f"  wrote {shown(catalogue)} ({catalogue.stat().st_size:,} bytes, {len(records)} sections)"
    )

    # The reading order, so each page knows what comes before and after it. Built from the
    # pages that are actually being written, so `--only` cannot produce a link to nothing.
    order = [s for s in wanted if s in index]
    reading: list[Neighbour] = [(href_for(s), title_for(s, index[s])) for s in order]

    written = []
    for at, source in enumerate(order):
        target = args.out / href_for(source)
        target.write_text(
            render_page(
                source,
                index[source],
                reading[at - 1] if at else None,
                reading[at + 1] if at + 1 < len(reading) else None,
            )
        )
        written.append(href_for(source))
        print(f"  wrote {shown(target)} ({len(target.read_text()):,} bytes)")
        if Path(source).stem in problem_chapters():
            # The chapter's problem set, beside the pages and named like its page.
            problems = args.out / "problems" / f"{Path(href_for(source)).stem}.json"
            problems.parent.mkdir(exist_ok=True)
            problems.write_text(problem_set(Path(source).stem))
            print(f"  wrote {shown(problems)} ({problems.stat().st_size:,} bytes)")

    crawlables(args.out, written)
    print(f"  wrote {shown(args.out / 'sitemap.xml')} and robots.txt")
    return 0


if __name__ == "__main__":  # pragma: no cover - a thin wrapper around main()
    raise SystemExit(main())
