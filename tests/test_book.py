"""The book and the data structure that describes it cannot drift apart.

``bench/outline.py`` says what the book is. ``myst.yml`` says what gets published. The pages on
disk say what a reader sees. Three descriptions of one thing is two opportunities for them to
disagree, and every check here exists because that disagreement is invisible from inside any one
of them.
"""

from __future__ import annotations

import re

import pytest
import yaml

from bench.figures import FIGURES
from bench.outline import APPENDICES, CHAPTERS, PARTS, Appendix, Chapter
from bench.stamp import ROOT, result_exists

MYST = yaml.safe_load((ROOT / "myst.yml").read_text())
PAGES = [
    ROOT / "index.md",
    *sorted((ROOT / "chapters").glob("*.md")),
    *sorted((ROOT / "appendices").glob("*.md")),
]

#: A page still carrying the generator's marker is a stub, and most rules below are about
#: finished prose rather than about a table of contents entry that has not been written yet.
STUB = "[To write"


def toc_files() -> list[str]:
    out = []
    for entry in MYST["project"]["toc"]:
        if "file" in entry:
            out.append(entry["file"])
        for child in entry.get("children", ()):
            out.append(child["file"])
    return out


def is_written(path) -> bool:
    return STUB not in path.read_text()


WRITTEN = [path for path in PAGES if is_written(path)]


# -- the outline, the config and the disk agree ------------------------------------------------


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda c: c.slug)
def test_every_chapter_exists_on_disk(chapter: Chapter):
    assert (ROOT / chapter.path).exists(), (
        f"{chapter.path} is in the outline and not on disk. "
        f"`python3 scripts/new-chapter.py {chapter.slug}`"
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda c: c.slug)
def test_every_chapter_is_published(chapter: Chapter):
    assert chapter.path in toc_files(), f"{chapter.path} is not in myst.yml's table of contents"


@pytest.mark.parametrize("appendix", APPENDICES, ids=lambda a: a.slug)
def test_every_appendix_exists_and_is_published(appendix: Appendix):
    assert (ROOT / appendix.path).exists()
    assert appendix.path in toc_files()


def test_every_published_page_is_checked_for_typed_numbers():
    """The rule that caught the template's preface: a page outside the check is a page exempt.

    ``scripts/verify-numbers.py`` scans a list it builds itself. This asserts that list is the
    same set of pages the site publishes, so a page cannot be added to the book and quietly left
    outside the rule.
    """
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from importlib import util

    spec = util.spec_from_file_location("vn", ROOT / "scripts" / "verify-numbers.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scanned = {path.relative_to(ROOT).as_posix() for path in module.published_pages()}
    assert scanned == set(toc_files()), (
        f"pages published but not scanned: {sorted(set(toc_files()) - scanned)}; "
        f"scanned but not published: {sorted(scanned - set(toc_files()))}"
    )


def test_the_parts_in_the_toc_are_the_parts_in_the_outline():
    titles = [entry["title"] for entry in MYST["project"]["toc"] if "title" in entry]
    assert titles == [*PARTS, "Appendices"]


# -- identity is the slug, the number is derived --------------------------------------------------


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda c: c.slug)
def test_no_identifier_carries_the_chapter_number(chapter: Chapter):
    """A number is a statement about position, and positions move.

    The template this book is built on moved a chapter three times, and each move renamed every
    anchor, file, test directory and permalink downstream of it. Identity is the slug.
    """
    for identifier in (chapter.slug, chapter.anchor, chapter.path, chapter.tests_dir):
        assert not re.search(r"\d", identifier), (
            f"{identifier!r} contains a number. A chapter's number is derived (Chapter.label), "
            "never typed into a name."
        )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda c: c.slug)
def test_a_chapter_declares_its_own_label(chapter: Chapter):
    body = (ROOT / chapter.path).read_text()
    assert f"({chapter.anchor})=" in body, f"{chapter.path} has no MyST label"
    assert f"# {chapter.label} · " in body, (
        f"{chapter.path}'s heading does not start with {chapter.label}. Numbers in headings are "
        "derived from the outline; regenerate the stub or fix the heading."
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda c: c.slug)
def test_a_prerequisite_comes_earlier(chapter: Chapter):
    for needed in chapter.needs:
        other = next(c for c in CHAPTERS if c.slug == needed)
        assert other.number < chapter.number, (
            f"{chapter.label} needs {other.label}, which comes after it"
        )


# -- what a page claims to be built from must exist --------------------------------------------


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda c: c.slug)
def test_what_a_chapter_consumes_exists(chapter: Chapter):
    for source in chapter.consumes:
        if source.endswith((".yaml", ".yml")):
            assert (ROOT / source).exists(), f"{chapter.label} names a model file that is missing"
        else:
            assert result_exists(source), (
                f"{chapter.label} says it is built from {source!r}, and "
                f"bench/results/{source}.json does not exist"
            )


def test_every_figure_belongs_to_a_page_by_name():
    """A figure id is an identifier too, and drifts the same way a chapter number does."""
    prefixes = {c.anchor for c in CHAPTERS} | {a.anchor for a in APPENDICES} | {"preface"}
    for name in FIGURES:
        assert any(name.startswith(prefix) for prefix in prefixes), (
            f"figure {name!r} is not named after a chapter or appendix. Name it for the page it "
            "belongs to, so a renamed page cannot leave an orphan behind."
        )


# -- house rules about finished prose ------------------------------------------------------------


@pytest.mark.parametrize("path", WRITTEN, ids=lambda p: p.name)
def test_a_written_chapter_says_what_it_cannot_tell_you(path):
    """The mandatory section, and the one that makes the other six believable."""
    if path.parent.name != "chapters":
        pytest.skip("appendices are reference material, not chapters")
    assert "## What this cannot tell you" in path.read_text(), (
        f"{path.name} has no 'What this cannot tell you'. A chapter is not finished without it; "
        "if it genuinely has no limits worth naming, look harder at the model."
    )


@pytest.mark.parametrize("path", WRITTEN, ids=lambda p: p.name)
def test_a_written_chapter_has_problems_that_are_tests(path):
    if path.parent.name != "chapters":
        pytest.skip("appendices carry no problems")
    body = path.read_text()
    assert "## Problems" in body
    slug = path.stem
    assert f"tests/{slug}/" in body, (
        f"{path.name}'s problems must live in tests/{slug}/ and the chapter must say so"
    )
    assert (ROOT / "tests" / slug).is_dir(), f"tests/{slug}/ does not exist"


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_no_literalinclude_uses_line_numbers(path):
    """Line numbers rot on the first edit above them. Anchor on text."""
    assert ":lines:" not in path.read_text(), (
        f"{path.name} quotes code by line number. Use :start-at: and :end-before: with text "
        "anchors, which survive an edit."
    )


#: One ``{literalinclude}``: the file it quotes, and the text anchors it quotes it between.
QUOTE = re.compile(
    r"```\{literalinclude\}\s*(?P<target>\S+)\n(?P<options>(?::[a-z-]+:.*\n)*)", re.MULTILINE
)


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_every_quoted_anchor_still_matches(path):
    """A text anchor that no longer matches quotes the wrong span, silently.

    Which is the failure mode :func:`test_no_literalinclude_uses_line_numbers` was avoiding in
    the first place: anchoring on text survives an edit *above* it, and does not survive the
    quoted function being renamed. This is the check that notices.
    """
    for quote in QUOTE.finditer(path.read_text()):
        target = (path.parent / quote["target"]).resolve()
        assert target.exists(), f"{path.name} quotes {quote['target']}, which does not exist"
        body = target.read_text()
        for option, anchor in re.findall(
            r":(start-at|start-after|end-before):\s*(.+)", quote["options"]
        ):
            assert anchor.strip() in body, (
                f"{path.name} quotes {quote['target']} :{option}: {anchor.strip()!r}, which is "
                f"no longer in that file. The quote is now of something else."
            )


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_every_directive_is_closed(path):
    """A build that succeeds is not the same as a page that says what it was written to say."""
    body = path.read_text()
    assert body.count("```") % 2 == 0, f"{path.name} has an unclosed fenced block"
    assert body.count(":::") % 2 == 0, f"{path.name} has an unclosed colon-fenced directive"


@pytest.mark.parametrize("path", WRITTEN, ids=lambda p: p.name)
def test_a_written_page_includes_generated_fragments_rather_than_numbers(path):
    """A finished page shows figures, and figures come from the build."""
    body = path.read_text()
    if path.name == "index.md" or path.parent.name in ("chapters", "appendices"):
        assert "_generated/" in body or "_figures/" in body, (
            f"{path.name} is written but includes no generated figure. Every number in this book "
            "comes from a stamped result."
        )


@pytest.mark.parametrize("path", WRITTEN, ids=lambda p: p.name)
def test_a_written_page_uses_no_marketing_tone(path):
    """A small, literal check on the house voice, for the phrases that creep back in."""
    body = path.read_text().lower()
    for phrase in ("in this chapter we will", "as we all know", "simply put", "best-in-class"):
        assert phrase not in body, f"{path.name} contains {phrase!r}"


def test_the_preface_states_the_distinction_the_book_is_built_on():
    body = (ROOT / "index.md").read_text()
    for required in ("deterministic structure", "measured constants", "ceiling"):
        assert required.lower() in body.lower(), (
            f"the front matter must explain the cost-model / sizing-model distinction; "
            f"{required!r} is missing"
        )
