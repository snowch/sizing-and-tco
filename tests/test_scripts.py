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
import subprocess
import sys
from pathlib import Path

import pytest

from bench.stamp import ROOT, shown

#: Scripts that take an output directory and are given a relative one by a workflow, and whether
#: each one can do its job in a checkout that has not been built yet. ``build-pdf.py`` assembles
#: what MyST parsed, so in a fresh clone it has nothing to assemble and says so — which is the
#: state CI is in when it runs the tests, because the book build comes after them.
TAKES_AN_OUT = [
    ("scripts/build-viewers.py", "--out", True),
    ("scripts/build-pdf.py", "--out", False),
    ("scripts/build-icons.py", "--out", True),
    ("scripts/build-playground.py", "--out", True),
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


@pytest.mark.parametrize(
    ("script", "flag", "self_sufficient"), TAKES_AN_OUT, ids=lambda v: Path(str(v)).name
)
def test_a_relative_out_does_not_blow_up(script, flag, self_sufficient):
    """Exactly what deploy.yml does: a repository-relative output directory.

    Run from the repository root with a relative path, because that is the invocation that
    failed. A script that only works with absolute paths works until somebody writes a workflow.

    A script that refuses because its inputs are not there has not failed this check — it has
    passed it, out loud. What fails it is a traceback, which is what printing a path used to
    produce.
    """
    relative = f"_build/test-out/{Path(script).stem}"
    extra = ["--no-myst", "--html-only"] if "pdf" in script else []
    completed = subprocess.run(
        [sys.executable, script, *extra, flag, relative + ("/book.pdf" if "pdf" in script else "")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert "relative_to" not in completed.stderr, (
        f"{script} cannot print a path it was given:\n{completed.stderr[-600:]}"
    )
    assert "Traceback" not in completed.stderr, (
        f"{script} raised where it should have reported:\n{completed.stderr[-600:]}"
    )
    if self_sufficient:
        assert completed.returncode == 0, completed.stderr[-600:]


def test_verify_setup_reports_rather_than_failing_on_a_missing_optional():
    """It is a report. A machine without Chromium is not a broken checkout."""
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
JS_TEMPLATES = ("RUNNER", "SEARCH")


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


def renderer():
    """``scripts/build-pdf.py``, imported. Its name has a dash in it."""
    from importlib import util

    spec = util.spec_from_file_location("build_pdf", ROOT / "scripts" / "build-pdf.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("written", "anchor", "expected"),
    [
        # The short form, which is most of the book.
        ("ch01", "what-one-number-hides", "ch01"),
        # The long form. The separator and the title belong to the author; only the label moves.
        (
            "ch01 · What one number hides",
            "what-one-number-hides",
            "ch01 · What one number hides",
        ),
        # A label left behind by a chapter that moved, in both forms.
        ("ch99", "what-one-number-hides", "ch01"),
        (
            "ch99 · What one number hides",
            "what-one-number-hides",
            "ch01 · What one number hides",
        ),
        (
            "Appendix A · The DSL, in full",
            "appendix-a-dsl-reference",
            "Appendix A · The DSL, in full",
        ),
        # Text that is not a label at all is the author's, and is left alone.
        ("the introduction", "what-one-number-hides", None),
    ],
)
def test_a_reference_keeps_everything_but_its_label(written, anchor, expected):
    """Deriving the number must not eat the separator, which it did.

    The first version of this matched the label *and* the middle dot, so the text after the
    match began at the title: every long-form reference in the book rendered as
    ``ch01What one number hides``. It survived because the check was a renumbering round-trip
    over the *source*, which a different code path fixes, and because the pages looked at
    afterwards were chapters, whose own heading does not go through here. A part page would have
    shown it immediately.
    """
    assert renderer()._relabel({"identifier": anchor}, written) == expected


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
    build.PDF.PAGES = {
        Path(build.href_for(s)).stem: build.href_for(s) for s in build.PDF.page_order()
    }
    assert build.PDF._published(url) == expected


def test_the_foot_of_a_page_points_at_its_neighbours_in_the_reading_order():
    """prev and next come from page_order(), and the ends of the book have one link, not two."""
    build = site()
    order = [s for s in build.PDF.page_order() if s in build.PDF.parsed_pages()]
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
        name = "storage_cluster" if stage.is_the_finished_model else stage.name
        chapter = (ROOT / "chapters" / f"{stage.chapter}.md").read_text()
        wanted = f"{{iframe}} /models/{name}-reference.html"
        assert wanted in chapter, (
            f"chapters/{stage.chapter}.md does not embed its stage's viewer. Add a "
            f"```{wanted}``` panel where the chapter shows what the stage adds."
        )


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
    # The call itself: in the two page templates, and in the viewer's own app.
    for caller in ("scripts/build-site.py", "scripts/build-playground.py", "sizing/viewer/app.js"):
        assert "bootToolkit(" in (ROOT / caller).read_text(), f"{caller} does not call bootToolkit"


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
    (site / "sizing-and-tco.html").write_text("<html/>")  # the PDF's intermediate: not kept

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
        if page.name == "sizing-and-tco.html":
            continue
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
