"""The six statistical words, and the chapter each is allowed to start in.

The introduction promises, in bold, that the reader is assumed to know **nothing** about
statistics, and then names the six words the book will teach and says each is used in plain
English first and named second, in the chapter where a model first needs it. That promise had
nothing keeping it: the words were rationed in CLAUDE.md, their home chapters were recorded in
the glossary, and no two of those three ever met.

So they leaked. ch01 said "sampling" in the sentence separating the two kinds of model
-- a page whose own introduction claims it names none of the six -- and five more chapters used
a word before the chapter that teaches it.

The same shape as the numbers rule, and the same escape hatch: `% word-ok: <reason>` on the line
before, where a reviewer sees the reason rather than a silent exception buried in a list here.
Several of the hits are honest: a scrape interval is a length of time, bytes per sample is a unit
of data, and a sample of your own records is a handful of records. Those are the sentences the
comment is for.
"""

from __future__ import annotations

import re

import pytest

from bench.outline import APPENDICES, CHAPTERS
from bench.stamp import ROOT, shown
from bench.tables import GLOSSARY

#: The six, and nothing else. CLAUDE.md names them; the glossary says where each one lives.
RATIONED = ("distribution", "sample", "percentile", "interval", "correlation", "convergence")

#: `% word-ok: <reason>` on the line before, like `% number-ok:` for a figure.
EXEMPTION = re.compile(r"^%\s*word-ok:\s*\S+")

#: Any form of the word, which means the stem rather than the word: the first version of this
#: matched `sample\w*` and so missed "sampling", which is the one use in ch01 that started all
#: of this.
STEMS = {
    "distribution": "distribut",
    "sample": "sampl",
    "percentile": "percentile",
    "interval": "interval",
    "correlation": "correlat",
    "convergence": "converg",
}
FORMS = {term: re.compile(rf"\b{stem}\w*", re.I) for term, stem in STEMS.items()}


def home() -> dict[str, str]:
    """Which chapter teaches each word, read from the glossary rather than restated."""
    missing = [term for term in RATIONED if term not in GLOSSARY]
    assert not missing, f"the glossary has no entry for {missing}, so nothing says where it lives"
    return {term: GLOSSARY[term][0] for term in RATIONED}


def reading_order() -> list:
    """Every page a reader passes through, in the order they pass through it."""
    return [
        ROOT / "index.md",
        *[ROOT / c.path for c in CHAPTERS],
        *[ROOT / a.path for a in APPENDICES],
    ]


def position() -> dict[str, int]:
    """Where each page sits in the reading order, by slug."""
    return {path.stem: i for i, path in enumerate(reading_order())}


def exempted(path, number: int) -> bool:
    """Whether `% word-ok:` covers this line.

    It covers the block it introduces, up to the next blank line, rather than only the line after
    it. The introduction's list of the six is six bullets, and six copies of the same comment
    above them would be worse than the thing the comment is for.
    """
    lines = path.read_text().splitlines()
    for above in range(number - 2, -1, -1):
        stripped = lines[above].strip()
        if not stripped:
            return False
        if EXEMPTION.match(stripped):
            return True
    return False


def prose_lines(path):
    """Every line of a page that is prose, with its number.

    Fenced code, tables, directive options and the book's own generated captions are not prose,
    and a link slug like `#correlation-and-convergence` is a target rather than a word.
    """
    fenced = False
    for n, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
            continue
        if fenced or stripped.startswith(("|", ":", "%", "<!--", "---", "*Source")):
            continue
        yield n, re.sub(r"\(#[^)]*\)|`[^`]*`", " ", line)


@pytest.mark.parametrize("term", RATIONED)
def test_a_rationed_word_waits_for_the_chapter_that_teaches_it(term):
    """No page uses one of the six before the chapter the glossary gives it.

    The introduction's promise is the specification: plain English first, the word second, in the
    chapter where a model first needs it. A word arriving earlier lands on a reader who was told
    they would not need to know it yet.
    """
    where, order = home(), position()
    lives_at = order.get(where[term])
    assert lives_at is not None, (
        f"{term} lives in {where[term]!r}, which is not in the reading order"
    )

    early = []
    for path in reading_order():
        if order[path.stem] >= lives_at:
            continue
        for n, line in prose_lines(path):
            if exempted(path, n):
                continue
            for hit in FORMS[term].findall(line):
                early.append(f"{shown(path)}:{n} says {hit!r}")
    assert not early, (
        f"{term!r} is taught in {where[term]}, and these come earlier:\n  "
        + "\n  ".join(early)
        + "\nSay the plain thing instead, or, where this is a different sense of the word "
        "— a scrape interval, bytes per sample — put `% word-ok: <reason>` on the line before."
    )
