"""A model viewer embedded in a chapter says nothing the chapter has not taught yet.

tests/test_vocabulary.py holds the chapters' own text to the ration. The viewer a chapter embeds
was outside it, and so for most of the book it told a reader about samples, seeds, distributions
and intervals from ch02 on. What a viewer shows comes from four places, and each is checked here
without a browser, because CI has none:

- ``sizing/viewer/words.json``: the words that change with the chapter. The plain set is what a
  chapter before sampling gets, through the flag ``scripts/build-site.py`` puts in the address.
- ``sizing/viewer/app.js``: every other string the page writes, which may use none of the six.
- the page template in ``scripts/build-viewers.py``: its text may use them only inside an element
  the viewer removes before then.
- the model itself: labels, notes and provenance, shown in the panel beside the graph.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from importlib import util
from pathlib import Path

import pytest

from bench.outline import CHAPTERS
from tests.test_vocabulary import FORMS, RATIONED, home

ROOT = Path(__file__).resolve().parent.parent
VIEWER = ROOT / "sizing" / "viewer"
WORDS = json.loads((VIEWER / "words.json").read_text())
#: What the removal marks are called in the template, and what app.js removes by.
MARKS = ("data-once-taught", "data-resample")


def _script(name: str, file: str):
    spec = util.spec_from_file_location(name, ROOT / "scripts" / file)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rationed(text: str) -> list[str]:
    return sorted({m.group(0) for form in FORMS.values() for m in form.finditer(text)})


def js_strings(source: str) -> list[str]:
    """The text of every string and template literal in a script, less its ``${...}`` code.

    A small scanner rather than a regular expression, because a template can hold an expression
    that holds another template, and the viewer's do.
    """
    out: list[str] = []

    def code(i: int, closing: str | None) -> int:
        depth = 0
        while i < len(source):
            c, pair = source[i], source[i : i + 2]
            if pair == "//":
                i = source.index("\n", i)
            elif pair == "/*":
                i = source.index("*/", i) + 2
                continue
            elif c in "\"'":
                i = quoted(i, c)
                continue
            elif c == "`":
                i = template(i + 1)
                continue
            elif c == "{":
                depth += 1
            elif c == "}":
                if closing and depth == 0:
                    return i + 1
                depth -= 1
            i += 1
        return i

    def quoted(i: int, quote: str) -> int:
        j = i + 1
        while source[j] != quote:
            j += 2 if source[j] == "\\" else 1
        out.append(source[i + 1 : j])
        return j + 1

    def template(i: int) -> int:
        text = []
        while source[i] != "`":
            if source[i] == "\\":
                text.append(source[i : i + 2])
                i += 2
            elif source.startswith("${", i):
                i = code(i + 2, "}")
                text.append(" ")
            else:
                text.append(source[i])
                i += 1
        out.append("".join(text))
        return i + 1

    code(0, None)
    return out


class _Text(HTMLParser):
    """Each run of text in a page, with whether an element around it carries a removal mark."""

    VOID = {"meta", "link", "br", "input", "img", "hr"}

    def __init__(self):
        super().__init__()
        self.stack: list[tuple[str, bool]] = []
        self.found: list[tuple[str, bool]] = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append((tag, any(name in MARKS for name, _ in attrs)))

    def handle_endtag(self, tag):
        while self.stack and self.stack.pop()[0] != tag:
            pass

    def handle_data(self, data):
        if not any(tag in ("script", "style") for tag, _ in self.stack) and data.strip():
            self.found.append((data, any(marked for _, marked in self.stack)))


def test_the_plain_words_use_none_of_the_six():
    used = {key: rationed(text) for key, text in WORDS["plain"].items() if rationed(text)}
    assert not used, f"the plain words are the ones a chapter before sampling sees: {used}"


def test_the_plain_words_do_not_name_a_scenario_either():
    """Not one of the six, but ch12 is the first chapter to say it, and the plain words serve every
    chapter before sampling. The reset button and a node's value row both said it from ch02 on."""
    named = [key for key, text in WORDS["plain"].items() if "scenario" in text.lower()]
    assert not named, f"say the book's values, not the scenario: {named}"


def test_every_word_has_a_plain_version_unless_only_a_resample_says_it():
    """A key missing from the plain set would throw in a chapter before sampling, or leak."""
    taught, plain = set(WORDS["taught"]), set(WORDS["plain"])
    assert plain <= taught, f"plain words nothing uses: {sorted(plain - taught)}"
    missing = sorted(k for k in taught - plain if not k.startswith("resample_"))
    assert not missing, f"no plain version of {missing}"


def test_the_flag_switches_where_every_word_it_guards_is_taught():
    """The taught words appear from the chapter that teaches "sample"; none may be taught later."""
    order = [c.slug for c in CHAPTERS]
    where = home()
    for text in WORDS["taught"].values():
        for word in rationed(text):
            term = next(t for t in RATIONED if FORMS[t].fullmatch(word))
            assert order.index(where[term]) <= order.index(where["sample"]), (
                f"{word!r} is taught in {where[term]}, after the viewer starts using it"
            )


def test_the_viewer_code_writes_none_of_the_six_itself():
    strings = js_strings((VIEWER / "app.js").read_text())
    assert len(strings) > 50, "the scanner found almost no strings, so it is not reading the file"
    used = [s for s in strings if rationed(s)]
    assert not used, f"words.json is where these belong, so the chapter can choose: {used}"


def test_the_page_says_them_only_where_the_viewer_removes_them():
    page = _Text()
    page.feed(_script("build_viewers", "build-viewers.py").PAGE)
    loose = [text.strip() for text, marked in page.found if rationed(text) and not marked]
    assert not loose, f"mark these {MARKS[0]} or {MARKS[1]}, or say them plainly: {loose}"


def test_a_chapter_before_sampling_asks_its_viewers_for_plain_words():
    site = _script("build_site", "build-site.py")
    order = [c.slug for c in CHAPTERS]
    teaches = order.index(home()["sample"])
    for i, chapter in enumerate(CHAPTERS):
        assert site.before_sampling(chapter.path) == (i < teaches), chapter.label


def _embedded() -> list[tuple[object, str]]:
    return [
        (chapter, name)
        for chapter in CHAPTERS
        for name in sorted(
            set(re.findall(r"/models/([\w-]+)\.html", Path(ROOT / chapter.path).read_text()))
        )
    ]


@pytest.mark.parametrize("chapter,name", _embedded(), ids=lambda v: getattr(v, "label", v))
def test_a_model_embedded_early_says_none_of_them_either(chapter, name):
    """The panel beside the graph shows each node's label, note and provenance, as prose."""
    order = [c.slug for c in CHAPTERS]
    here = order.index(chapter.slug)
    early = {t for t, slug in home().items() if slug in order and here < order.index(slug)}
    nodes = json.loads((ROOT / "bench" / "results" / f"{name}.json").read_text())["summary"][
        "nodes"
    ]
    found = []
    for node, entry in nodes.items():
        shown = [
            entry.get("label"),
            entry.get("note"),
            (entry.get("provenance") or {}).get("source"),
        ]
        for text in filter(None, shown):
            for term in early:
                if FORMS[term].search(text):
                    found.append(f"{node}: {FORMS[term].search(text).group(0)!r}")
    assert not found, f"{chapter.label} shows {name}, whose text says {found}"
