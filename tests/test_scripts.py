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
    ("scripts/build-futures.py", "--out"),
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


#: The constants that hold JavaScript rather than Python, and the file each one is in.
JS_TEMPLATES = (
    [
        ("scripts/build-site.py", name)
        for name in ("EXPAND", "MENU", "OFFLINE", "PROBLEMS", "SEARCH")
    ]
    + [("bench/theme.py", name) for name in ("_PARENT", "FRAME")]
    + [("bench/reading.py", "_PARENT")]
)


@pytest.mark.parametrize(("where", "name"), JS_TEMPLATES)
def test_a_javascript_template_is_a_raw_string(where, name):
    """Python must not eat the escapes in a script it is only carrying.

    This has bitten twice. A ``\\n`` inside a JavaScript regex became a real newline, and a
    regex literal cannot span lines, so the page shipped JavaScript that would not parse --
    silently, because nothing on the Python side was wrong. The fix both times was a raw
    string, and this is what stops the third time.
    """
    source = (ROOT / where).read_text()
    raw = f"{name} = r" + '"""'
    assert raw in source, (
        f"{name} in {where} carries JavaScript, so it must be a raw string, "
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


def test_the_takeaways_box_is_drawn_like_a_definition_box_with_its_own_icon():
    """Every chapter's takeaways sit in a `takeaways` box, which is only a box because of this.

    A class the stylesheet has forgotten fails nothing: the page renders a plain list where the
    box was, which is how the box went missing the first time without a test noticing.
    """
    css = site().CSS
    assert ".takeaways {" in css or ".takeaways," in css, (
        "the takeaways box is not drawn like a definition"
    )
    icon = re.search(r"\.takeaways::before \{ content: '([a-z_]+)'; \}", css)
    assert icon, "the takeaways box has no icon"
    assert icon[1] != "menu_book", "the takeaways box borrows the definition box's icon"


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


def test_the_model_file_page_shows_the_file_and_runs_nothing():
    """The file beside a chapter's graph is there to be read. The graph is what a reader moves.

    It used to be a second place to run the model, with its own Run, its own editor and a ten
    megabyte download, from before the chapters embedded the graph.
    """
    module = playground()
    stage = next(iter(module.pages().values()))
    page = module.build(stage)
    assert "<pre>" in page and stage.path.read_text().splitlines()[-1].strip() in page
    for sign in ("<textarea", "<button", "contenteditable", "bootToolkit", "pyodide"):
        assert sign not in page, f"the model file page still carries {sign}"


def test_every_playground_the_build_ships_is_reachable_from_its_chapter():
    """A page nobody links is a page nobody reads, and nobody proofreads either.

    The build shipped five of these and two were embedded. The three orphans deployed on every
    push, cost a Pyodide fetch to anybody who found them, and one of them printed a sentence that
    contradicted itself -- it told a reader the model had neither a measured constant nor a
    ceiling while classifying it as a conditional model, which is only possible because it has one.
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


def test_the_prose_column_is_measured_in_characters():
    """The column has to grow when the reader's text does, or the line collapses.

    The prose is sized in ``px`` and the column was capped in ``rem``, which is the root font.
    Those two never move together: a minimum-font-size floor, an accessibility text size or a
    user stylesheet raises the glyphs and leaves the column where it was, and the reader gets a
    column too narrow for their own text. Measured in a browser, an 18px page at 576px holds 78
    characters to a line; the same 576px holds 42 at 32px text and 31 at 40px. It fails the
    other way too -- raise the browser's default font size and ``36rem`` grows while 18px prose
    does not, so the line gets longer rather than shorter.

    So the cap is ``max(--measure, --prose)`` with ``--prose`` in ``ch``, which resolves against
    the element's own font, and the line stays the same length whatever the reader's text does.

    ``ch`` is the width of a zero, and Charter's lowercase is narrower than its zero, so the
    number in the declaration is not the number of characters: 82ch renders 101 a line, 64ch
    rendered 78. Counted per rendered line over six paragraphs, last lines excluded -- an
    average that includes them measures where the paragraphs end rather than where the column
    does, and reports 64 for the column that holds 78.
    """
    css = (ROOT / "scripts" / "build-site.py").read_text()

    prose = re.search(r"--prose:\s*([\d.]+)(ch|em)\s*;", css)
    assert prose, "--prose is not declared in a unit relative to the text it measures"

    # Registered as a <length>, or it is substituted as three characters and resolved against
    # whichever element reads it -- so a heading measures it in the heading's font and comes out
    # a different width from the text beneath it. That shipped, and indented every heading.
    assert re.search(r'@property --prose \{[^}]*syntax:\s*"<length>"', css), (
        "--prose is not registered as a <length>, so it resolves per element rather than once "
        "in the prose font, and blocks in one chapter will not share a column"
    )

    # One cap for every block in the chapter, so they share a left edge. The wide tiers override
    # it afterwards on their own selectors; nothing else may.
    generic = re.search(r"#main > \* \{ max-width: ([^;]+);", css)
    assert generic, "nothing caps the chapter's blocks"
    assert "--prose" in generic.group(1), (
        f"blocks are capped by {generic.group(1)!r}, which ignores --prose. A heading capped "
        "apart from its paragraphs is centred in a narrower box and reads as indented."
    )
    text = re.search(r"p, li \{ max-width: ([^;]+);", css)
    assert text and text.group(1) == generic.group(1), (
        f"prose is capped by {text and text.group(1)!r} and the blocks around it by "
        f"{generic.group(1)!r}. Two caps drift apart the moment one of them moves."
    )


def test_every_embedded_directory_gets_the_base_path():
    """A `/futures/...` that nothing rebased is a 404 on the project site and nowhere else.

    MyST rewrites `href` for a base path and does not rewrite an `{iframe}` directive's `src`, so
    ``build-icons.py`` stamps the base onto the root-relative URLs this repository publishes
    beside the book. It does that from a pattern, and a pattern is a list: add a publish
    directory, forget the list, and every chapter embedding that directory breaks on deploy and
    only on deploy -- ``check-built-links.py`` at the site root cannot tell a URL missing the base
    path from one that has it.

    That has now happened twice. This asserts the pattern covers every directory the chapters
    actually embed, read from the chapters rather than from a third list.
    """
    from importlib import util

    spec = util.spec_from_file_location("build_icons", ROOT / "scripts" / "build-icons.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    embedded = {
        match
        for path in (ROOT / "chapters").glob("*.md")
        for match in re.findall(r"\{iframe\}\s+/([a-z0-9-]+)/", path.read_text())
    }
    assert embedded, "no chapter embeds a panel -- this test is checking nothing"
    for directory in sorted(embedded):
        url = f'src="/{directory}/whatever.html"'
        assert module.UNBASED.search(url), (
            f"a chapter embeds /{directory}/ and build-icons.py would not give it the base path, "
            f"so every reader of that chapter gets a 404 on the project site"
        )


def test_the_pages_that_run_the_toolkit_share_one_runtime_and_one_boot():
    """Two pages start Python in a browser. One copy of how, or they drift.

    The inline runner, the playground and the viewer each carried their own runtime URL, module
    list and boot sequence until the third one was about to be written. Now
    ``sizing/playground/toolkit.py`` holds the URL and the list, ``boot.js`` the sequence, and
    every builder inlines them. A builder that spells the CDN out again is a fourth copy.
    """
    builders = ("scripts/build-site.py", "scripts/build-viewers.py")
    for builder in builders:
        text = (ROOT / builder).read_text()
        assert "cdn.jsdelivr.net/pyodide" not in text, f"{builder} pins its own runtime URL"
        assert "{boot}" in text, f"{builder} does not inline boot.js"
        assert "from sizing.playground.toolkit import" in text, f"{builder} does not import toolkit"
    # The call itself: in the chapter page's template, and in the viewer's own app. A chapter
    # page goes through the shared start, because its Checks are one runtime.
    for caller in ("scripts/build-site.py", "sizing/viewer/app.js"):
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
    # The offline control keeps what a Check fetches as well as what a Resample does.
    assert offline_manifest()["wheels"] == wheels() + problem_wheels()


def test_every_page_that_boots_the_toolkit_hands_it_the_same_wheels():
    """Two pages boot the runtime, and each has to pass the pinned wheels to the one boot."""
    boot = (ROOT / "sizing" / "playground" / "boot.js").read_text()
    assert 'loadPackage(["numpy", "pyyaml", ...(wheels || [])])' in boot
    assert "micropip" not in boot, "an install by name is an install of whatever PyPI has today"
    assert "wheels: SPEC.wheels" in (ROOT / "scripts" / "build-site.py").read_text()
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
    # Four states, one per pair of rails, and the cap comes off only when both are away. The
    # column's width is read rather than written: what this is checking is that all four states
    # use the same one, and pinning the number here means a change to it fails four tests that
    # have nothing to say about it.
    wide = re.search(r"calc\((\d+)rem \+ 5rem\)", css)
    assert wide, "the middle column is the widest thing a chapter holds, plus its gutter"
    column = f"minmax(0, calc({wide.group(1)}rem + 5rem))"
    for selector in (
        f"html.nav-closed .shell {{ grid-template-columns: {column} var(--toc); }}",
        f"grid-template-columns: var(--nav) {column}; }}",
        f"grid-template-columns: {column}; max-width: none; }}",
    ):
        assert selector in css, selector
    # Two ways the outline goes: the reader closed it, or the chapter could not spare the room.
    # They are the same layout, so every rule that serves one serves the other -- written apart,
    # the arithmetic one would hide the rail and leave its column standing empty.
    for selector, declaration in (
        ("", "grid-template-columns: var\\(--nav\\)"),
        (" \\.toc", "display: none"),
    ):
        for state in ("toc-closed", "toc-cramped"):
            assert re.search(
                rf"html\.{state}{selector}[^{{}}]*\{{[^}}]*{declaration}", css, re.S
            ), f"nothing gives `{state}` its {declaration.replace(chr(92), '')}"
    # The measure moved off the column and onto each child, after the rule that caps the column.
    assert css.index("#main > * { max-width:") > css.index(
        "main { padding: 1rem clamp(1rem, 4vw, 2.6rem) 6rem;"
    ), "a media query adds no specificity, so the rule that lifts the cap has to come after it"
    # Both choices are read before the page paints, so a rail does not close again on every page.
    opening = build_site.MENU.split("document.addEventListener")[0]
    assert 'localStorage.getItem("nav") === "closed"' in opening
    assert 'localStorage.getItem("toc") === "closed"' in opening


def test_the_rails_take_the_room_as_it_appears():
    """A chapter list that wraps is hard to scan, and the room to fix it arrives gradually.

    Sixteen of the thirty-nine entries wrapped at 17rem, and "What this cannot tell you" wrapped
    in a 14rem outline that needed 228px. A single step at 96rem fixed that for a desk and gave
    a 1512 laptop nothing, 1512 being the commonest width there is. The rails grow with the
    window instead: the middle column stops needing every pixel past 1440, which is where an
    embedded model still clears the 861px its layout needs to put the inputs beside the graph,
    so the extra a rail may take is what the window has over 1440. The ramp starts a rem later
    than that, because `100vw` counts a classic scrollbar the layout does not have.

    Swept over the reader's text size as well as the window, which the first version of this was
    not, and that is how it passed while the layout was broken. It hardcoded ``rem = 16`` and so
    only ever checked a reader on browser defaults. ``rem`` means two things here: in these
    declarations it is the reader's text, and in the ``@media`` rules that decide whether a rail
    is shown at all the spec fixes it at 16px whatever the reader has done. At 24px text the
    layout showed both rails and drew them half as wide again -- 744px of a 1440px window, the
    chapter down to 696px, the code to 65 of its 100 columns, the model to 581px and stacked.
    """
    css = site().CSS
    # The shape is fixed; the numbers in it are free to move, and the arithmetic below is what
    # says whether they may. Pinning both here would mean only the shape was ever checked.
    assert "--rails: clamp(0rem, (100vw" in css, (
        "the rails take nothing under a start width and never more than a cap"
    )
    assert "--nav: min(calc(" in css and "var(--rails)" in css, "the chapter list takes a share"
    assert "--toc: min(calc(" in css, "so does the outline"
    assert "@media (min-width: 96rem)" not in css, (
        "the step this replaced skipped every window between 1440 and 1536"
    )
    assert "max-width: 126rem;" in css, (
        "the shell's own cap is what hands the rails their room rather than a margin"
    )
    assert "grid-template-columns: 17rem" not in css and "5rem)) 14rem" not in css, (
        "every grid rule reads the variables, or widening one rail moves only some of them"
    )
    ramp = re.search(
        r"--rails: clamp\(0rem, \(100vw - ([\d.]+)rem\) \* ([\d.]+), ([\d.]+)rem\)", css
    )
    assert ramp, "the ramp is a clamp of the window less a start, with a slope and a cap"

    rails = {}
    for rail in ("nav", "toc"):
        got = re.search(
            rf"--{rail}: min\(calc\(([\d.]+)rem \+ var\(--rails\) \* ([\d.]+)\), "
            rf"([\d.]+)px\)",
            css,
        )
        assert got, f"--{rail} is its own width plus a share of the ramp, capped in px"
        rails[rail] = (float(got[1]), float(got[2]), float(got[3]))
    assert abs(sum(share for _, share, _ in rails.values()) - 1) < 1e-9, (
        "the two shares are the whole of the ramp, or the cap does not mean what it says"
    )
    # Each cap is that rail at its widest on browser defaults, so a reader who has changed
    # nothing sees exactly what they saw before, at every window width.
    for rail, (base, share, cap) in rails.items():
        widest = base * 16 + float(ramp[3]) * 16 * share
        assert abs(cap - widest) < 0.5, (
            f"--{rail} is capped at {cap:.0f}px but reaches {widest:.0f}px on browser defaults, "
            f"so the cap changes the page for a reader who never asked for anything"
        )

    def width(rail, rem, window):
        base, share, cap = rails[rail]
        taken = min(float(ramp[3]) * rem, max(0.0, window - float(ramp[1]) * rem)) * share
        return min(base * rem + taken, cap)

    needs, column = 861, float(re.search(r"calc\((\d+)rem \+ 5rem\)", css)[1]) * 16
    shell = float(re.search(r"\.shell \{[^}]*max-width: ([\d.]+)rem", css, re.S)[1]) * 16
    # Every text size a reader might be on, not just the one the browser ships with.
    for rem in (16, 18, 20, 24, 28, 32):
        padding = min(max(rem, 0.04 * 1440), 2.6 * rem) * 2
        for window in range(1400, 2400, 4):
            nav, toc = width("nav", rem, window), width("toc", rem, window)
            # The outline gives way when the chapter cannot have what a model needs; the page
            # measures that for itself, because a media query cannot see the reader's text.
            if window - nav - toc - padding < needs:
                toc = 0
            model = min(min(window, shell) - nav - toc - padding, column)
            assert model >= needs or window - nav - padding < needs, (
                f"{window}px at {rem}px text: the chapter gets {model:.0f}px and a model's "
                f"layout needs {needs}px, with the outline already away"
            )


def test_the_model_panel_says_how_far_a_slider_reaches():
    """Dragging an input and watching nothing move is a question the page used to leave open.

    A reader moved "records held, day one" and the five-year total did not budge, which reads as
    a broken page and is in fact the model's argument: the bill is for the fleet somebody decided
    to buy. One hop of "Feeds" cannot say that, so the panel names which of the model's declared
    outputs an input reaches and, more usefully, which it cannot.
    """
    app = (ROOT / "sizing" / "viewer" / "app.js").read_text()
    assert "const reach = descendants(name);" in app, "the forward closure, not one hop"
    assert "PAYLOAD.outputs.filter((o) => o !== name && reach.has(o))" in app
    assert "PAYLOAD.outputs.filter((o) => o !== name && !reach.has(o))" in app, (
        "naming what it cannot move is the half that answers the question"
    )
    assert "Cannot move:" in app
    # And the same reach, while a slider is held, over the outputs table.
    assert "const reach = touched ? descendants(touched) : null;" in app
    assert "Greyed rows cannot be moved by" in app, (
        "a greyed row with no explanation is a new puzzle rather than an answer"
    )
    css = (ROOT / "sizing" / "viewer" / "style.css").read_text()
    assert "#outputs tr.inert td { color: var(--muted); }" in css


def test_a_choice_is_marked_as_one_and_a_year_in_seconds_is_not():
    """Both graphs read the model's own declaration rather than inferring it.

    The inference available -- an input with no distribution is a decision -- files six unit
    anchors in this model as choices, and the records a service's users uploaded as one too.
    `decided` is the model saying which is which, so the mark is a claim it makes rather than a
    guess about how finished the file is.
    """
    from sizing.dsl import discover

    app = (ROOT / "sizing" / "viewer" / "app.js").read_text()
    assert 'const isDecision = (node) => node.decided === "you";' in app
    assert "!node.distribution" not in app, "the heuristic is gone, not merely unused"
    drawing = (ROOT / "bench" / "diagrams.py").read_text()
    assert 'if lit and node.get("decided") == "you":' in drawing
    # The payload the graphs read has to carry it.
    assert 'entry["decided"] = node.decided' in (ROOT / "sizing" / "export.py").read_text()

    # And the classification says what a reader would say.
    web = next(m for m in discover() if m.name == "web_service")
    assert web.nodes["hosts"].decided == "you", "the fleet is the decision the book is about"
    assert web.nodes["stored_data_t0"].decided == "world", (
        "nobody decides how much their users uploaded"
    )
    assert web.nodes["seconds_per_year"].decided == "definition"


def test_a_models_box_follows_the_layout_the_model_chose():
    """One fixed height fits none of the viewer's three layouts, and it has all three now."""
    css = site().CSS
    assert "figure:has(> iframe.viewer) { container-type: inline-size; }" in css
    assert "@container (min-width: 860px) { iframe.viewer { height: 600px; } }" in css
    assert "@container (min-width: 1101px) { iframe.viewer { height: 812px; } }" in css


def test_a_chapter_is_two_widths_on_one_middle():
    """Prose, and one column for everything that cannot fit in it. Addressed by the id.

    `p`, every heading, `.admonition`, `.editable-block` and the turn all write `margin: x 0 y`,
    which is the same specificity as `main > *` and comes later in the sheet, so the element
    rule won and the whole page stacked against the left of its column.

    One width for everything was worse in the other direction: the prose column cut 121 code
    blocks over 33 pages off mid-word and left a model far under the 860px its own layout needs
    to put the inputs beside the graph. Three widths was worse again -- prose, then code, then a
    model further out than either, which reads as three columns stacked rather than one. Each
    width is a cap rather than a size, so both centre on the same middle.
    """
    css = site().CSS
    centred = re.search(r"#main > \* \{ max-width: (.+?); margin-inline: auto; \}", css)
    assert centred, (
        "centring a chapter's children has to out-specify the children's own margin rules"
    )
    assert "--measure" in centred.group(1), (
        f"the chapter's blocks are capped by {centred.group(1)!r}, which is not the measure"
    )
    # One selector, holding both tenants. Two selectors is what put a model at a different edge
    # from the code block above it.
    # Non-greedy to the first `)` that a `max-width` follows: the selector has `:has(...)` in
    # it, so a paren-counting pattern would stop inside it.
    wide = re.search(r"#main > :is\((.*?)\)\s*\{\s*max-width: ([^;]+);", css, re.S)
    assert wide, "nothing caps the wide column"
    selector, cap = wide.group(1), wide.group(2)
    for part in (
        "figure:has(> iframe)",
        "table",
        "pre",
        ".editable-block",
        ".problem",
        "figure:has(> pre)",
    ):
        assert part in selector, (
            f"{part} is not in the wide column, so it sits at an edge of its own"
        )
    assert "--prose" in cap, (
        f"the wide column is capped by {cap!r}, which cannot grow with the reader's text -- so "
        "a paragraph can end up wider than the block it introduces"
    )
    assert "min(100%," in cap, (
        "a cap in rem alone overflows the column on a narrow window; it yields to the room "
        "there actually is"
    )
    assert css.index("#main > :is(") > css.index("#main > * {"), (
        "the measure is the default and the wider cap is the exception, so it has to come "
        "after it -- at equal specificity the later rule wins"
    )

    # What the number has to clear, read from the files that set it rather than restated. The
    # model viewer is a separate document with its own breakpoint, and the two drifting apart is
    # invisible here: the chapter would simply stop showing the detail panel beside the graph.
    rem = 16
    tier = float(re.search(r"max\((\d+(?:\.\d+)?)rem,", cap).group(1)) * rem
    viewer = (ROOT / "sizing" / "viewer" / "style.css").read_text()
    panel = float(re.search(r"@media \(max-width: (\d+)px\)", viewer).group(1))
    assert tier > panel, (
        f"the wide column is {tier:.0f}px and the model viewer stacks its detail panel under "
        f"the graph at {panel:.0f}px, so an embedded model never shows it"
    )
    # The book's own code lines stop at 100 columns; its widest block draws at 942px.
    assert tier >= 942, f"the wide column is {tier:.0f}px and the widest code block wants 942px"


def test_a_model_can_take_the_window_without_losing_the_reader_s_place():
    """The chapter holds a model at 84rem; the button over its corner gives it the window.

    A model's graph is drawn at a fixed width -- 1470px for the widest in the book -- so no
    column can hold it and a wider card only shows more of it. Letting the card follow the
    window instead put a slab three times the width of the prose in the middle of a chapter.
    The control keeps the same frame rather than opening the model's own page, which reloads
    it: every slider the reader has moved stays where they put it, and closing returns them to
    the paragraph they were reading.
    """
    from bench import render as renderer

    build_site = site()
    drawn = renderer.render(
        {"type": "iframe", "src": "/models/web_service-reference.html"},
    )
    assert drawn.index('class="expand"') < drawn.index("<iframe"), (
        "the control belongs to the figure, over the panel's corner, not inside the model"
    )
    assert 'aria-expanded="false"' in drawn and "hidden>" in drawn, (
        "it does nothing without the script, so it is not there without it"
    )
    css = build_site.CSS
    assert "figure.container:has(> iframe) { position: relative; }" in css, (
        "a model's button sits over the corner of the frame, which reserves room for it"
    )
    assert "html.model-open { overflow: hidden; }" in css, "the page must not scroll behind it"
    assert "html.model-open #main .expanded { position: fixed; inset: 0;" in css, (
        "a table can sit inside a note, so the overlay cannot want a direct child"
    )
    assert "const cut = (el) => el.scrollWidth > el.clientWidth + 1;" in build_site.EXPAND, (
        "code and tables get the control only where they are actually cut off, which the page "
        "can know only by measuring"
    )
    assert 'if (el.tagName !== "TABLE") return cut(el);' in build_site.EXPAND, (
        "a table shrinks to its column and wraps every cell rather than overflowing it, so "
        "`cut` said no to 65 of the book's 96 tables while the reader saw a heading broken "
        "over three lines; each one has to be asked what it would be unsqueezed"
    )
    script = build_site.EXPAND
    assert "window.scrollTo(0, scrolled)" in script, (
        "the figure leaves the flow while it is open, so the page under it moves"
    )
    assert 'event.key === "Escape"' in script
    assert "button.hidden = false" in script


def test_a_control_never_sits_on_the_thing_it_opens():
    """Over the corner works on a model and nowhere else, because a table has words there.

    A model's own page reserves 104px in its header for the button above it, so the corner is
    empty by arrangement. A table reserves nothing: on a 390px phone the control sat on the
    third column's heading, and once open it sat on the header row, which is the one row the
    reader needs to make sense of the rest. The wrapper puts it above instead, right-aligned,
    where it covers nothing at any width.
    """
    build_site = site()
    css = build_site.CSS
    assert (
        ".wide-block > .expand { position: static; width: fit-content; margin: 0 0 .4rem auto; }"
        in css
    ), "taken out of the flow it overlays the block; left in it, above and right, it does not"
    # Open, the control is pinned to the window rather than laid out in the box, because the box
    # scrolls: at the right-hand edge of a 715px table in a 412px phone, a control in the flow is
    # 300px away from a reader who has scrolled back to the first column. Pinned it is out of the
    # flow, so the box keeps a row for it -- or it lands on the header row, which is the fault
    # the control was moved out of the corner to fix, arriving by the other door.
    assert "html.model-open #main .expanded > .expand { position: fixed;" in css
    assert "html.model-open #main .expanded:has(> .expand) { padding-top:" in css, (
        "the control is out of the flow and the box keeps no row for it, so it sits on the "
        "first line of whatever it just opened"
    )
    assert ".wide-block { position: relative" not in css, (
        "a wrapper that establishes a containing block invites the button back over the content"
    )
    # The page behind an expanded box cannot scroll, so anything outside the box is unreachable
    # rather than merely off-screen. A phone had 715px of table in a 412px box with the last
    # three columns simply gone.
    opened = re.search(r"html\.model-open #main \.expanded \{([^}]*)\}", css, re.S)
    assert opened and "overflow: auto" in opened.group(1), (
        "the expanded box does not scroll, and `model-open` stops the page scrolling too, so "
        "content wider than the window has nothing that can reach it"
    )
    assert "html.model-open { overflow: hidden; }" in css, (
        "the reason the box has to scroll; if this goes, the assertion above is the wrong one"
    )
    # The stylesheet can only put the control on top if the script puts it there first.
    script = build_site.EXPAND
    wrapping = script[script.index('box.className = "wide-block"') :]
    wrapping = wrapping[: wrapping.index("wire(box, button)")]
    assert wrapping.index("box.appendChild(button)") < wrapping.index("box.appendChild(el)"), (
        "the button is appended before the block it opens, or it renders underneath it"
    )


def test_a_figure_and_a_model_follow_the_page_into_the_dark():
    """The book's own drawings are written inline, so the stylesheet can reach into them.

    They are drawn once, in daylight. On a dark page the stylesheet swaps each colour for the
    counterpart `bench.diagrams.DARK_FIGURE` names, colour by colour rather than by inverting,
    because red means a ceiling and a ceiling that came out cyan would say nothing. The model
    panel is its own document, so it carries its own dark palette.
    """
    from bench.diagrams import DARK_FIGURE

    css = site().CSS
    for light, dark in DARK_FIGURE.items():
        assert f'#main svg [fill="{light}"] {{ fill: {dark}; }}' in css, light
        assert f'#main svg [stroke="{light}"] {{ stroke: {dark}; }}' in css, light
    viewer = (ROOT / "sizing" / "viewer" / "style.css").read_text()
    assert "@media (prefers-color-scheme: dark)" in viewer
    outside = re.sub(r":root \{.*?\}", "", viewer, flags=re.S)
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b", outside), (
        "a colour written into a rule cannot follow the page; every one belongs in the palette"
    )


def _palettes(css):
    """The light and the dark value of every colour a stylesheet names."""
    out = {}
    dark_at = css.find("prefers-color-scheme: dark")
    for block in re.finditer(r":root[^{]*\{(.*?)\n\s*\}", css, re.S):
        scheme = "dark" if dark_at != -1 and block.start() > dark_at else "light"
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})", block.group(1)):
            out.setdefault(scheme, {})[name] = value
    return out


def _contrast(one, other):
    """WCAG relative contrast between two hex colours."""

    def light(value):
        value = value.lstrip("#")
        if len(value) == 3:
            value = "".join(c * 2 for c in value)
        channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]
        linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    high, low = sorted((light(one), light(other)), reverse=True)
    return (high + 0.05) / (low + 0.05)


#: Which colour is read against which surface. A pair here is a pair a reader actually meets:
#: the book's three greys on its three backgrounds, and in the model the node's label and its
#: value on every kind of node, plus each status badge on its own wash.
BOOK_PAIRS = [
    (ink, on) for ink in ("--ink", "--muted", "--faint") for on in ("--bg", "--panel", "--code")
]
VIEWER_PAIRS = [
    (ink, on)
    for ink in ("--ink", "--muted")
    for on in ("--bg", "--panel", "--input", "--derived", "--measured", "--ceiling")
]
VIEWER_PAIRS += [("--ok", "--ok-wash"), ("--warn", "--warn-wash"), ("--over", "--over-wash")]


def test_every_colour_a_reader_has_to_read_clears_the_threshold():
    """Text the book asks somebody to read is at least 4.5:1 against what is behind it.

    None of this is a matter of taste. `--faint` carried every table's headings at 2.4:1 on a
    code block, which is about half of what the smallest readable text needs, and in the model
    the amber badge sat on its own amber wash at 3.0:1. Both read as a decision about emphasis
    until you measure them. The pairs below are the ones a reader meets, so the numbers move
    only when a designer decides they should.
    """
    for label, css, pairs in (
        ("the book", site().CSS, BOOK_PAIRS),
        ("the model", (ROOT / "sizing" / "viewer" / "style.css").read_text(), VIEWER_PAIRS),
    ):
        palettes = _palettes(css)
        assert set(palettes) == {"light", "dark"}, f"{label}: both schemes are declared"
        for scheme, colours in palettes.items():
            for ink, on in pairs:
                assert ink in colours and on in colours, f"{label} {scheme}: {ink} on {on}"
                got = _contrast(colours[ink], colours[on])
                assert got >= 4.5, (
                    f"{label}, in the {scheme}: {ink} ({colours[ink]}) on {on} ({colours[on]}) "
                    f"is {got:.2f}:1, and text this size needs 4.5:1"
                )


def test_the_graph_paints_its_own_labels():
    """SVG text is black until something says otherwise, and the palette cannot reach it.

    The node's value carried `fill="var(--muted)"` from the start; its label carried nothing, so
    it fell back to the SVG default. In daylight black on a pale node is right by accident. Once
    the panel learned to go dark the fills followed the palette and the label did not, which put
    black on `#232d33` -- 1.4:1, and 62 of the 124 labels in one model were that.
    """
    drawing = (ROOT / "sizing" / "viewer" / "app.js").read_text()
    labels = re.findall(r"<text [^>]*>", drawing)
    assert labels, "the graph draws its nodes as SVG text"
    for label in labels:
        assert "fill=" in label, (
            f"every label says what colour it is: {label!r} inherits, and SVG inherits black"
        )
    outside = re.sub(r"^\s*(//|\*|/\*).*$", "", drawing, flags=re.M)
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b", outside), (
        "a colour written into the drawing code cannot follow the reader's page; every one "
        "belongs in the palette, where the dark scheme can answer it"
    )


def test_the_three_columns_sit_together():
    """The middle column is the widest thing a chapter holds, and the group is what centres.

    A middle column of `1fr` left 230px of nothing between the chapter list and the first word
    of the chapter, and the same again before the outline, so the page read as three things
    adrift rather than as one.
    """
    css = site().CSS
    wide = re.search(r"calc\((\d+)rem \+ 5rem\)", css)
    assert wide, "the middle column is the widest thing a chapter holds, plus its gutter"
    assert f"grid-template-columns: var(--nav) minmax(0, calc({wide.group(1)}rem + 5rem));" in css
    assert "justify-content: center;" in css
    assert "minmax(0, 1fr)" not in css.split("@media (min-width: 58rem)")[1], (
        "above the first breakpoint no column is a fraction of the window any more"
    )
