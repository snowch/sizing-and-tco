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
