"""Every figure is legible, checked the way a person checks it: by looking at where the text is.

The figures are drawn by arithmetic in :mod:`bench.diagrams`, so a label's position is a function
of the data, and data moves. A percentile that lands near a point estimate, a tail that runs three
decades further than the last one, a model with a longer node name — each of those has printed one
label over another at some point in this repository's short history, and none of them is visible
from a test that only checks the SVG parses.

So this reconstructs each text element's box from its anchor and font size and asks two questions
a reader would ask: does anything overlap, and is anything off the page. The character width is an
approximation, which is why :data:`TOLERANCE` exists — the check is for labels sitting on top of
each other, not for two boxes touching at the corner.
"""

from __future__ import annotations

import html
import re

import pytest

from bench.figures import FIGURES as DECLARED
from bench.stamp import ROOT

FIGURES = sorted((ROOT / "chapters" / "_figures").glob("*.svg"))

TEXT = re.compile(r"<text([^>]*)>(.*?)</text>", re.S)
ATTRIBUTE = re.compile(r'(\S+)="([^"]*)"')
MARKUP = re.compile(r"<[^>]+>")

#: Advance width of one character as a fraction of the font size, for the sans-serif the figures
#: ask for. Deliberately generous: a label that only just clears its neighbour at this width is
#: one data change away from not clearing it.
ADVANCE = 0.52

#: How much two boxes may overlap before it counts. Absorbs the error in :data:`ADVANCE` without
#: absorbing anything a reader would notice.
TOLERANCE = 1.5


def boxes(svg: str) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Every unrotated text element, as (content, left, top, right, bottom).

    Rotated labels are skipped rather than approximated: the two figures that use them put them
    in a lane of their own alongside a line, precisely so they cannot collide with anything.
    """
    out = []
    for match in TEXT.finditer(svg):
        attributes = dict(ATTRIBUTE.findall(match.group(1)))
        if "transform" in attributes:
            continue
        content = html.unescape(MARKUP.sub("", match.group(2)))
        size = float(attributes.get("font-size", 10))
        x, y = float(attributes.get("x", 0)), float(attributes.get("y", 0))
        width = len(content) * size * ADVANCE
        anchor = attributes.get("text-anchor", "start")
        left = x - width if anchor == "end" else x - width / 2 if anchor == "middle" else x
        out.append((content, (left, y - size * 0.78, left + width, y + size * 0.22)))
    return out


def canvas(svg: str) -> tuple[float, float]:
    width = re.search(r'width="(\d+)"', svg)
    height = re.search(r'height="(\d+)"', svg)
    assert width and height, "a figure with no declared size"
    return float(width.group(1)), float(height.group(1))


@pytest.mark.parametrize("path", FIGURES, ids=lambda p: p.name)
def test_no_label_is_printed_over_another(path):
    found = boxes(path.read_text())
    for i, (first, a) in enumerate(found):
        for second, b in found[i + 1 :]:
            horizontal = min(a[2], b[2]) - max(a[0], b[0])
            vertical = min(a[3], b[3]) - max(a[1], b[1])
            assert horizontal <= TOLERANCE or vertical <= TOLERANCE, (
                f"{path.name} prints {first!r} over {second!r}. Two labels landed in the same "
                f"place because the data moved; the figure needs to place them, not hope."
            )


@pytest.mark.parametrize("path", FIGURES, ids=lambda p: p.name)
def test_no_label_falls_off_the_page(path):
    svg = path.read_text()
    width, height = canvas(svg)
    for content, (left, top, right, bottom) in boxes(svg):
        assert left >= -TOLERANCE and right <= width + TOLERANCE, (
            f"{path.name}: {content!r} runs off the side of a {width:.0f}x{height:.0f} canvas. "
            f"Anchor it inwards at the ends rather than centring it on the axis."
        )
        assert top >= -TOLERANCE and bottom <= height + TOLERANCE, (
            f"{path.name}: {content!r} is above or below a {width:.0f}x{height:.0f} canvas."
        )


@pytest.mark.parametrize("path", FIGURES, ids=lambda p: p.name)
def test_no_label_is_truncated(path):
    """A box that was too small for its label is a figure that lost a word, silently."""
    assert "…" not in path.read_text(), (
        f"{path.name} truncates a label. Shorten the label in the model, or give the box room."
    )


# -- a figure's conditions line names what the figure was made from -----------------------------


def test_a_renderer_that_ignores_a_result_is_not_given_one():
    """The bug: a table of unit conversions stamped with a compression benchmark.

    ``conversions_table``, ``glossary_table`` and ``constants_index`` all take ``_name`` and
    ignore it — they are assembled from the model files or from the results directory. Each was
    nonetheless declared with a ``result`` purely to satisfy the machinery, and the conditions
    line under them therefore sent a reader to a file the table had nothing to do with. Nothing
    noticed, because ``verify-numbers.py`` only checks that a named result *exists*.
    """
    import inspect

    from bench.figures import FIGURES, Table

    for name, figure in FIGURES.items():
        if not isinstance(figure, Table):
            continue
        first = next(iter(inspect.signature(figure.render).parameters), None)
        if first and first.startswith("_"):
            assert figure.result is None, (
                f"figure {name!r} is rendered by {figure.render.__name__}, which ignores the "
                f"result it is given — yet it declares result={figure.result!r}. Its conditions "
                "line will name a result the table was not built from. Use computed_from instead."
            )
            assert figure.computed_from, (
                f"figure {name!r} has no result and no computed_from, so its conditions line "
                "cannot say where it came from."
            )


def test_a_table_drawing_on_two_results_names_both():
    """A scenario comparison prints two columns from two runs and must disclose both.

    Five of them named only the first, so half the numbers in each table — including the whole
    point of ch16 — came from a file the footer never mentioned.
    """
    from bench.figures import FIGURES, Table

    for name, figure in FIGURES.items():
        if not isinstance(figure, Table) or figure.render.__name__ != "scenario_comparison":
            continue
        other = figure.args[0] if figure.args else None
        assert other in figure.also, (
            f"figure {name!r} compares against {other!r} and does not list it in `also`, so its "
            "conditions line names one of the two results its columns come from."
        )


def test_every_declared_figure_is_included_somewhere():
    """A figure nobody includes is rendered on every build and read by nobody.

    ``bench/figures.py`` is the only place a figure is declared, and `render-figures.py` writes
    one file per entry whether or not a page asks for it. Nothing noticed when the introduction
    stopped including its table of unmeasured constants, so the declaration stayed and the
    fragment kept being written — which is the quiet half of moving prose around.
    """
    pages = "\n".join(
        path.read_text()
        for pattern in ("chapters/*.md", "appendices/*.md", "parts/*.md", "index.md")
        for path in ROOT.glob(pattern)
    )
    orphaned = sorted(
        name for name in DECLARED if f"{name}.md" not in pages and f"{name}.svg" not in pages
    )
    assert not orphaned, (
        f"declared in bench/figures.py and included by no page: {orphaned}. Either a page should "
        "be using it, or the declaration should go."
    )


def test_the_formula_sheet_lists_every_formula_once():
    """The sheet is a view of the model file: one row per derived node or ceiling, verbatim."""
    from bench import tables
    from bench.stages import model_path
    from sizing.dsl import Ceiling, Derived, load_model

    model = load_model(model_path("web_service"))
    sheet = tables.formulas_table(None, "web_service")
    rows = sheet.splitlines()[2:]
    listed = [n for n, node in model.nodes.items() if isinstance(node, Derived | Ceiling)]
    assert len(rows) == len(listed)
    for name, node in model.nodes.items():
        if isinstance(node, Derived):
            assert f"| `{node.formula_text}` |" in sheet, name
        elif isinstance(node, Ceiling):
            assert f"`{node.of_text}` against a limit of `{node.limit_text}`" in sheet, name
    assert "Introduced in" in sheet.splitlines()[0]
    assert "Introduced in" not in tables.formulas_table(None, "observability")
