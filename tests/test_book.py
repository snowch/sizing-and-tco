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
from bench.outline import (
    APPENDICES,
    CHAPTER_SHAPE,
    CHAPTERS,
    PART_PAGES,
    Appendix,
    Chapter,
)
from bench.stamp import ROOT, result_exists

MYST = yaml.safe_load((ROOT / "myst.yml").read_text())
PAGES = [
    ROOT / "index.md",
    *sorted((ROOT / "parts").glob("*.md")),
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
    grouped = [entry for entry in MYST["project"]["toc"] if entry.get("children")]
    assert [entry.get("file") for entry in grouped[: len(PART_PAGES)]] == [
        part.path for part in PART_PAGES
    ], "a part group in myst.yml is not the part page bench/outline.py names"
    assert [entry.get("title") for entry in grouped[len(PART_PAGES) :]] == ["Appendices"]


@pytest.mark.parametrize("part", PART_PAGES, ids=lambda p: p.slug)
def test_every_part_page_introduces_its_own_chapters(part):
    """A part page that does not mention a chapter in it is a transition nobody wrote.

    The point of these pages is to make the seams explicit, and a seam is explicit when the page
    in front of it says what each chapter behind it is for.
    """
    body = (ROOT / part.path).read_text()
    assert f"(#{part.anchor})=" in body or f"({part.anchor})=" in body, (
        f"{part.path} does not declare the anchor {part.anchor!r}"
    )
    for chapter in [c for c in CHAPTERS if c.part == part.title]:
        assert f"(#{chapter.anchor})" in body, (
            f"{part.path} never mentions {chapter.label}, which is one of its chapters"
        )


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


#: A link to a chapter, as a page writes it: ``[ch13](#monte-carlo)`` or
#: ``[ch13 · Monte Carlo](#monte-carlo)``.
CHAPTER_LINK = re.compile(r"\[(ch\d+)([^\]]*)\]\(#([a-z-]+)\)")

#: What separates a chapter's number from its title, here and in every chapter's own heading.
TITLED = " · "


#: "problem 3.2", however the line happens to wrap.
PROBLEM_REFERENCE = re.compile(r"[Pp]roblems?\s+(\d+)\.(\d+)")

#: A problem as its chapter declares it: "**3.2 — Take a constant...**"
PROBLEM_DECLARED = re.compile(r"^\*\*(\d+\.\d+) \u2014", re.M)

#: A problem with no oracle, which says so in its first sentence: "**3.3 — ...** No test: ..."
PROBLEM_UNGRADED = re.compile(r"^\*\*(\d+\.\d+) \u2014 [^\n]*?\*\* No test\b", re.M)


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda c: c.slug)
def test_a_problem_is_numbered_for_its_own_chapter(chapter: Chapter):
    """A problem number is its chapter's number and a position, and both are derived.

    The same rule as ``Chapter.label``, one level down, and it was the last typed number left in
    the book. Inserting ch01 moved fifty-two of these, which is fine when a script does it and a
    check says whether it worked; the failure that is worth preventing is the quiet one, where a
    chapter moves and its problems keep the old number while still reading plausibly.

    ``python3 scripts/relabel-references.py`` fixes what this reports.
    """
    if not is_written(ROOT / chapter.path):
        pytest.skip("a stub has no problems yet")
    declared = PROBLEM_DECLARED.findall((ROOT / chapter.path).read_text())
    expected = [f"{chapter.number}.{position}" for position in range(1, len(declared) + 1)]
    assert declared == expected, (
        f"{chapter.path} declares problems {declared}. They belong to {chapter.label}, so they "
        f"are {expected} — the chapter's own number, and their position in it, with no gaps."
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda c: c.slug)
def test_a_chapter_ends_on_a_problem_about_the_reader_s_own_system(chapter: Chapter):
    """The one problem in each chapter that this repository cannot mark.

    Invariant 5 used to require every problem to be a test, which meant every problem had to be
    about a model this repository owns: of fifty-two, one mentioned a system the reader runs. The
    rule now allows a problem with no oracle, and this is what holds it — not that a chapter has
    problems, which the test above covers, but that it has the kind whose answer is the reader's
    judgement rather than arithmetic on the book's own numbers.

    It is the last one because that is where it is useful: after the chapter has been worked
    through on a model somebody else built, and while the method is still in the reader's hands.
    """
    if not is_written(ROOT / chapter.path):
        pytest.skip("a stub has no problems yet")
    body = (ROOT / chapter.path).read_text()
    declared = PROBLEM_DECLARED.findall(body)
    ungraded = PROBLEM_UNGRADED.findall(body)
    assert ungraded, (
        f"{chapter.path} has no problem about a system the reader runs. Every chapter owes one: "
        "take the limit its 'What this cannot tell you' names, and ask the reader for the thing "
        "only they have. Write it as '**N.M \u2014 Title.** No test: <why there is no oracle>'."
    )
    assert declared[-1] == ungraded[-1], (
        f"{chapter.path}'s last problem is {declared[-1]}, and its last ungraded one is "
        f"{ungraded[-1]}. The ungraded problem goes last, after the chapter has been worked "
        "through on a model somebody else built."
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda c: c.slug)
def test_a_problem_reference_points_at_a_problem_that_exists(chapter: Chapter):
    """A problem number is a chapter number and a position, and chapters move.

    Both halves of this failed. Renumbering left ch02 pointing at "problem 2.2", which exists and
    is about something else entirely, and ch09 pointing at "problem 9.3", which never existed at
    all. Neither is visible from the chapter doing the pointing.

    A bare reference means this chapter's own problem: that is what thirty-five of the book's
    thirty-eight do. The exception is a reference that names the owning chapter in the same
    breath — "ch03's discipline and problem 2.2's arithmetic" — which reads correctly and is
    allowed, because the link beside it is what a reader follows.
    """
    declared = {
        c.label: set(PROBLEM_DECLARED.findall((ROOT / c.path).read_text())) for c in CHAPTERS
    }
    flat = " ".join((ROOT / chapter.path).read_text().split())
    for match in PROBLEM_REFERENCE.finditer(flat):
        number = f"{match.group(1)}.{match.group(2)}"
        owner = f"ch{int(match.group(1)):02d}"
        assert number in declared.get(owner, set()), (
            f"{chapter.path} points at problem {number}, which no chapter declares. "
            f"{owner} has {sorted(declared.get(owner, set())) or 'no problems'}."
        )
        if owner != chapter.label:
            near = flat[max(0, match.start() - 200) : match.start()]
            other = next(c for c in CHAPTERS if c.label == owner)
            assert f"(#{other.anchor})" in near, (
                f"{chapter.path} says 'problem {number}' without naming {owner}, so a reader "
                f"takes it for one of {chapter.label}'s own. Either it meant "
                f"{chapter.label}.{match.group(2)}, or it should link {owner} beside it."
            )


#: A repository path as a page writes it: backticked, with a slash and an extension this book
#: actually uses. Deliberately narrow — `USD/TB/month` is a unit, not a file.
QUOTED_PATH = re.compile(r"`([A-Za-z0-9_./-]+\.(?:py|js|yaml|yml|json|md|sh|toml|txt|css))`")


@pytest.mark.parametrize("path", WRITTEN, ids=lambda p: p.name)
def test_a_page_does_not_name_a_file_that_is_not_there(path):
    """A page telling a reader to go and look at something that is not there.

    The one item from AUTHORING_GUIDE's "What no check can catch" that turned out to be
    checkable. The rest of that list needs a reader; this one only needs the filesystem, and it
    fails the day a script is renamed rather than the day somebody follows the path.
    """
    for named in QUOTED_PATH.findall(path.read_text()):
        assert (ROOT / named).exists() or list(ROOT.glob(f"**/{named}")), (
            f"{path.name} sends a reader to {named!r}, which does not exist. Rename the "
            "reference, or write the file."
        )


@pytest.mark.parametrize("path", WRITTEN, ids=lambda p: p.name)
def test_a_chapter_reference_names_the_chapter_the_outline_names(path):
    """A reference that carries a title has to carry the right one.

    Both forms are deliberate. Inside a sentence a bare number is enough, because the sentence
    says what the chapter is about. Where the reference stands alone — a prerequisites row, the
    opening of a paragraph on a part page — it carries the title too, because there is no prose
    to carry it and ``ch14`` on its own tells a reader where to click and nothing else.

    Either way the text is derived from ``bench/outline.py``, and neither the number nor the
    title is the chapter's identity, so both move without warning. This is the check that makes
    them move everywhere at once instead of going stale in a table cell nobody rereads.
    """
    by_anchor = {c.anchor: c for c in CHAPTERS}
    for label, rest, target in CHAPTER_LINK.findall(path.read_text()):
        chapter = by_anchor.get(target)
        assert chapter is not None, (
            f"{path.name} links to #{target} as a chapter, and the outline has no such chapter"
        )
        assert label == chapter.label, (
            f"{path.name} calls #{target} {label!r}; the outline makes it {chapter.label!r}"
        )
        assert rest in ("", TITLED + chapter.title), (
            f"{path.name} links to #{target} as {label + rest!r}. A chapter reference is either "
            f"{chapter.label!r} or {chapter.label + TITLED + chapter.title!r} — nothing "
            "else, so that a renamed chapter cannot leave a stale title behind."
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
def test_a_written_chapter_has_the_shape_the_outline_declares(path):
    """Every chapter, the same five headings, in the same order.

    The repetition is what makes the book read as one book, so the shape is a contract rather
    than a default. It is checked here because it was written down in three places that
    disagreed — PLAN.md said six parts, the chapter command said seven, the generator made five —
    which is what happens to a convention nothing enforces.
    """
    if path.parent.name != "chapters":
        pytest.skip("parts and appendices have their own shapes")
    found = tuple(re.findall(r"^## (.+)$", path.read_text(), re.M))
    assert found == CHAPTER_SHAPE, (
        f"{path.name} has sections {found}, and a chapter has {CHAPTER_SHAPE}. "
        "A section a chapter needs and the shape does not have is a subsection of The material."
    )


@pytest.mark.parametrize("path", WRITTEN, ids=lambda p: p.name)
def test_a_written_chapter_says_what_it_cannot_tell_you(path):
    """The mandatory section, and the one that makes the other six believable."""
    if path.parent.name != "chapters":
        pytest.skip("parts and appendices are not chapters")
    assert "## What this cannot tell you" in path.read_text(), (
        f"{path.name} has no 'What this cannot tell you'. A chapter is not finished without it; "
        "if it genuinely has no limits worth naming, look harder at the model."
    )


@pytest.mark.parametrize("path", WRITTEN, ids=lambda p: p.name)
def test_a_written_chapter_has_problems_that_are_tests(path):
    if path.parent.name != "chapters":
        pytest.skip("only chapters carry problems")
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
    """A finished page shows figures, and figures come from the build.

    The introduction is not held to this. It states no numbers -- its first figure is ch01's --
    and the one fragment it used to include was the commit line, which is in Appendix H now,
    beside the instructions for checking a figure against the repository.
    """
    body = path.read_text()
    if path.parent.name in ("chapters", "appendices"):
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


def test_a_chapter_states_the_distinction_the_book_is_built_on():
    """And the front matter does not, which is the change this replaced.

    The distinction used to be stated in the introduction, because that is what PLAN.md said and
    PLAN.md said it because the book this repository was bootstrapped from put its definitions
    there. The result was that the idea seven chapters depend on was taught in a preface, with no
    problems, nothing the reader could run, and no *What this cannot tell you* — front matter
    cannot have those. It is a chapter now, and a chapter is where an argument goes.
    """
    body = (ROOT / "chapters" / "point_estimates.md").read_text().lower()
    for required in ("deterministic structure", "measured constants", "ceiling"):
        assert required in body, (
            f"ch01 must explain the cost-model / sizing-model distinction; {required!r} is missing"
        )
    preface = (ROOT / "index.md").read_text().lower()
    assert "deterministic structure" not in preface, (
        "the introduction is explaining the distinction again. It points at the chapter that "
        "teaches it; saying it twice is how the two versions start to disagree."
    )


def test_dollar_maths_stays_off_while_the_book_prints_money():
    """Two dollar signs on one line are a LaTeX span, and this book puts money in tables.

    ``$318,062 to $611,522`` parses as inline maths with dollar-maths on, and KaTeX sets the
    "to" as a pair of variables. It went unnoticed because nothing warns: the HTML is valid, the
    build is clean, and the only symptom is a number that has quietly become an equation.
    """
    parser = MYST["project"].get("settings", {}).get("parser", {})
    assert parser.get("dollarmath") is False, (
        "myst.yml must set project.settings.parser.dollarmath: false — note the nesting, which "
        "is easy to get wrong and which MyST answers with a warning rather than an error. "
        "ci-check.sh checks the symptom rather than this key, because the key being present is "
        "not the same as the key being read."
    )
    money = [
        (path.name, line)
        for path in (ROOT / "chapters" / "_generated").glob("*.md")
        for line in path.read_text().splitlines()
        if line.count("$") > 1
    ]
    assert money, (
        "no generated fragment prints two dollar signs on a line any more. If the book has "
        "stopped writing money that way, this rule and the setting it guards can go."
    )


def test_every_model_run_shares_one_sample_count_and_seed():
    """Appendix H states them once and the tables no longer carry them.

    That is only honest while they never vary. Before, every figure printed ``100,000 samples ·
    seed 20260916`` — the same words on ninety tables, which is how a constant disguises itself
    as information. Appendix H now says it once and points at this test.

    It said it on page one until a reader pointed out that a seed is of no use to somebody
    reading a table: it is a detail for whoever re-runs the book, and they are in Appendix H.

    If a run ever needs a different sample count or seed, this fails, and the choice is to put
    them back under the figures that differ or to name the exceptions where the setting is
    stated.
    """
    import json

    settings = {}
    for path in sorted((ROOT / "bench" / "results").glob("*.json")):
        produced = json.loads(path.read_text()).get("produced_by", {})
        for field in ("samples", "seed"):
            if produced.get(field) is not None:
                settings.setdefault(field, {}).setdefault(produced[field], []).append(path.stem)

    for field, values in settings.items():
        assert len(values) == 1, (
            f"results disagree about {field!r}: "
            + "; ".join(f"{value} in {sorted(names)}" for value, names in values.items())
            + f". index.md states one {field} for the whole book and no figure prints it, so a "
            "second value is published nowhere a reader could find it."
        )


#: Product names, for the rule CLAUDE.md calls absolute. Necessarily a list rather than a
#: principle — no check can recognise a product it has not been told about — so it is the common
#: ones, and it is worth extending when a new one nearly gets in.
PRODUCTS = (
    "aws",
    "amazon",
    "azure",
    "google cloud",
    "gcp",
    "kubernetes",
    "prometheus",
    "grafana",
    "elasticsearch",
    "kafka",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
    "ceph",
    "minio",
    "datadog",
    "splunk",
    "nvidia",
    "intel",
    "amd",
    "dell",
    "seagate",
    "western digital",
    "cloudflare",
    "snowflake",
    "databricks",
    "clickhouse",
    "influxdb",
    "jaeger",
    "opentelemetry",
    "hadoop",
    "spark",
    "terraform",
    "openstack",
    "vmware",
)


@pytest.mark.parametrize("path", WRITTEN, ids=lambda p: p.name)
def test_no_product_is_named(path):
    """Vendor neutrality, which CLAUDE.md calls absolute and nothing was checking.

    The introduction tells a reader "no vendor is named anywhere in this book", and that was
    true — but true because everybody had remembered, which is the kind of true this repository
    does not accept anywhere else. A measured constant may name the *implementation* it belongs
    to, because that is what makes it a measurement; a chapter may not name a product.
    """
    body = re.sub(r"`[^`]*`", " ", path.read_text().lower())  # code spans are not prose
    named = sorted({p for p in PRODUCTS if re.search(rf"\b{re.escape(p)}\b", body)})
    assert not named, (
        f"{path.name} names {named}. CLAUDE.md §4: no product is named in any chapter, model or "
        "figure. Describe what it does instead, or name the implementation a measurement "
        "belongs to."
    )
