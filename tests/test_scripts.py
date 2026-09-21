"""The scripts, exercised the way CI and a workflow actually invoke them.

One of these exists because the same defect was fixed in three separate files before anybody
wrote it down, and the third time it took the Pages deploy out: a script handed a *relative*
``--out`` on the command line tried to print the resulting path relative to the repository root,
and ``Path.relative_to`` raises when one path is relative and the other is absolute.

Printing a path is never important enough to fail a build. These check that it cannot.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from bench import render as renderer
from bench.stamp import ROOT, shown

#: Scripts that take an output directory and are given a relative one by a workflow. Each one
#: can do its job in a checkout that has not been built yet, which is the state CI is in when it
#: runs the tests, because the book build comes after them.
TAKES_AN_OUT = [
    ("scripts/build-viewers.py", "--out"),
    ("scripts/build-icons.py", "--out"),
    ("scripts/build-playground.py", "--out"),
]


@pytest.mark.parametrize(
    "path",
    [
        "bench/results",
        "_build/html/models/x.html",
        "./chapters/monte_carlo.md",
        "/tmp/somewhere/else",
        "../outside-the-repo",
        "",
    ],
)
def test_shown_never_raises(path):
    """Whatever the shape, a path can be printed."""
    assert isinstance(shown(path), str)


def test_shown_strips_the_root_when_it_can():
    assert shown(ROOT / "bench" / "results") == "bench/results"
    assert shown("bench/results") == "bench/results"


def test_shown_leaves_a_path_outside_the_repository_alone():
    assert shown("/tmp/elsewhere").startswith("/tmp")


@pytest.mark.parametrize(("script", "flag"), TAKES_AN_OUT, ids=lambda v: Path(str(v)).name)
def test_a_relative_out_does_not_blow_up(script, flag):
    """Exactly what deploy.yml does: a repository-relative output directory.

    Run from the repository root with a relative path, because that is the invocation that
    failed. A script that only works with absolute paths works until somebody writes a workflow.
    """
    relative = f"_build/test-out/{Path(script).stem}"
    completed = subprocess.run(
        [sys.executable, script, flag, relative], cwd=ROOT, capture_output=True, text=True
    )
    assert "relative_to" not in completed.stderr, (
        f"{script} cannot print a path it was given:\n{completed.stderr[-600:]}"
    )
    assert "Traceback" not in completed.stderr, (
        f"{script} raised where it should have reported:\n{completed.stderr[-600:]}"
    )
    assert completed.returncode == 0, completed.stderr[-600:]


def test_verify_setup_reports_rather_than_failing_on_a_missing_optional():
    """It is a report. A machine without myst is not a broken checkout."""
    completed = subprocess.run(
        [sys.executable, "scripts/verify-setup.py"], cwd=ROOT, capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "targets" in completed.stdout


def test_every_script_is_executable_and_parses():
    """A script with a syntax error or no shebang is one CI finds at the worst moment."""
    for script in sorted((ROOT / "scripts").glob("*.py")):
        source = script.read_text()
        assert source.startswith("#!/usr/bin/env python3"), f"{script.name} has no shebang"
        compile(source, str(script), "exec")


#: The constants in scripts/build-site.py that hold JavaScript rather than Python.
JS_TEMPLATES = ("MENU", "OFFLINE", "PROBLEMS", "RUNNER", "SEARCH")


@pytest.mark.parametrize("name", JS_TEMPLATES)
def test_a_javascript_template_is_a_raw_string(name):
    """Python must not eat the escapes in a script it is only carrying.

    This has bitten twice. A ``\\n`` inside a JavaScript regex became a real newline, and a
    regex literal cannot span lines, so the page shipped JavaScript that would not parse --
    silently, because nothing on the Python side was wrong. The fix both times was a raw
    string, and this is what stops the third time.
    """
    source = (ROOT / "scripts" / "build-site.py").read_text()
    raw = f"{name} = r" + '"""'
    assert raw in source, (
        f"{name} in scripts/build-site.py carries JavaScript, so it must be a raw string, "
        f"or Python will interpret its backslashes as its own."
    )


@pytest.mark.parametrize(
    ("written", "anchor", "expected"),
    [
        # The short form, which is most of the book.
        ("ch01", "point-estimates", "ch01"),
        # The long form. The separator and the title belong to the author; only the label moves.
        (
            "ch01 · Point estimates",
            "point-estimates",
            "ch01 · Point estimates",
        ),
        # A label left behind by a chapter that moved, in both forms.
        ("ch99", "point-estimates", "ch01"),
        (
            "ch99 · Point estimates",
            "point-estimates",
            "ch01 · Point estimates",
        ),
        (
            "Appendix A · The DSL, in full",
            "appendix-a-dsl-reference",
            "Appendix A · The DSL, in full",
        ),
        # Text that is not a label at all is the author's, and is left alone.
        ("the introduction", "point-estimates", None),
    ],
)
def test_a_reference_keeps_everything_but_its_label(written, anchor, expected):
    """Deriving the number must not eat the separator, which it did.

    The first version of this matched the label *and* the middle dot, so the text after the
    match began at the title: every long-form reference in the book rendered as
    ``ch01Point estimates``. It survived because the check was a renumbering round-trip
    over the *source*, which a different code path fixes, and because the pages looked at
    afterwards were chapters, whose own heading does not go through here. A part page would have
    shown it immediately.
    """
    assert renderer._relabel({"identifier": anchor}, written) == expected


def site():
    """``scripts/build-site.py``, imported, with the renderer it carries."""
    from importlib import util

    spec = util.spec_from_file_location("build_site", ROOT / "scripts" / "build-site.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("/monte-carlo", "monte-carlo.html"),
        ("/monte-carlo#a-section", "monte-carlo.html#a-section"),
        ("/", "index.html"),
        # A playground directory is named after the chapter it was built from, so taking the last
        # segment of a path resolved every one of them to the wrong page. One segment only.
        ("/playground/monte-carlo/", None),
        ("/models/observability-reference.html", None),
        ("https://example.com/monte-carlo", None),
        ("relative.html", None),
    ],
)
def test_only_a_top_level_path_resolves_to_a_page(url, expected):
    build = site()
    build.renderer.PAGES = {
        Path(build.href_for(s)).stem: build.href_for(s) for s in build.renderer.page_order()
    }
    assert build.renderer._published(url) == expected


def test_a_chapter_says_what_it_builds_on_from_the_outline():
    """The line under a chapter's title is derived from the outline, and links what it names."""
    build_site = site()
    line = build_site.builds_on("chapters/queueing_and_the_knee.md")
    assert line.startswith('<p class="builds-on">Builds on ')
    assert 'href="littles-law.html"' in line and ">ch05</a>" in line
    assert build_site.builds_on("chapters/point_estimates.md") == ""
    assert build_site.builds_on("index.md") == ""


def _page_with(*paragraphs: str) -> dict:
    return {
        "type": "root",
        "children": [
            {"type": "paragraph", "children": [{"type": "text", "value": text}]}
            for text in paragraphs
        ]
        + [
            {"type": "heading", "depth": 2, "children": [{"type": "text", "value": "An interval"}]},
            {"type": "paragraph", "children": [{"type": "inlineCode", "value": "interval"}]},
        ],
    }


def test_a_glossary_term_links_to_its_entry_only_after_its_chapter():
    """One link per term per page, on pages after the chapter that introduces it, never in code
    or a heading. The interval arrives in ch13, so ch12 gets no link and ch19 gets one."""
    from bench.tables import GLOSSARY

    build_site = site()
    page = _page_with("The interval, and the interval again.", "Two intervals here.")
    build_site.link_terms("chapters/which_input_is_the_answer.md", page)
    links = [n for n in build_site.walk(page) if n.get("type") == "link"]
    assert len(links) == 1
    assert links[0]["url"] == "/appendix-g-glossary#term-interval"
    assert links[0]["_term"] == GLOSSARY["interval"][1]
    assert links[0]["children"][0]["value"] == "interval"

    before = _page_with("The interval, and the interval again.")
    build_site.link_terms("chapters/the_sizing_model.md", before)
    assert not [n for n in build_site.walk(before) if n.get("type") == "link"]

    glossary = _page_with("The interval is a term here.")
    build_site.link_terms(build_site.GLOSSARY_PAGE, glossary)
    assert not [n for n in build_site.walk(glossary) if n.get("type") == "link"]


def test_a_provenance_mark_is_drawn_not_typeset():
    """Each of the three marks renders as a span the stylesheet draws, with the glyph kept."""
    from bench import render as renderer

    out = renderer.render({"type": "text", "value": "\u25cf fact, \u25d0 claim, \u25cb guess"})
    assert '<span class="mark" data-mark="fact">\u25cf</span> fact' in out
    assert '<span class="mark" data-mark="vendor_claim">\u25d0</span> claim' in out
    assert '<span class="mark" data-mark="assumption">\u25cb</span> guess' in out
    assert renderer.render({"type": "inlineCode", "value": "\u25cf"}) == "<code>\u25cf</code>"


def test_a_term_link_carries_its_meaning_and_the_glossary_rows_carry_ids():
    build_site = site()
    node = {
        "type": "link",
        "url": "/appendix-g-glossary#term-interval",
        "_term": "the gap between two percentiles",
        "children": [{"type": "text", "value": "interval"}],
    }
    rendered = build_site.renderer.render(node)
    assert 'class="term"' in rendered and 'title="the gap between two percentiles"' in rendered
    row = build_site.anchor_glossary_rows("<tr><td><strong>measured constant</strong></td></tr>")
    assert row.startswith('<tr id="term-measured-constant">')


def test_the_foot_of_a_page_points_at_its_neighbours_in_the_reading_order():
    """prev and next come from page_order(), and the ends of the book have one link, not two."""
    build = site()
    order = [s for s in build.renderer.page_order() if s in build.renderer.parsed_pages()]
    hrefs = [build.href_for(s) for s in order]
    for at, href in enumerate(hrefs):
        before = (hrefs[at - 1], "before") if at else None
        after = (hrefs[at + 1], "after") if at + 1 < len(hrefs) else None
        _, foot = build.turning(before, after)
        if at:
            assert f'class="prev" href="{hrefs[at - 1]}"' in foot, href
        else:
            assert 'class="prev"' not in foot, f"{href} is the first page and offers a previous"
        if at + 1 < len(hrefs):
            assert f'class="next" href="{hrefs[at + 1]}"' in foot, href
        else:
            assert 'class="next"' not in foot, f"{href} is the last page and offers a next"


def playground():
    """``scripts/build-playground.py``, imported so the tests can ask what it builds."""
    from importlib import util

    spec = util.spec_from_file_location(
        "build_playground", ROOT / "scripts" / "build-playground.py"
    )
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_playground_the_build_ships_is_reachable_from_its_chapter():
    """A page nobody links is a page nobody reads, and nobody proofreads either.

    The build shipped five of these and two were embedded. The three orphans deployed on every
    push, cost a Pyodide fetch to anybody who found them, and one of them printed a sentence that
    contradicted itself -- it told a reader the model had neither a measured constant nor a
    ceiling while classifying it as a sizing model, which is only possible because it has one.
    That survived because the only pages anybody looked at were the two that are linked.
    """
    embedded = {
        directory
        for path in (ROOT / "chapters").glob("*.md")
        for directory in re.findall(r"\{iframe\}\s+/playground/([a-z0-9-]+)/", path.read_text())
    }
    built = set(playground().pages())
    assert built == embedded, (
        f"the build ships {sorted(built)} and the chapters embed {sorted(embedded)}. A playground "
        "is built for a chapter, so the chapter embeds it -- or it should not be built."
    )


def viewers():
    """``scripts/build-viewers.py``, imported so the tests can ask what it builds."""
    from importlib import util

    spec = util.spec_from_file_location("build_viewers", ROOT / "scripts" / "build-viewers.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_table_links_a_viewer_exactly_when_one_is_built():
    """Two selections on the same predicate, in two files, that must not drift apart.

    ``bench.tables`` sends a reader to ``/models/<name>.html`` for a result of kind ``model``,
    and ``build-viewers.py`` builds a page for a result of kind ``model``. Written separately,
    so a change to either one could leave every table in a chapter pointing at a page nobody
    builds -- and an external-looking link is not something the built-link check can follow.
    """
    from bench.stamp import RESULTS_DIR
    from bench.tables import _where

    built = set(viewers().model_results())
    sent = {path.stem for path in RESULTS_DIR.glob("*.json") if _where(path.stem).startswith("/")}
    assert built == sent, (
        f"viewers are built for {sorted(built)} and tables link {sorted(sent)}. A table points a "
        "reader at a viewer exactly when there is one to point at."
    )


def test_every_stage_viewer_is_embedded_by_its_chapter():
    """The reader watches the graph grow, so every stage's viewer has to be on its chapter's page.

    Each stage of the running model has an interactive page built from its stamped result, and
    the chapter that introduces the stage embeds it: seven nodes in ch02, ten in ch03, fifty by
    the time the model is finished. A stage whose viewer nobody embeds is a stage the reader
    never sees drawn, and a chapter embedding a stage that is not its own is showing the reader
    nodes the book has not built yet.
    """
    from bench.stages import stages

    for stage in stages():
        name = stage.model if stage.is_the_finished_model else stage.name
        chapter = (ROOT / "chapters" / f"{stage.chapter}.md").read_text()
        wanted = f"{{iframe}} /models/{name}-reference.html"
        assert wanted in chapter, (
            f"chapters/{stage.chapter}.md does not embed its stage's viewer. Add a "
            f"```{wanted}``` panel where the chapter shows what the stage adds."
        )


def test_every_tested_problem_is_checkable_on_its_chapter_page():
    """Under each tested problem, the page shows the piece of the stubs file the test grades,
    editable, with a Check; the pieces splice back into the whole file unchanged; and the
    chapter's problem set is written beside the page for the first Check to fetch."""
    from sizing.playground.toolkit import problem_chapters, problem_pieces

    build_site = site()
    index = renderer.parsed_pages()
    if not index:
        pytest.skip("no parsed content; run `myst build` first")
    for slug in problem_chapters():
        source = f"chapters/{slug}.md"
        page = index[source]
        html = build_site.render_page(source, page, None, None)
        blocks = problem_pieces(slug)
        assert html.count('<div class="problem" data-test="') == len(blocks), (
            f"{source}: not every test file has a Check under its problem"
        )
        for block in blocks:
            assert f'data-test="{block["test"]}"' in html, f"{source} lacks {block['test']}"
            for piece in block["pieces"]:
                assert f'data-start="{piece["start"]}" data-end="{piece["end"]}"' in html
            for entry in block["files"]:
                # A file the reader edits whole is shown whole, at the path the grader writes.
                assert (
                    f'<pre class="editable stub-file" contenteditable="plaintext-only" spellcheck="false" data-path="{entry["path"]}">'
                    in html
                ), f"{source}: no editable block for {entry['path']}"
            # The command the chapter wrote is a note inside the block, not a block of its own:
            # drawn as one, it read as the next step after Check.
            note = (
                '<p class="desk">The same check at a desk: '
                f"<code>python3 -m pytest {block['test']} -m problem"
            )
            assert f"{note}</code></p></div>" in html, f"{source}: no desk note for {block['test']}"
        assert "<pre><code>python3 -m pytest" not in html, f"{source} draws a command as a block"
        assert 'id="problem-spec"' in html and "async function bootToolkit" in html
        # Every heading carries an id made from its text, so "## Problems" owns `problems`; a
        # script tag with that id is the heading's text parsed as JSON, and it shipped once.
        assert html.count('id="problems"') == 1, "the spec's id collides with the heading's"
        assert f'"set": "problems/{build_site.href_for(source).removesuffix(".html")}.json"' in html
        # The whole stubs file the page splices into, and the set it fetches, are the repository's.
        assert (ROOT / "tests" / slug / "stubs.py").read_text() in json.loads(
            re.search(
                r'<script type="application/json" id="problem-spec">(.*?)</script>', html
            ).group(1)
        )["whole"]
        payload = json.loads(build_site.problem_set(slug))
        assert set(payload) == {"modules", "files"}
        assert f"tests/{slug}/stubs.py" in payload["files"]


def test_the_pages_that_run_the_toolkit_share_one_runtime_and_one_boot():
    """Three pages start Python in a browser. One copy of how, or they drift.

    The inline runner, the playground and the viewer each carried their own runtime URL, module
    list and boot sequence until the third one was about to be written. Now
    ``sizing/playground/toolkit.py`` holds the URL and the list, ``boot.js`` the sequence, and
    every builder inlines them. A builder that spells the CDN out again is a fourth copy.
    """
    builders = ("scripts/build-site.py", "scripts/build-playground.py", "scripts/build-viewers.py")
    for builder in builders:
        text = (ROOT / builder).read_text()
        assert "cdn.jsdelivr.net/pyodide" not in text, f"{builder} pins its own runtime URL"
        assert "{boot}" in text, f"{builder} does not inline boot.js"
        assert "from sizing.playground.toolkit import" in text, f"{builder} does not import toolkit"
    # The call itself: in the two page templates, and in the viewer's own app. A chapter page
    # goes through the shared start, because its Run and its Checks are one runtime.
    for caller in ("scripts/build-site.py", "scripts/build-playground.py", "sizing/viewer/app.js"):
        assert re.search(r"\b(bootToolkit|shareToolkit)\(", (ROOT / caller).read_text()), (
            f"{caller} does not call bootToolkit"
        )


def test_the_toolkit_does_not_import_the_harness():
    """``sizing`` runs in a browser that has no ``bench``; nothing under it may import bench.

    A lazy ``from bench.stamp import load_result`` inside ``sizing.dsl`` meant any model with a
    measured constant could not load in the playground -- every stage from ch09 on -- and the
    page said so only to a reader who pressed Run, which for three of them nobody had.
    """
    offenders = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "sizing").rglob("*.py")
        if re.search(r"^\s*(from|import) bench\b", path.read_text(), re.M)
    ]
    assert not offenders, f"the toolkit imports the harness in {offenders}"


def test_the_toolkit_pins_the_wheels_a_run_installs():
    """A Run installs exact files, at the Pint version the native toolkit pins.

    ``requirements.txt`` pins Pint for the reason it gives; the browser used to install whatever
    PyPI had that day. Now both name one version, and everything Pint needs is listed beside it,
    because a wheel installed by URL brings no dependencies with it.
    """
    from sizing.playground.toolkit import WHEELS, wheels

    pins = dict(
        line.strip().split("==")
        for line in (ROOT / "requirements.txt").read_text().splitlines()
        if "==" in line and not line.startswith("#")
    )
    names = {url.rsplit("/", 1)[-1].split("-")[0].lower() for url in wheels()}
    assert any(url.endswith(f"/pint-{pins['Pint']}-py3-none-any.whl") for url in wheels()), (
        "the browser's Pint wheel is not the version requirements.txt pins"
    )
    assert {"flexcache", "flexparser", "platformdirs", "typing_extensions"} <= names
    for url, digest in WHEELS:
        assert url.startswith("https://files.pythonhosted.org/") and url.endswith(".whl"), url
        assert re.fullmatch(r"[0-9a-f]{64}", digest), url


def test_the_toolkit_pins_the_runner_a_check_installs():
    """A Check runs pytest at the version ``requirements-dev.txt`` pins for the native suite.

    The verdict under a problem in the page is meant to be the verdict the same test gives at a
    desk, and that holds only while both run the same runner. Everything pytest imports is
    beside it, for the reason Pint's wheels are: a wheel installed by URL brings nothing with it.
    """
    from sizing.playground.toolkit import PROBLEM_WHEELS, offline_manifest, problem_wheels, wheels

    pins = dict(
        line.strip().split("==")
        for line in (ROOT / "requirements-dev.txt").read_text().splitlines()
        if "==" in line and not line.startswith("#")
    )
    assert any(
        url.endswith(f"/pytest-{pins['pytest']}-py3-none-any.whl") for url in problem_wheels()
    ), "the browser's pytest wheel is not the version requirements-dev.txt pins"
    names = {url.rsplit("/", 1)[-1].split("-")[0].lower() for url in problem_wheels()}
    assert {"pluggy", "iniconfig", "packaging", "pygments"} <= names
    for url, digest in PROBLEM_WHEELS:
        assert url.startswith("https://files.pythonhosted.org/") and url.endswith(".whl"), url
        assert re.fullmatch(r"[0-9a-f]{64}", digest), url
    # The offline control keeps what a Check fetches as well as what a Run does.
    assert offline_manifest()["wheels"] == wheels() + problem_wheels()


def test_every_page_that_boots_the_toolkit_hands_it_the_same_wheels():
    """Three pages boot the runtime, and each has to pass the pinned wheels to the one boot."""
    boot = (ROOT / "sizing" / "playground" / "boot.js").read_text()
    assert 'loadPackage(["numpy", "pyyaml", ...(wheels || [])])' in boot
    assert "micropip" not in boot, "an install by name is an install of whatever PyPI has today"
    assert "wheels: WHEELS" in (ROOT / "scripts" / "build-site.py").read_text()
    assert 'id="model-wheels"' in (ROOT / "scripts" / "build-site.py").read_text()
    assert "wheels: WHEELS" in (ROOT / "scripts" / "build-playground.py").read_text()
    assert "wheels: TOOLKIT.wheels" in (ROOT / "sizing" / "viewer" / "app.js").read_text()
    assert '"wheels": wheels()' in (ROOT / "scripts" / "build-viewers.py").read_text()


HARNESS = r"""
const script = process.argv[2];
const spec = JSON.parse(process.argv[3]);
const puts = [], listeners = {};
const span = { textContent: "" };
const button = {
  hidden: true, disabled: false, dataset: { state: "" },
  querySelector: () => span,
  addEventListener: (name, fn) => { listeners[name] = fn; },
};
globalThis.window = globalThis;
globalThis.document = {
  getElementById: (id) => (id === "offline" ? button : null),
  addEventListener: (name, fn) => { listeners[name] = fn; },
};
// Node has a navigator of its own, read-only, so it has to be replaced rather than assigned.
Object.defineProperty(globalThis, "navigator", { configurable: true, value: {
  serviceWorker: {}, onLine: true, storage: { persist: async () => true } } });
globalThis.confirm = () => true;
const lock = { packages: {
  numpy: { file_name: "numpy-x.whl", depends: ["openblas"] },
  openblas: { file_name: "openblas-x.zip", depends: [] },
  pyyaml: { file_name: "pyyaml-x.whl", depends: [] },
  micropip: { file_name: "micropip-x.whl", depends: ["packaging"] },
} };
const body = (url) => url.endsWith("pyodide-lock.json") ? JSON.stringify(lock) : "x".repeat(1000);
const respond = (url) => ({
  ok: true, clone() { return respond(url); },
  json: async () => JSON.parse(body(url)),
  arrayBuffer: async () => new ArrayBuffer(body(url).length),
});
const store = new Map();
globalThis.caches = {
  open: async () => ({
    match: async (url) => store.get(url),
    put: async (url, response) => { puts.push(url); store.set(url, response); },
  }),
  delete: async () => store.clear(),
};
globalThis.fetch = async (url) => respond(url);
new Function(script)();
(async () => {
  await listeners.DOMContentLoaded();
  await new Promise((r) => setTimeout(r, 10));
  const before = { hidden: button.hidden, label: span.textContent };
  await listeners.click();
  console.log(JSON.stringify({ before, puts, label: span.textContent, state: button.dataset.state }));
})();
"""


def test_the_offline_control_keeps_everything_a_run_fetches(tmp_path):
    """Pressed, it puts the runtime's own files, the lock file's packages with what they depend
    on, and every pinned wheel into the worker's cache, and then says so. Unpressed, it fetches
    nothing and is merely shown."""
    import json
    import subprocess

    from sizing.playground.toolkit import PYODIDE, offline_manifest, problem_wheels, wheels

    build_site = site()
    script = re.sub(r"^\s*<script>|</script>\s*$", "", build_site.OFFLINE_SCRIPT.strip())
    harness = tmp_path / "harness.js"
    harness.write_text(HARNESS)
    out = subprocess.run(
        ["node", str(harness), script, json.dumps(offline_manifest())],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    report = json.loads(out.stdout.strip().splitlines()[-1])
    assert report["before"] == {"hidden": False, "label": ""}, report
    expected = {
        *(
            PYODIDE + f
            for f in (
                "pyodide.mjs",
                "pyodide.asm.js",
                "pyodide.asm.wasm",
                "python_stdlib.zip",
                "pyodide-lock.json",
            )
        ),
        *(PYODIDE + f for f in ("numpy-x.whl", "openblas-x.zip", "pyyaml-x.whl")),
        *wheels(),
        *problem_wheels(),
    }
    assert set(report["puts"]) == expected, sorted(set(report["puts"]) ^ expected)
    assert report["label"] == "Kept offline" and report["state"] == "kept", report


def test_the_offline_worker_lists_exactly_what_the_build_produced(tmp_path):
    """A service worker's precache is a promise: every path on it is fetched on install, and one
    missing path fails the whole install in the reader's browser. So the list is derived from the
    tree rather than written, and this holds it to the tree."""
    import subprocess
    import sys

    site = tmp_path / "site"
    (site / "models").mkdir(parents=True)
    (site / "playground" / "capacity").mkdir(parents=True)
    (site / "index.html").write_text("<html><head><title>x</title></head><body></body></html>")
    (site / "capacity.html").write_text("<html><head></head><body></body></html>")
    (site / "models" / "web_service-reference.html").write_text("<html><head></head></html>")
    (site / "playground" / "capacity" / "index.html").write_text("<html><head></head></html>")
    (site / "search.json").write_text("[]")
    (site / "favicon.svg").write_text("<svg/>")
    (site / "sitemap.xml").write_text("<urlset/>")  # not a page: not kept

    def run():
        return subprocess.run(
            [sys.executable, "scripts/build-offline.py", "--inject", str(site), "--base", "/b"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

    first = run()
    assert first.returncode == 0, first.stdout + first.stderr
    worker = (site / "sw.js").read_text()
    assert '"/b/"' in worker, "the base path the site is served from"
    kept = re.search(r"const PRECACHE = (\[.*?\]);", worker, re.S).group(1)
    assert json.loads(kept) == [
        "capacity.html",
        "favicon.svg",
        "index.html",
        "models/web_service-reference.html",
        "playground/capacity/index.html",
        "search.json",
    ]
    for page in site.rglob("*.html"):
        assert page.read_text().count("serviceWorker.register(") == (
            1 if "<head>" in page.read_text() else 0
        )
    # Idempotent: the deploy may run it twice, and a page that registers two workers is a bug.
    version = re.search(r'const VERSION = "([0-9a-f]+)";', worker).group(1)
    second = run()
    assert second.returncode == 0
    assert (site / "index.html").read_text().count("serviceWorker.register(") == 1
    assert (
        re.search(r'const VERSION = "([0-9a-f]+)";', (site / "sw.js").read_text()).group(1)
        != version
    ), (
        "registering the worker changed every page, so the content hash must change too; "
        "a version that ignores the pages' own bytes would leave readers on a stale copy"
    )


#: The page's own arithmetic for a verdict, lifted out of the script that carries it. Sliced by
#: text because the rest of the script talks to a document, which node has not got.
def counting() -> str:
    runner = site().PROBLEMS
    start = runner.index("function score(tests) {")
    return runner[start : runner.index("\n}\n", start) + 3]


@pytest.mark.node
def test_the_page_counts_the_tests_the_reader_has_to_pass(tmp_path):
    """Not the book's scaffolding beside them, which passes whatever the reader types.

    Counting every test in the file told a reader who had typed nothing that four of six tests
    passed, and would have withheld "solved" from a right answer until the book's own checks
    passed too. A scaffolding failure is the book's fault, so it is counted nowhere and shown
    on its own.
    """
    if shutil.which("node") is None:
        pytest.skip("no node")
    mine = {"problem": True, "outcome": "failed"}
    book = {"problem": False, "outcome": "passed"}
    cases = {
        "untouched": [mine, mine, book, book, book, book],
        "half": [{**mine, "outcome": "passed"}, mine, book, book],
        "solved": [{**mine, "outcome": "passed"}, {**mine, "outcome": "passed"}, book],
        "book_broken": [{**mine, "outcome": "passed"}, {**book, "outcome": "failed"}],
    }
    harness = """
    const out = {};
    for (const [name, tests] of Object.entries(JSON.parse(process.argv[2]))) {
      const verdict = score(tests);
      out[name] = {yours: verdict.yours.length, passed: verdict.passed,
                   book: verdict.book.length, solved: verdict.solved};
    }
    console.log(JSON.stringify(out));
    """
    script = tmp_path / "score.mjs"
    script.write_text(counting() + textwrap.dedent(harness))
    run = subprocess.run(
        ["node", str(script), json.dumps(cases)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert run.returncode == 0, run.stderr[-2000:]
    got = json.loads(run.stdout)
    assert got["untouched"] == {"yours": 2, "passed": 0, "book": 0, "solved": False}
    assert got["half"] == {"yours": 2, "passed": 1, "book": 0, "solved": False}
    assert got["solved"] == {"yours": 2, "passed": 2, "book": 0, "solved": True}
    assert got["book_broken"] == {"yours": 1, "passed": 1, "book": 1, "solved": True}, (
        "a failing scaffolding test is the book's fault and never the reader's, so it neither "
        "counts against them nor withholds the verdict they have earned"
    )


def test_each_rail_has_a_control_and_the_chapter_takes_the_room_back():
    """Two rails, two buttons, and the measure on each thing rather than on the column.

    A reader working through a wide graph wants the window. Closing the chapter list gave the
    room to the chapter already; closing this page's outline did not, because it had no
    control. With both closed the shell's own cap comes off too, and what widens is a model,
    the runner and a table -- never a line of prose, which keeps the measure at every width.
    """
    build_site = site()
    page = build_site.PAGE
    css = build_site.CSS
    # The button names the rail it controls, and ships hidden because it needs the script.
    assert 'id="outline"' in page and 'aria-controls="toc"' in page
    assert '<aside id="toc" class="toc"' in page
    assert page.index('id="outline"') < page.index('id="menu"'), (
        "the two rail controls sit together"
    )
    assert "[hidden] { display: none !important; }" in css, (
        "a class that sets display beats the browser's rule for the attribute, so a control "
        "written hidden showed anyway and did nothing when pressed"
    )
    # Four states, one per pair of rails, and the cap comes off only when both are away.
    for selector in (
        "html.nav-closed .shell { grid-template-columns: minmax(0, 1fr) 14rem; }",
        "html.toc-closed .shell { grid-template-columns: 17rem minmax(0, 1fr); }",
        "html.nav-closed.toc-closed .shell { grid-template-columns: minmax(0, 1fr); max-width: none; }",
        "html.toc-closed .toc { display: none; }",
    ):
        assert selector in css, selector
    # The measure moved off the column and onto each child, after the rule that caps the column.
    assert css.index("main > * { max-width: var(--measure); margin-inline: auto; }") > css.index(
        "main { padding: 1rem clamp(1rem, 4vw, 2.6rem) 6rem;"
    ), "a media query adds no specificity, so the rule that lifts the cap has to come after it"
    assert (
        "main > :is(figure:has(> iframe), figure:has(> .runner), table) { max-width: 100%; }" in css
    )
    # Both choices are read before the page paints, so a rail does not close again on every page.
    opening = build_site.MENU.split("document.addEventListener")[0]
    assert 'localStorage.getItem("nav") === "closed"' in opening
    assert 'localStorage.getItem("toc") === "closed"' in opening


def test_a_models_box_follows_the_layout_the_model_chose():
    """One fixed height fits none of the viewer's three layouts, and it has all three now."""
    css = site().CSS
    assert "figure:has(> iframe.viewer) { container-type: inline-size; }" in css
    assert "@container (min-width: 860px) { iframe.viewer { height: 600px; } }" in css
    assert "@container (min-width: 1101px) { iframe.viewer { height: 812px; } }" in css
