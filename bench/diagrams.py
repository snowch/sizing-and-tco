"""Figures, drawn as SVG by code, deterministically.

Not a plotting library, for the reason *Systems From Scratch* gives and this book inherits: a
plot whose bytes change when the renderer is upgraded cannot be put under a staleness check, and
a check people learn to ignore is worse than no check. Everything here is arithmetic and string
formatting, so ``render-figures.py --check`` can diff a committed figure against a fresh one and
the difference always means something.

Every figure must show a mechanism. A picture of this book's dependency graph is not decoration:
the shape of the graph *is* the argument — which quantities are guesses, how far a guess is from
the answer, and where the chain stops being a chain and meets a ceiling.

Colours are carried by kind and by provenance, and they mean the same thing in every figure and
in the interactive page. They are also readable in greyscale: the marks ``●``, ``◐``, ``○`` say
the same thing as the fills, because a page gets printed and a printer may not have the colours.
"""

from __future__ import annotations

import html
import math

from bench.stamp import load_result
from bench.tables import fmt, signed_money, unit_label

#: Node kinds, by fill. The distinction the whole book rests on is visible here: a model with no
#: amber and no red in it is a definitional model, and one with either is a conditional model.
KIND_FILL = {
    "input": "#dbe7f3",
    "derived": "#eceff1",
    "measured": "#fde8c8",
    "ceiling": "#f8d3d0",
}
KIND_STROKE = {
    "input": "#4a7ba7",
    "derived": "#90a4ae",
    "measured": "#c8791a",
    "ceiling": "#b3413a",
}
PROVENANCE_STROKE = {"fact": "#2e7d32", "vendor_claim": "#c8791a", "assumption": "#b3413a"}

#: What each of those colours becomes when the page is dark, and the whole reason the figures can
#: follow it at all: they are drawn inline, so the page's stylesheet reaches every fill and stroke
#: in them. `scripts/build-site.py` turns this into one rule per colour, inside the dark block.
#:
#: A figure is drawn once, in daylight, and read in both. Substituting colour by colour rather
#: than inverting keeps what the colour means -- amber is a measured constant, red a ceiling, and
#: a ceiling that inverted to cyan would say nothing. `tests/test_figures.py` fails a figure that
#: uses a colour this does not name, so a new one cannot quietly ship a white slab.
DARK_FIGURE = {
    # Paper and the panels drawn on it.
    "#ffffff": "#151c20",
    "#fafafa": "#1b2429",
    "#eceff1": "#232d33",
    "#e4e7e9": "#232d33",
    "#e0e0e0": "#2b363c",
    "#cfd8dc": "#2b363c",
    "#bdbdbd": "#3d4b53",
    # Ink, from the darkest label to the faintest rule.
    "#263238": "#dde4e8",
    "#37474f": "#c9d4da",
    "#455a64": "#b3c1c9",
    "#546e7a": "#9db0ba",
    "#607d8b": "#8ea3ae",
    "#78909c": "#7f939e",
    "#90a4ae": "#6c828d",
    # An input, and the blue the book draws data in.
    "#dbe7f3": "#22384a",
    "#dde5ec": "#22384a",
    "#9fc0dd": "#4a7ba7",
    "#5b8fb9": "#5b8fb9",
    "#4a7ba7": "#7fb0d8",
    # A measured constant, a ceiling, a fact, and the second series in a comparison.
    "#fde8c8": "#3a2c15",
    "#c8791a": "#d9922c",
    "#f8d3d0": "#3a1f1d",
    "#b3413a": "#cf5a52",
    "#2e7d32": "#4f9c53",
    "#c98a6b": "#c98a6b",
}
PROVENANCE_DASH = {"fact": "", "vendor_claim": "4 2", "assumption": "2 3"}

COLUMN_WIDTH = 188
ROW_HEIGHT = 46
BOX_WIDTH = 154
BOX_HEIGHT = 32
MARGIN = 16

#: The smallest text any figure prints, in the figure's own units. A figure is inlined at its
#: natural width wherever the column has room, so this is the size a reader sees on a tablet or
#: a desktop; the review flags anything that renders under nine pixels, and ten leaves a figure
#: room to be squeezed by a tenth before it does. Narrower than that, the page gives the figure
#: an Expand control that shows it at this size (`scripts/build-site.py`).
#: `tests/test_figures.py` fails any committed figure with smaller text.
TEXT = 10

#: An edge's head, drawn as a triangle rather than an SVG marker: a marker needs an id, and
#: every figure on a page is inlined into one document, where ids must not repeat.
ARROW_LENGTH = 6.0
ARROW_HALF_WIDTH = 3.0
#: The bar on an input somebody chose. One colour for every box, whatever its border says.
DECIDED_BAR = "#455a64"
#: A measured constant with no measurement: the box is left empty.
UNMEASURED_FILL = "#ffffff"
#: The lead-in to the legend's second line, which says what an input's border means.
LEGEND_BORDERS = "an input's border says where it came from:"
LEGEND_LINE = 16

#: The dependency graph drawn narrow enough to read on a phone, for a model of a few columns.
#: The usual layout is 596 units wide for three columns, and a screen 320 pixels wide draws its
#: text under five pixels high. This one keeps the text at :data:`TEXT` and pays for it in
#: lines: a label wraps onto three.
COMPACT = {"margin": 4, "column": 110, "box_width": 84, "box_height": 44, "row": 52, "wrap": 13}
COMPACT_LINES = 3


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _svg(width: float, height: float, body: str, title: str) -> str:
    """One figure, sized to its content, with a title element for a screen reader."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" font-family="system-ui, sans-serif">'
        f"<title>{_esc(title)}</title>"
        f'<rect width="{width:.0f}" height="{height:.0f}" fill="#ffffff"/>'
        f"{body}</svg>\n"
    )


def _wrap(text: str, width: int = 26, most: int = 2) -> list[str]:
    """Break a label into at most ``most`` lines, because a box is a box."""
    words, lines, current = str(text).split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
        if len(lines) == most:
            break
    if current and len(lines) < most:
        lines.append(current)
    if len(lines) == most and len(words) > len(" ".join(lines).split()):
        lines[-1] = lines[-1][: width - 1] + "…"
    return [line for line in lines if line]


# -- the dependency graph -------------------------------------------------------------------


def dependency_graph(
    result: str, focus: str | None = None, only_focus: bool = False, compact: bool = False
) -> str:
    """The model as a graph, coloured by node kind, arrows pointing from cause to effect.

    With ``focus``, everything that does not feed that output is faded: the sub-graph that
    produced one number, which on a fifty-node model is the difference between a picture and a
    diagram. The interactive version does the same thing on a click; this is the printable one.

    With ``only_focus`` as well, the faded nodes are left out and the rest packed into as few
    columns and rows as they need. A page whose prose is about one output's ancestry gets the
    ancestry at a size its labels can be read at, instead of a whole model shrunk to fit.

    With ``compact``, the boxes are narrower and taller and a label wraps onto three lines
    (:data:`COMPACT`), for a graph of a few columns that a phone has to show whole.
    """
    if compact:
        margin, column_width, box_width, box_height, row_height, wrap = COMPACT.values()
        most = COMPACT_LINES
    else:
        margin, column_width, box_width, box_height, row_height = (
            MARGIN,
            COLUMN_WIDTH,
            BOX_WIDTH,
            BOX_HEIGHT,
            ROW_HEIGHT,
        )
        wrap, most = 26, 2
    payload = load_result(result)["summary"]
    nodes = payload["nodes"]
    keep = _ancestry(payload, focus) if focus else set(nodes)
    if focus and only_focus:
        # Every parent of a kept node is itself kept, so no edge points at a node left out.
        # An input sits in the column just before its first consumer. Left where the whole
        # model's layout put it, an input could be columns away from the box it feeds, and its
        # edge then ran behind a box in between, which read as feeding that box instead.
        children: dict[str, list[str]] = {}
        for name in keep:
            for parent in nodes[name]["depends_on"]:
                children.setdefault(parent, []).append(name)
        layer = {name: nodes[name]["layer"] for name in keep}
        for name in keep:
            if not nodes[name]["depends_on"] and name in children:
                layer[name] = max(layer[name], min(layer[c] for c in children[name]) - 1)
        nodes = {name: {**nodes[name], "layer": layer[name]} for name in keep}
        layers = sorted({nodes[name]["layer"] for name in keep})
        packed = {}
        for column, layer in enumerate(layers):
            in_layer = sorted(
                (name for name in keep if nodes[name]["layer"] == layer),
                key=lambda name: nodes[name]["row"],
            )
            for row, name in enumerate(in_layer):
                packed[name] = {**nodes[name], "layer": column, "row": row}
        nodes = packed

    columns = max(node["layer"] for node in nodes.values()) + 1
    rows = max(node["row"] for node in nodes.values()) + 1
    unmeasured_drawn = any(
        name in keep and node["kind"] == "measured" and not node.get("measured")
        for name, node in nodes.items()
    )
    # No gap after the last column: it is the width a reader's column has to shrink the drawing
    # by, and every unit of it makes the labels smaller.
    width = margin * 2 + (columns - 1) * column_width + box_width
    legend, header = _legend(margin, margin + 8, width, unmeasured_drawn)
    height = margin * 2 + rows * row_height + header

    def centre(name: str) -> tuple[float, float]:
        node = nodes[name]
        return (
            margin + node["layer"] * column_width + box_width / 2,
            margin + header + node["row"] * row_height + box_height / 2,
        )

    edges = []
    for name, node in sorted(nodes.items()):
        for parent in node["depends_on"]:
            lit = name in keep and parent in keep
            colour = "#607d8b" if lit else "#e4e7e9"
            x1, y1 = centre(parent)
            x2, y2 = centre(name)
            x1 += box_width / 2
            x2 -= box_width / 2
            mid = (x1 + x2) / 2
            # The curve arrives level, so the head points along the row: the line stops where the
            # head starts, and the head's point touches the box it feeds.
            end = x2 - ARROW_LENGTH
            edges.append(
                f'<path d="M{x1:.1f},{y1:.1f} C{mid:.1f},{y1:.1f} {mid:.1f},{y2:.1f} '
                f'{end:.1f},{y2:.1f}" fill="none" stroke="{colour}" '
                f'stroke-width="{1.1 if lit else 0.7}"/>'
                f'<polygon points="{x2:.1f},{y2:.1f} {end:.1f},{y2 - ARROW_HALF_WIDTH:.1f} '
                f'{end:.1f},{y2 + ARROW_HALF_WIDTH:.1f}" fill="{colour}"/>'
            )

    boxes = []
    for name, node in sorted(nodes.items()):
        x = margin + node["layer"] * column_width
        y = margin + header + node["row"] * row_height
        lit = name in keep
        fill = KIND_FILL[node["kind"]] if lit else "#fafafa"
        stroke = KIND_STROKE[node["kind"]] if lit else "#e0e0e0"
        dash = ""
        if node["kind"] == "input" and lit:
            provenance = node.get("provenance", {}).get("kind", "assumption")
            stroke = PROVENANCE_STROKE.get(provenance, stroke)
            dash = (
                f' stroke-dasharray="{PROVENANCE_DASH[provenance]}"'
                if PROVENANCE_DASH.get(provenance)
                else ""
            )
        if node["kind"] == "measured" and not node.get("measured") and lit:
            fill, dash = UNMEASURED_FILL, ' stroke-dasharray="3 3"'
        boxes.append(
            f'<rect x="{x}" y="{y}" width="{box_width}" height="{box_height}" rx="3" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.2"{dash}/>'
        )
        # Whether somebody chose this, as the model file declares it rather than as anything
        # here could infer. One colour whatever the box's border, so that the bar in the legend
        # is the bar on every box; a bar in the border's colour matched no entry in the legend.
        if lit and node.get("decided") == "you":
            boxes.append(
                f'<rect x="{x}" y="{y + 3}" width="3" height="{box_height - 6}" rx="1.5" '
                f'fill="{DECIDED_BAR}"/>'
            )
        label = node["label"]
        if node["kind"] == "ceiling":
            label = f"limit on {label}"
        lines = _wrap(label, wrap, most)
        for i, line in enumerate(lines):
            if compact:
                # Centred in the taller box, whether the label took one line or three.
                offset = box_height / 2 - (len(lines) - 1) * 11.5 / 2 - 2.5 + i * 11.5
            else:
                offset = 13 if len(lines) == 1 else 9 + i * 11.5
            boxes.append(
                f'<text x="{x + 6}" y="{y + offset + 6:g}" font-size="{TEXT}" '
                f'fill="{"#263238" if lit else "#bdbdbd"}">{_esc(line)}</text>'
            )

    title = f"{payload['title']} — dependency graph"
    if focus:
        title += f", showing only what feeds {nodes[focus]['label']}"
    return _svg(width, height, legend + "".join(edges) + "".join(boxes), title)


def _ancestry(payload: dict, name: str) -> set[str]:
    seen, stack = {name}, [name]
    while stack:
        for parent in payload["nodes"][stack.pop()]["depends_on"]:
            if parent not in seen:
                seen.add(parent)
                stack.append(parent)
    return seen


def _swatch(x: float, y: float, fill: str, stroke: str | None, dash: str = "") -> str:
    edge = f' stroke="{stroke}"' if stroke else ""
    pattern = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x:g}" y="{y:g}" width="13" height="10" rx="2" fill="{fill}"{edge}{pattern}/>'


def _legend(x: float, y: float, width: float, unmeasured: bool = False) -> tuple[str, int]:
    """The key above a graph, and how much height it took.

    What a box's fill says is its kind. What an input's border says is where the number came
    from, which is a second question, so it has a line of its own. Entries run on to a new line
    when the next one would pass the drawing's right-hand edge.
    """
    advance = TEXT * 0.58
    kinds = [
        (_swatch(0, 0, KIND_FILL["input"], None), "input"),
        *(
            (_swatch(0, 0, KIND_FILL[kind], KIND_STROKE[kind]), kind)
            for kind in ("derived", "measured", "ceiling")
        ),
    ]
    if unmeasured:
        kinds.append(
            (_swatch(0, 0, UNMEASURED_FILL, KIND_STROKE["measured"], "3 3"), "not measured")
        )
    # Not a kind: the mark an input wears when somebody chose it.
    kinds.append(
        (
            _swatch(0, 0, KIND_FILL["input"], None)
            + f'<rect x="0" y="1" width="3" height="8" rx="1.5" fill="{DECIDED_BAR}"/>',
            "you decide",
        )
    )
    borders = [
        (
            _swatch(0, 0, KIND_FILL["input"], PROVENANCE_STROKE[kind], PROVENANCE_DASH[kind]),
            kind.replace("_", " "),
        )
        for kind in ("fact", "vendor_claim", "assumption")
    ]
    out, line = [], 0
    for lead, entries in ((None, kinds), (LEGEND_BORDERS, borders)):
        offset = 0.0
        top = y + line * LEGEND_LINE
        if lead:
            out.append(
                f'<text x="{x:g}" y="{top + 9:g}" font-size="{TEXT}" fill="#455a64">'
                f"{_esc(lead)}</text>"
            )
            offset = len(lead) * advance + 8
        for swatch, text in entries:
            needs = 17 + len(text) * advance
            if offset and x + offset + needs > width - x:
                line += 1
                top, offset = y + line * LEGEND_LINE, 0.0
            out.append(
                f'<g transform="translate({x + offset:g},{top:g})">{swatch}</g>'
                f'<text x="{x + offset + 17:g}" y="{top + 9:g}" font-size="{TEXT}" '
                f'fill="#455a64">{_esc(text)}</text>'
            )
            offset += needs + 8
        line += 1
    return "".join(out), 34 + (line - 1) * LEGEND_LINE


# -- tornado ----------------------------------------------------------------------------------


def tornado_chart(result: str, output: str, limit: int = 9) -> str:
    """How far one output moves when each uncertain input is swung across its middle 80%.

    Sorted by swing, longest at the top, which is the only ordering that answers the question
    people bring to a tornado: *what should I go and measure first?*
    """
    payload = load_result(result)["summary"]
    declared = payload["tornado"].get(output, [])
    # An input that does not reach this output swings it by nothing, and a row of those is six
    # identical empty bars where the eye is looking for a shape. The count is worth saying; the
    # bars are not. The table beside the figure keeps every row, including the still ones.
    bars = [bar for bar in declared if bar["span"] > 0][:limit]
    still = sum(1 for bar in declared if bar["span"] <= 0)
    node = payload["nodes"][output]
    if not bars:
        return _svg(360, 40, '<text x="8" y="24" font-size="11">no uncertain input</text>', "empty")

    # The label column fits the longest label rather than assuming one. The web service names
    # its inputs in sentences, and a fixed column put the longest of them off the left of the page.
    longest = max(len(bar["label"]) for bar in bars)
    label_width, chart_width, bar_height = max(168.0, longest * TEXT * 0.55 + 8), 300.0, 24.0
    width = label_width + chart_width + MARGIN * 2 + 96
    height = MARGIN * 2 + 42 + len(bars) * bar_height + (14 if still else 0)

    base = bars[0]["base"]
    low = min(min(bar["low"], bar["high"]) for bar in bars)
    high = max(max(bar["low"], bar["high"]) for bar in bars)
    low, high = min(low, base), max(high, base)
    span = (high - low) or 1.0

    def at(value: float) -> float:
        return MARGIN + label_width + (value - low) / span * chart_width

    body = [
        f'<text x="{MARGIN}" y="{MARGIN + 12}" font-size="11" fill="#263238">'
        f"{_esc(node['label'])} ({_esc(unit_label(node['unit']))}) — point estimate "
        f"{_esc(fmt(base, node['unit']))}</text>",
        f'<line x1="{at(base):.1f}" y1="{MARGIN + 24}" x2="{at(base):.1f}" '
        f'y2="{MARGIN + 38 + len(bars) * bar_height:.0f}" stroke="#455a64" stroke-width="1" '
        f'stroke-dasharray="3 2"/>',
    ]
    if still:
        body.append(
            f'<text x="{MARGIN + label_width - 8}" y="{height - MARGIN + 2:.0f}" font-size="{TEXT}" '
            f'text-anchor="end" fill="#90a4ae">and {still} that do not move it at all</text>'
        )
    for i, bar in enumerate(bars):
        y = MARGIN + 34 + i * bar_height
        left, right = sorted((bar["low"], bar["high"]))
        kind = "measured" if bar["kind"] == "measured" else "input"
        body.append(
            f'<rect x="{at(left):.1f}" y="{y}" width="{max(at(right) - at(left), 1.5):.1f}" '
            f'height="{bar_height - 8}" rx="2" fill="{KIND_FILL[kind]}" '
            f'stroke="{KIND_STROKE[kind]}" stroke-width="1"/>'
        )
        body.append(
            f'<text x="{MARGIN + label_width - 8}" y="{y + 12}" font-size="{TEXT}" '
            f'text-anchor="end" fill="#263238">{_esc(bar["label"])}</text>'
        )
        body.append(
            f'<text x="{MARGIN + label_width + chart_width + 8}" y="{y + 12}" font-size="{TEXT}" '
            f'fill="#546e7a">{_esc(fmt(bar["span"], node["unit"]))}</text>'
        )
    return _svg(width, height, "".join(body), f"Tornado for {node['label']}")


# -- a distribution ------------------------------------------------------------------------


#: How much of the sampled mass a distribution figure draws before it truncates. A long right
#: tail is a fact about the model, but a figure that spends nine tenths of its width on the last
#: hundredth of the samples shows the reader nothing. The figure draws the bulk and says in words
#: how far the tail runs and how much of it was left off.
SHOWN_MASS = 0.99


def distribution(result: str, node_name: str, plain: bool = False, middle: bool = False) -> str:
    """One node's sampled distribution, with the interval and the point estimate on it.

    The point estimate is drawn as a line through the histogram deliberately. Seeing where the
    single number a plan was built on actually sits in the distribution it came from is the whole
    of ch13's argument, and it is much harder to argue with than a paragraph.

    ``plain`` words it for a page before ch13, in the model viewer's own words for the same
    three points: :func:`distribution_in_plain_words`.

    With ``middle``, the median is drawn too, solid and dark, for a page whose argument is where
    the point estimate sits against the middle answer rather than against the ends. A linear axis
    is then labelled at its ends only: its midpoint tick is an arbitrary figure, and it landed
    beside one of the lines above it, where a reader took the tick's figure for the line's (ch21).
    """
    payload = load_result(result)["summary"]
    node = payload["nodes"][node_name]
    histogram, summary = node.get("histogram"), node.get("summary")
    if not histogram or not summary:
        return _svg(
            360, 40, '<text x="8" y="24" font-size="11">this node does not vary</text>', "fixed"
        )

    width, height = 520.0, 240.0
    plot_left, plot_right, plot_top, plot_bottom = 46.0, width - 24, 72.0, height - 42
    counts, edges = histogram["counts"], histogram["edges"]
    # A quantity spanning orders of magnitude arrives already binned by ratio (`mc.histogram`).
    # It gets a logarithmic axis to match, and no truncation: on that axis the tail costs a
    # third of the width rather than nine tenths of it.
    logarithmic = histogram.get("spacing") == "log"
    if logarithmic:
        drawn, hidden = len(counts), 0
    else:
        drawn, hidden = _visible_bins(counts, edges, summary, node.get("point"))
    low, high = edges[0], edges[drawn]
    span = (math.log10(high / low) if logarithmic else high - low) or 1.0
    tallest = max(counts[:drawn]) or 1

    def at_x(value: float) -> float:
        travelled = math.log10(max(value, low) / low) if logarithmic else value - low
        return plot_left + travelled / span * (plot_right - plot_left)

    unit = node["unit"]
    if plain:
        heading = PLAIN_HEADING.format(samples=payload["scenario"]["samples"])
        detail = PLAIN_DETAIL.format(
            low=_esc(fmt(summary["p5"], unit)),
            high=_esc(fmt(summary["p95"], unit)),
            middle=_esc(fmt(summary["p50"], unit)),
        )
    else:
        heading = f"{payload['scenario']['samples']:,} samples"
        detail = (
            f"90% interval {_esc(fmt(summary['p5'], unit))} to "
            f"{_esc(fmt(summary['p95'], unit))} · median "
            f"{_esc(fmt(summary['p50'], unit))}"
        )
    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">'
        f"{_esc(node['label'])} — {heading}</text>",
        f'<text x="{MARGIN}" y="34" font-size="{TEXT}" fill="#546e7a">{detail}'
        f"{' · horizontal axis logarithmic' if logarithmic else ''}</text>",
    ]
    for i, count in enumerate(counts[:drawn]):
        x1, x2 = at_x(edges[i]), at_x(edges[i + 1])
        bar = (count / tallest) * (plot_bottom - plot_top)
        inside = summary["p5"] <= (edges[i] + edges[i + 1]) / 2 <= summary["p95"]
        body.append(
            f'<rect x="{x1:.2f}" y="{plot_bottom - bar:.2f}" width="{max(x2 - x1 - 0.4, 0.4):.2f}" '
            f'height="{bar:.2f}" fill="{"#9fc0dd" if inside else "#dde5ec"}"/>'
        )
    markers = [
        (summary["p5"], "#455a64", PLAIN_LOW if plain else "p5"),
        (node.get("point"), "#b3413a", "point"),
        *([(summary["p50"], "#263238", MIDDLE_LABEL)] if middle else []),
        (summary["p95"], "#455a64", PLAIN_HIGH if plain else "p95"),
    ]
    # Two rows, so that a point estimate sitting almost on top of a percentile does not print
    # one label over the other. Both rows clear the subtitle and the line below them.
    row_ends = [MARGIN - 2.0, MARGIN - 2.0]
    row_y = (plot_top - 10.0, plot_top - 22.0)
    for value, colour, label in markers:
        if value is None or not low <= value <= high:
            continue
        x = at_x(value)
        half = len(label) * TEXT * 0.28 + 3
        row = next((i for i, end in enumerate(row_ends) if x - half >= end), None)
        if row is None:  # both taken: the less crowded one, and accept the crowding
            row = row_ends.index(min(row_ends))
        row_ends[row] = x + half
        dash = (
            ""
            if label in ("point", "the single number", MIDDLE_LABEL)
            else ' stroke-dasharray="3 2"'
        )
        body.append(
            f'<line x1="{x:.1f}" y1="{plot_top - 6:.0f}" x2="{x:.1f}" '
            f'y2="{plot_bottom:.0f}" stroke="{colour}" stroke-width="1.2"{dash}/>'
        )
        if label:
            body.append(
                f'<text x="{x:.1f}" y="{row_y[row]:.0f}" font-size="{TEXT}" '
                f'text-anchor="middle" fill="{colour}">{_esc(label)}</text>'
            )
    body.append(
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" '
        f'stroke="#90a4ae" stroke-width="1"/>'
    )
    ticks = _ticks(low, high, logarithmic)
    if middle and not logarithmic:
        ticks = [ticks[0], ticks[-1]]
    for value, anchor in ticks:
        x = at_x(value)
        body.append(
            f'<line x1="{x:.1f}" y1="{plot_bottom}" x2="{x:.1f}" y2="{plot_bottom + 4}" '
            f'stroke="#90a4ae"/>'
            f'<text x="{x:.1f}" y="{plot_bottom + 16}" font-size="{TEXT}" text-anchor="{anchor}" '
            f'fill="#546e7a">{_esc(fmt(value, node["unit"]))}</text>'
        )
    if hidden:
        total = sum(counts) or 1
        body.append(
            f'<text x="{plot_right:.0f}" y="{plot_top - 22:.0f}" font-size="{TEXT}" '
            f'text-anchor="end" fill="#90a4ae">'
            f"{hidden / total * 100:.1f}% of {PLAIN_TAIL if plain else 'samples'} run on to "
            f"{_esc(fmt(edges[-1], node['unit']))}</text>"
        )
    return _svg(
        width,
        height,
        "".join(body),
        f"Distribution of {node['label']}",
    )


#: The distribution figure's words for a page before ch13, which names a sample, an interval, a
#: median and a percentile. They follow the model viewer's plain Details labels
#: (`sizing/viewer/words.json`), because those pages send the reader from the figure to that panel.
PLAIN_HEADING = "{samples:,} futures"
PLAIN_DETAIL = "1 future in 20 below {low} · 1 in 20 above {high} · middle {middle}"
PLAIN_LOW = "low end"
PLAIN_HIGH = "high end"
PLAIN_TAIL = "futures"


#: The label on the median's line, where a figure draws one.
MIDDLE_LABEL = "median"


def distribution_against_the_middle(result: str, node_name: str) -> str:
    """The plain distribution figure with the median drawn as a line, for ch12.

    ch12's argument is where the point estimate sits against the middle answer, which the plain
    figure only prints in its subtitle. The page comes before ch13, so the rest of the words are
    the plain ones.
    """
    return distribution(result, node_name, plain=True, middle=True)


def distribution_with_median(result: str, node_name: str) -> str:
    """The distribution figure with the median marked as well as the point estimate, for ch21.

    ch21 offers the median as the first of three numbers to choose from and tells the reader to
    choose off the chart, so the chart has to show it. The page comes after ch13, so the words
    are the usual ones.
    """
    return distribution(result, node_name, middle=True)


def distribution_in_plain_words(result: str, node_name: str) -> str:
    """The distribution figure for a chapter before ch13: the same drawing, in the viewer's words.

    ch13 names a sample, an interval, a median and a percentile. A page before it says futures,
    the low and high ends, and the middle, as the model viewer's Details panel does.
    """
    return distribution(result, node_name, plain=True)


def _ticks(low: float, high: float, logarithmic: bool) -> list[tuple[float, str]]:
    """Where to put the labels along the bottom, and which way to hang them off their tick.

    The ends are always labelled and always fall inside the canvas, which is why they are
    anchored rather than centred. Between them, a decade if the axis is logarithmic and the
    midpoint if it is not.
    """
    ticks = [(low, "start")]
    if logarithmic:
        span = math.log10(high / low)
        ticks += [
            (float(10**power), "middle")
            for power in range(math.ceil(math.log10(low)), math.floor(math.log10(high)) + 1)
            # Not so close to an end that the two labels would collide.
            if 0.09 < math.log10(10**power / low) / span < 0.91
        ]
    else:
        ticks.append((low + (high - low) / 2, "middle"))
    return [*ticks, (high, "end")]


def _visible_bins(
    counts: list[int], edges: list[float], summary: dict, point: float | None
) -> tuple[int, int]:
    """How many bins to draw, and how many samples that leaves off the right-hand end.

    Always enough to reach the top of the interval and the point estimate, whatever the tail
    does: the figure exists to show where the point estimate sits inside the interval, and a
    truncation that hid either of those would be hiding the argument.
    """
    total = sum(counts) or 1
    must_reach = max(x for x in (summary["p95"], point) if x is not None)
    running = 0
    for i, count in enumerate(counts):
        running += count
        if running >= total * SHOWN_MASS and edges[i + 1] >= must_reach:
            return i + 1, total - running
    return len(counts), 0


# -- convergence ------------------------------------------------------------------------------


def _decade(power: int) -> str:
    """A tick label for ten to the power, short enough to sit beside an axis."""
    if power >= 6:
        return f"${10 ** (power - 6)}M"
    if power >= 3:
        return f"${10 ** (power - 3)}k"
    return f"${10**power}"


#: The convergence figure's two line labels and its subtitle, in the convergence table's names.
CONVERGENCE_SERIES = ("90% interval half-width", "run-to-run spread of p95")
CONVERGENCE_SUBTITLE = (
    "Both axes logarithmic. The half-width settles; the run-to-run spread keeps falling"
)


def convergence(result: str) -> str:
    """The two quantities ch14 is at pains to separate, drawn on one pair of axes.

    The interval's half-width is a property of the model, and more samples do not move it. The
    run-to-run spread is a property of how hard you looked, and falls at one over the square root
    of n. Drawn apart they are two unremarkable lines; drawn together they are
    the argument, which is why the flat one is in the picture at all.
    """
    payload = load_result(result)["summary"]
    points = payload["convergence"]
    width, height = 520.0, 264.0
    left, right, top, bottom = 64.0, width - 16, 56.0, height - 46

    counts = [p["samples"] for p in points]
    series = (
        ("half_width", "#4a7ba7", CONVERGENCE_SERIES[0]),
        ("p95_spread", "#c8791a", CONVERGENCE_SERIES[1]),
    )
    log_n = [math.log10(c) for c in counts]
    x_low, x_high = min(log_n), max(log_n)
    magnitudes = [math.log10(p[key]) for key, _, _ in series for p in points]
    y_low, y_high = math.floor(min(magnitudes)), math.ceil(max(magnitudes))

    def at(lx: float, ly: float) -> tuple[float, float]:
        return (
            left + (lx - x_low) / (x_high - x_low or 1) * (right - left),
            bottom - (ly - y_low) / (y_high - y_low or 1) * (bottom - top),
        )

    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">Two things that are easily '
        f"confused, at rising sample counts</text>",
        f'<text x="{MARGIN}" y="34" font-size="{TEXT}" fill="#546e7a">'
        f"{_esc(CONVERGENCE_SUBTITLE)}</text>",
    ]
    for power in range(y_low, y_high + 1):
        _, y = at(x_low, power)
        body.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#eceff1"/>'
            f'<text x="{left - 6:.0f}" y="{y + 3:.1f}" font-size="{TEXT}" text-anchor="end" '
            f'fill="#546e7a">{_decade(power)}</text>'
        )
    # The law, anchored on the first sample count the run was willing to fit it from, and cut
    # where it would leave the axes rather than drawn off the edge of the figure.
    anchor = next(i for i, c in enumerate(counts) if c >= payload["law_measured_from"])
    law_y = math.log10(points[anchor]["p95_spread"])
    end_x = x_high
    if law_y - 0.5 * (x_high - log_n[anchor]) < y_low:
        end_x = log_n[anchor] + 2 * (law_y - y_low)
    law = ((log_n[anchor], law_y), (end_x, law_y - 0.5 * (end_x - log_n[anchor])))
    body.append(
        '<path d="M'
        + " L".join(f"{x:.1f},{y:.1f}" for x, y in (at(*pair) for pair in law))
        + '" fill="none" stroke="#b3413a" stroke-width="1.2" stroke-dasharray="4 3"/>'
    )
    law_end_x, law_end_y = at(*law[1])
    body.append(
        f'<text x="{law_end_x - 4:.1f}" y="{law_end_y + 13:.1f}" font-size="{TEXT}" '
        f'text-anchor="end" fill="#b3413a">one over the square root of n</text>'
    )
    for key, colour, label in series:
        magnitude = [math.log10(p[key]) for p in points]
        path = " L".join(
            f"{x:.1f},{y:.1f}"
            for x, y in (at(lx, ly) for lx, ly in zip(log_n, magnitude, strict=True))
        )
        body.append(f'<path d="M{path}" fill="none" stroke="{colour}" stroke-width="1.8"/>')
        for lx, ly in zip(log_n, magnitude, strict=True):
            x, y = at(lx, ly)
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{colour}"/>')
        x, y = at(log_n[0], magnitude[0])
        body.append(
            f'<text x="{x + 8:.1f}" y="{y - 8:.1f}" font-size="{TEXT}" fill="{colour}">'
            f"{_esc(label)}</text>"
        )
    body.append(
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#90a4ae"/>'
    )
    for i, (lx, count) in enumerate(zip(log_n, counts, strict=True)):
        x, _ = at(lx, y_low)
        anchor = "start" if i == 0 else "end" if i == len(counts) - 1 else "middle"
        body.append(
            f'<text x="{x:.1f}" y="{bottom + 14:.0f}" font-size="{TEXT}" text-anchor="{anchor}" '
            f'fill="#546e7a">{count:,}</text>'
        )
    body.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 8:.0f}" font-size="{TEXT}" '
        f'text-anchor="middle" fill="#455a64">samples drawn</text>'
    )
    return _svg(width, height, "".join(body), "Monte Carlo convergence")


# -- Part II's two shapes ----------------------------------------------------------------


def queueing_curve(result: str) -> str:
    """Residence time against utilisation: flat, and then vertical.

    Drawn on linear axes on purpose. A logarithmic vertical axis would make this curve look like
    a gentle slope, which is how most people have seen it and is the reason most people are
    surprised by it in production. The shape is the argument, and flattening the shape to fit the
    page would be flattening the argument.

    The line is drawn through the dense sweep, so it has no corners the formula does not have; the
    dots are the table's rows. The one dashed line is the model's own queueing margin, taken off
    full utilisation: the *Allowed* column of the chapter's ceilings table.
    """
    summary = load_result(result)["summary"]
    rows = summary["curve"]
    last = rows[-1]["utilisation"]
    line = [row for row in summary["smooth"] if row["utilisation"] <= last + 1e-9]
    width, height = 500.0, 256.0
    left, right, top, bottom = 52.0, width - 20, 46.0, height - 42

    ceiling_value = max(row["inflation"] for row in rows)

    def at(utilisation: float, inflation: float) -> tuple[float, float]:
        return (
            left + utilisation * (right - left),
            bottom - (inflation - 1.0) / (ceiling_value - 1.0) * (bottom - top),
        )

    # From an idle fleet, where a request takes exactly its service time, to the last row.
    path = " L".join(
        f"{x:.1f},{y:.1f}"
        for x, y in [at(0.0, 1.0)] + [at(r["utilisation"], r["inflation"]) for r in line]
    )
    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">How much longer a request '
        f"takes than it would on an idle fleet</text>",
        f'<text x="{MARGIN}" y="34" font-size="{TEXT}" fill="#546e7a">The arrival rate moves; '
        f"the software and the machines do not</text>",
    ]
    # Where the model's own margin puts the fleet, so the curve is read against a decision rather
    # than admired. Written up the line rather than across the top, so the curve does not cross it.
    margin = summary["queueing_margin"]
    x = left + (1.0 - margin) * (right - left)
    body.append(
        f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" stroke="#c8791a" '
        f'stroke-width="1" stroke-dasharray="3 3"/>'
        f'<text transform="rotate(-90 {x - 5:.1f} {bottom - 24:.0f})" x="{x - 5:.1f}" '
        f'y="{bottom - 24:.0f}" font-size="11" fill="#c8791a">'
        f"{_esc(QUEUEING_ALLOWED.format(margin=margin))}</text>"
    )
    body.append(f'<path d="M{path}" fill="none" stroke="#4a7ba7" stroke-width="2"/>')
    for row in rows:
        cx, cy = at(row["utilisation"], row["inflation"])
        body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.4" fill="#4a7ba7"/>')

    body.append(
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#90a4ae"/>'
    )
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        tx = left + fraction * (right - left)
        body.append(
            f'<text x="{tx:.1f}" y="{bottom + 15:.0f}" font-size="{TEXT}" text-anchor="middle" '
            f'fill="#546e7a">{fraction:.0%}</text>'
        )
    for value in (1.0, ceiling_value / 2, ceiling_value):
        ty = bottom - (value - 1.0) / (ceiling_value - 1.0) * (bottom - top)
        body.append(
            f'<text x="{left - 6:.0f}" y="{ty + 3:.1f}" font-size="{TEXT}" text-anchor="end" '
            f'fill="#546e7a">{value:.0f}x</text>'
        )
    body.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 8:.0f}" font-size="{TEXT}" '
        f'text-anchor="middle" fill="#455a64">utilisation</text>'
        f'<text transform="rotate(-90 13 {(top + bottom) / 2:.0f})" x="13" '
        f'y="{(top + bottom) / 2:.0f}" font-size="{TEXT}" text-anchor="middle" fill="#455a64">'
        f"how much longer a request takes</text>"
    )
    return _svg(width, height, "".join(body), "Residence time against utilisation")


#: The dashed line's label on the queueing curve: the model's margin, formatted from the result.
QUEUEING_ALLOWED = "allowed: a {margin:.0%} margin"
#: The zoomed figure's words. Each panel's title and ticks are formatted from the result.
ZOOM_TITLE = "The same curve, stopped in two places"
ZOOM_SUBTITLE = "Each stretch is drawn to fill its own axes. The bend sits wherever the axis stops"
ZOOM_PANEL = "idle share {idle_from:.0%} to {idle_to:.0%}"
ZOOM_TICK = "{utilisation:.0%} busy"


def queueing_zoom(result: str) -> str:
    """The same curve, stopped in two places, each stretch drawn to fill its own axes.

    The two stretches are chosen so that the idle share of the fleet shrinks by the same factor
    across each. That is the one sense in which the curve is the same at every scale, and it is
    why the two drawings are identical: the bend sits in the same place in each frame, and that
    place is a different utilisation. The knee is where the axis stopped.
    """
    summary = load_result(result)["summary"]
    smooth = summary["smooth"]
    width, height = 500.0, 222.0
    top, bottom = 62.0, height - 40
    gap = 44.0
    panel_width = (width - 2 * MARGIN - 34 - gap) / 2
    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">{_esc(ZOOM_TITLE)}</text>',
        f'<text x="{MARGIN}" y="34" font-size="{TEXT}" fill="#546e7a">{_esc(ZOOM_SUBTITLE)}</text>',
    ]
    for i, (start, stop) in enumerate(summary["zoom"]):
        left = MARGIN + 34 + i * (panel_width + gap)
        right = left + panel_width
        rows = [r for r in smooth if start - 1e-9 <= r["utilisation"] <= stop + 1e-9]
        low, high = rows[0]["inflation"], rows[-1]["inflation"]

        def at(
            u: float, v: float, left=left, right=right, low=low, high=high, start=start, stop=stop
        ) -> tuple[float, float]:
            return (
                left + (u - start) / (stop - start) * (right - left),
                bottom - (v - low) / (high - low) * (bottom - top),
            )

        path = " L".join(
            f"{x:.1f},{y:.1f}" for x, y in (at(r["utilisation"], r["inflation"]) for r in rows)
        )
        panel = ZOOM_PANEL.format(idle_from=1 - start, idle_to=1 - stop)
        body.append(
            f'<text x="{left:.1f}" y="{top - 10:.0f}" font-size="10.5" fill="#455a64">'
            f"{_esc(panel)}</text>"
            f'<line x1="{left:.1f}" y1="{bottom}" x2="{right:.1f}" y2="{bottom}" stroke="#90a4ae"/>'
            f'<line x1="{left:.1f}" y1="{top}" x2="{left:.1f}" y2="{bottom}" stroke="#90a4ae"/>'
            f'<path d="M{path}" fill="none" stroke="#4a7ba7" stroke-width="2"/>'
        )
        for u, anchor in ((start, "start"), (stop, "end")):
            x, _ = at(u, low)
            body.append(
                f'<text x="{x:.1f}" y="{bottom + 15:.0f}" font-size="10.5" '
                f'text-anchor="{anchor}" fill="#546e7a">'
                f"{_esc(ZOOM_TICK.format(utilisation=u))}</text>"
            )
        for v in (low, high):
            _, y = at(start, v)
            body.append(
                f'<text x="{left - 5:.1f}" y="{y + 4:.1f}" font-size="10.5" text-anchor="end" '
                f'fill="#546e7a">{v:.3g}x</text>'
            )
    return _svg(width, height, "".join(body), ZOOM_TITLE)


#: The scaling figure's title.
SCALING_TITLE = "What more machines buy"


def scaling_curve(result: str) -> str:
    """Throughput against host count, against the straight line nobody gets.

    Two curves and the gap between them. The straight line is what a budget assumes; the other is
    what the machines do. The place they stop diverging and start converging on nothing is the
    peak, and the peak is a property of the software.
    """
    summary = load_result(result)["summary"]
    rows = summary["curve"]
    width, height = 500.0, 260.0
    left, right, top, bottom = 56.0, width - 20, 42.0, height - 42

    most_hosts = max(row["hosts"] for row in rows)
    # Scaled to what the fleet can actually reach, not to the straight line — which is nine times
    # taller and would squash the real curve onto the axis. So the line a budget assumes runs off
    # the top of the figure, which is a fair description of what it does in practice.
    tallest = max(row["achievable_throughput"] for row in rows) * 1.35

    def at(hosts: float, throughput: float) -> tuple[float, float]:
        return (
            left + hosts / most_hosts * (right - left),
            bottom - min(throughput / tallest, 1.0) * (bottom - top),
        )

    def path_of(key: str) -> str:
        return " L".join(f"{x:.1f},{y:.1f}" for x, y in (at(r["hosts"], r[key]) for r in rows))

    leaves_at = next(
        (row["hosts"] for row in rows if row["linear_throughput"] > tallest), most_hosts
    )

    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">{_esc(SCALING_TITLE)}</text>',
        f'<text x="{MARGIN}" y="34" font-size="{TEXT}" fill="#546e7a">The straight line is what a '
        f"budget assumes. The curve is what the machines do</text>",
        f'<path d="M{path_of("linear_throughput")}" fill="none" stroke="#b3413a" '
        f'stroke-width="1.2" stroke-dasharray="4 3"/>',
        f'<path d="M{path_of("achievable_throughput")}" fill="none" stroke="#4a7ba7" '
        f'stroke-width="2"/>',
    ]
    exit_x, _ = at(leaves_at, tallest)
    body.append(
        f'<text x="{exit_x + 6:.1f}" y="{top + 12:.0f}" font-size="{TEXT}" fill="#b3413a">'
        f"the budget's line leaves the page at {leaves_at:.0f} hosts</text>"
    )

    peak = max(rows, key=lambda row: row["achievable_throughput"])
    peak_x, peak_y = at(peak["hosts"], peak["achievable_throughput"])
    body.append(
        f'<circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="4" fill="none" stroke="#b3413a" '
        f'stroke-width="1.5"/>'
        f'<text x="{peak_x:.1f}" y="{peak_y - 10:.1f}" font-size="{TEXT}" text-anchor="middle" '
        f'fill="#b3413a">past here it falls</text>'
    )
    body.append(
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#90a4ae"/>'
    )
    for row in rows:
        if row["hosts"] not in (rows[0]["hosts"], 64, 128, 256, most_hosts):
            continue
        x, _ = at(row["hosts"], 0)
        body.append(
            f'<text x="{x:.1f}" y="{bottom + 15:.0f}" font-size="{TEXT}" text-anchor="middle" '
            f'fill="#546e7a">{row["hosts"]:.0f}</text>'
        )
    body.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 8:.0f}" font-size="{TEXT}" '
        f'text-anchor="middle" fill="#455a64">hosts</text>'
        f'<text x="{left - 6:.0f}" y="{top + 4:.0f}" font-size="{TEXT}" text-anchor="end" '
        f'fill="#546e7a">{tallest / 1000:.0f}k</text>'
        f'<text x="{left - 6:.0f}" y="{bottom:.0f}" font-size="{TEXT}" text-anchor="end" '
        f'fill="#546e7a">0</text>'
        f'<text transform="rotate(-90 13 {(top + bottom) / 2:.0f})" x="13" '
        f'y="{(top + bottom) / 2:.0f}" font-size="{TEXT}" text-anchor="middle" fill="#455a64">'
        f"requests per second</text>"
    )
    return _svg(width, height, "".join(body), "Throughput against host count")


#: The shapes figure's title.
SHAPES_TITLE = "The four shapes the sampler draws from"


def distribution_shapes(_result: str | None = None) -> str:
    """The four shapes this book uses, drawn from their own percentile functions.

    Not illustrations of distributions: these are the functions in ``sizing/mc.py`` themselves,
    evaluated at evenly spaced percentiles and plotted. If somebody changes one, this picture
    changes, which is the only kind of figure this book is willing to print.

    All four are scaled onto the same horizontal range so the *shapes* can be compared. Their
    parameters are chosen to cover about the same values, centred in about the same place, which
    is the fair comparison: the question is never "which is wider" but "which is the right claim
    about what can happen".

    Narrow on purpose, with each shape's name above its histogram rather than in a column beside
    it. The site draws an inlined SVG at its own width, capped at the column, so a 520-unit canvas
    put the names, the figure's only labels, at about five pixels on a phone. At 360 units they
    stay above nine.
    """
    import numpy as np

    from sizing import mc

    width, height = 360.0, 306.0
    left, right = float(MARGIN), width - MARGIN
    panel = 68.0
    percentiles = np.linspace(0.001, 0.999, 1200)

    shapes = (
        ("uniform", mc.uniform_ppf(percentiles, 2.0, 8.0), "bounds, and nothing else claimed"),
        (
            "triangular",
            mc.triangular_ppf(percentiles, 2.0, 4.0, 8.0),
            "an expert's least / likely / most",
        ),
        (
            "lognormal",
            mc.lognormal_ppf(percentiles, 2.6, 7.4),
            "prices, growth, anything compounding",
        ),
        ("normal", mc.normal_ppf_scaled(percentiles, 5.0, 1.15), "measurement error"),
    )
    low = min(float(values.min()) for _, values, _ in shapes)
    high = max(float(values.max()) for _, values, _ in shapes)
    span = high - low

    body = [f'<text x="{MARGIN}" y="20" font-size="13" fill="#263238">{_esc(SHAPES_TITLE)}</text>']
    for index, (name, values, caption) in enumerate(shapes):
        top = 34.0 + index * panel
        label = top + 12
        base = top + panel - 6
        counts, edges = np.histogram(values, bins=70, range=(low, high))
        tallest = max(counts.max(), 1)
        body.append(
            f'<text x="{MARGIN}" y="{label:.0f}" font-size="12.5" fill="#263238">'
            f'<tspan font-weight="600">{_esc(name)}</tspan>'
            f'<tspan fill="#546e7a" font-size="11.5"> · {_esc(caption)}</tspan></text>'
        )
        for i, count in enumerate(counts):
            x1 = left + (edges[i] - low) / span * (right - left)
            x2 = left + (edges[i + 1] - low) / span * (right - left)
            bar = (count / tallest) * (base - label - 8)
            body.append(
                f'<rect x="{x1:.2f}" y="{base - bar:.2f}" width="{max(x2 - x1 - 0.4, 0.4):.2f}" '
                f'height="{bar:.2f}" fill="#9fc0dd"/>'
            )
        body.append(
            f'<line x1="{left}" y1="{base:.1f}" x2="{right}" y2="{base:.1f}" stroke="#90a4ae"/>'
        )
    return _svg(width, height, "".join(body), "The four distributions this book uses")


# -- two quotes for one workload (ch22) ------------------------------------------------------


def paired_difference(result: str) -> str:
    """The difference between two totals, taken over the same futures, with the tie marked.

    One histogram, split at zero. Everything to the left is a future in which the challenger's
    quote came out cheaper; everything to the right is one in which the incumbent's did. The
    two shares are written on the figure, because they are the number a comparison is for and
    the one a pair of intervals side by side cannot give (ch22).

    Drawn narrow and set large, because the chapter reads the tie line and the p5 and p95
    marks off it: at a phone's column the text stays above nine pixels. The axis is labelled at
    its two ends and at the tie, and nowhere else, so that no tick sits beside a mark and reads
    as its value.
    """
    payload = load_result(result)["summary"]
    node = payload["nodes"]["difference"]
    paired = payload["paired"]
    histogram, summary = node["histogram"], node["summary"]
    counts, edges = histogram["counts"], histogram["edges"]

    width, height = 440.0, 330.0
    plot_left, plot_right, plot_top, plot_bottom = 20.0, width - 20, 118.0, height - 40
    low, high = edges[0], edges[-1]
    span = (high - low) or 1.0
    tallest = max(counts) or 1

    def at_x(value: float) -> float:
        return plot_left + (value - low) / span * (plot_right - plot_left)

    cheaper, dearer = "#5b8fb9", "#c98a6b"
    body = [
        f'<text x="{MARGIN}" y="22" font-size="15" fill="#263238">{_esc(node["label"])}</text>',
        f'<text x="{MARGIN}" y="42" font-size="13.5" fill="#546e7a">'
        f"{paired['shared_inputs']} inputs drawn once for both · median "
        f"{_esc(signed_money(summary['p50']))}</text>",
        f'<text x="{MARGIN}" y="61" font-size="13.5" fill="#546e7a">'
        f"middle nine in ten {_esc(signed_money(summary['p5']))} to "
        f"{_esc(signed_money(summary['p95']))}</text>",
    ]
    # The two shares, as a legend above the plot, where they cannot land on a bar or a mark.
    for i, (colour, text) in enumerate(
        (
            (cheaper, f"challenger cheaper in {paired['share_challenger_cheaper']:.0%} of futures"),
            (dearer, f"incumbent cheaper in {paired['share_incumbent_cheaper']:.0%}"),
        )
    ):
        y = 84 + i * 18
        body.append(
            f'<rect x="{MARGIN}" y="{y - 10}" width="11" height="11" fill="{colour}"/>'
            f'<text x="{MARGIN + 17}" y="{y}" font-size="14" fill="{colour}">{_esc(text)}</text>'
        )
    for i, count in enumerate(counts):
        x1, x2 = at_x(edges[i]), at_x(edges[i + 1])
        bar = (count / tallest) * (plot_bottom - plot_top - 24)
        middle = (edges[i] + edges[i + 1]) / 2
        body.append(
            f'<rect x="{x1:.2f}" y="{plot_bottom - bar:.2f}" width="{max(x2 - x1 - 0.4, 0.4):.2f}" '
            f'height="{bar:.2f}" fill="{cheaper if middle < 0 else dearer}"/>'
        )
    zero = at_x(0.0)
    body.append(
        f'<line x1="{zero:.1f}" y1="{plot_top + 4:.0f}" x2="{zero:.1f}" y2="{plot_bottom:.0f}" '
        f'stroke="#263238" stroke-width="1.4"/>'
        f'<text x="{zero:.1f}" y="{plot_top - 2:.0f}" font-size="13.5" text-anchor="middle" '
        f'fill="#263238">the two totals tie</text>'
    )
    for value, label in ((summary["p5"], "p5"), (summary["p95"], "p95")):
        x = at_x(value)
        body.append(
            f'<line x1="{x:.1f}" y1="{plot_top + 24:.0f}" x2="{x:.1f}" y2="{plot_bottom:.0f}" '
            f'stroke="#455a64" stroke-width="1.2" stroke-dasharray="4 3"/>'
            f'<text x="{x:.1f}" y="{plot_top + 19:.0f}" font-size="13.5" text-anchor="middle" '
            f'fill="#455a64">{label}</text>'
        )
    body.append(
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" '
        f'stroke="#90a4ae" stroke-width="1"/>'
    )
    # The ends, and the tie where it is clear of both: a midpoint tick landed beside the p5 line
    # and read as its value.
    ticks = [(low, "start"), (high, "end")]
    if 0.15 < (0.0 - low) / span < 0.85:
        ticks.append((0.0, "middle"))
    for value, anchor in ticks:
        x = at_x(value)
        body.append(
            f'<line x1="{x:.1f}" y1="{plot_bottom}" x2="{x:.1f}" y2="{plot_bottom + 5}" '
            f'stroke="#90a4ae"/>'
            f'<text x="{x:.1f}" y="{plot_bottom + 21}" font-size="13.5" text-anchor="{anchor}" '
            f'fill="#546e7a">{_esc(signed_money(value))}</text>'
        )
    return _svg(width, height, "".join(body), "The difference between two totals, paired")


def power_wall(result: str) -> str:
    """The same fleet on two axes: watts, which have a wall, and money, which has a slope.

    ch16 sizes backwards from an allocation. The left panel is what the building supplies drawn
    as a line across the fleet's draw, with the largest whole number of hosts under it and the
    next one over it. The right panel is the same hosts against what they cost over the horizon,
    and there is deliberately nothing drawn across it: a price can be argued with.

    The marked points are named in a key under each panel rather than beside the line, because
    those names are what the page's paragraph reads out, and beside the line they had to be the
    smallest text in the figure to fit.
    """
    payload = load_result(result)["summary"]
    rows = payload["curve"]
    allocation = float(payload["allocation"])
    fits = int(round(payload["fits"]))
    demand = int(round(payload["demand"]))
    by_hosts = {int(round(row["hosts"])): row for row in rows}
    width, height = 560.0, 300.0
    plot_top, plot_bottom = 50.0, 200.0
    hosts_max = max(by_hosts)
    panels = (
        (WALL_WORDS["watts"], "facility_power", 44.0, 262.0),
        (WALL_WORDS["money"], "tco", 326.0, 544.0),
    )
    body = []
    for title, key, left, right in panels:
        top_value = max(row[key] for row in rows) * 1.08

        def at_x(hosts: float, left=left, right=right) -> float:
            return left + hosts / hosts_max * (right - left)

        def at_y(value: float, top_value=top_value) -> float:
            return plot_bottom - value / top_value * (plot_bottom - plot_top)

        money = key == "tco"
        body.append(
            f'<text x="{left:.0f}" y="24" font-size="12" fill="#263238">{_esc(title)}</text>'
        )
        body.append(
            f'<line x1="{left}" y1="{plot_bottom}" x2="{right}" y2="{plot_bottom}" '
            f'stroke="#90a4ae" stroke-width="1"/>'
            f'<line x1="{left}" y1="{plot_top}" x2="{left}" y2="{plot_bottom}" '
            f'stroke="#90a4ae" stroke-width="1"/>'
        )
        for hosts in range(0, hosts_max + 1, 20):
            x = at_x(hosts)
            body.append(
                f'<line x1="{x:.1f}" y1="{plot_bottom}" x2="{x:.1f}" y2="{plot_bottom + 4}" '
                f'stroke="#90a4ae"/>'
                f'<text x="{x:.1f}" y="{plot_bottom + 15}" font-size="{TEXT}" text-anchor="middle" '
                f'fill="#546e7a">{hosts}</text>'
            )
        body.append(
            f'<text x="{(left + right) / 2:.0f}" y="{plot_bottom + 31}" font-size="{TEXT}" '
            f'text-anchor="middle" fill="#546e7a">{_esc(WALL_WORDS["hosts"])}</text>'
        )
        # Every ten kilowatts rather than every five, so the ticks do not crowd at this size.
        step = 1_000_000.0 if money else 10.0
        tick = step
        while tick < top_value:
            y = at_y(tick)
            label = f"${tick / 1e6:.0f}M" if money else f"{tick:.0f} kW"
            body.append(
                f'<line x1="{left - 4}" y1="{y:.1f}" x2="{left}" y2="{y:.1f}" stroke="#90a4ae"/>'
                f'<text x="{left - 6}" y="{y + 3.5:.1f}" font-size="{TEXT}" text-anchor="end" '
                f'fill="#546e7a">{label}</text>'
            )
            tick += step
        points = " ".join(f"{at_x(row['hosts']):.1f},{at_y(row[key]):.1f}" for row in rows)
        body.append(
            f'<polyline points="{points}" fill="none" stroke="#4a7ba7" stroke-width="1.6"/>'
        )
        if not money:
            # Under the dashed line at its right-hand end, where the curve has not reached it.
            y = at_y(allocation)
            body.append(
                f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#b3413a" '
                f'stroke-width="1.4" stroke-dasharray="5 3"/>'
                f'<text x="{right:.0f}" y="{y + 15:.1f}" font-size="10.5" text-anchor="end" '
                f'fill="#b3413a">{_esc(WALL_WORDS["allocation"].format(kw=allocation))}</text>'
            )
        else:
            body.append(
                f'<text x="{right:.0f}" y="{plot_top - 6:.0f}" font-size="{TEXT}" '
                f'text-anchor="end" fill="#546e7a">{_esc(WALL_WORDS["no_wall"])}</text>'
            )
        fit_row, next_row, demand_row = by_hosts[fits], by_hosts.get(fits + 1), by_hosts[demand]

        def value(row, key=key, money=money) -> str:
            return fmt(row[key], "USD") if money else f"{row[key]:.1f} kW"

        # The marked points, and under the panel a key that names each in the same colour.
        key_rows = [
            (fit_row, "#2e7d32", True, WALL_WORDS["fits"].format(n=fits, value=value(fit_row))),
            (
                demand_row,
                "#b3413a",
                True,
                WALL_WORDS["demand"].format(n=demand, value=value(demand_row)),
            ),
        ]
        if not money and next_row is not None:
            key_rows.append((next_row, "#b3413a", False, WALL_WORDS["one_more"].format(n=fits + 1)))
        for i, (row, colour, filled, text) in enumerate(key_rows):
            fill = colour if filled else "#ffffff"
            body.append(
                f'<circle cx="{at_x(row["hosts"]):.1f}" cy="{at_y(row[key]):.1f}" r="4" '
                f'fill="{fill}" stroke="{colour}" stroke-width="1.4"/>'
            )
            ky = plot_bottom + 52 + 16 * i
            body.append(
                f'<circle cx="{left + 4:.1f}" cy="{ky - 3.5:.1f}" r="4" fill="{fill}" '
                f'stroke="{colour}" stroke-width="1.4"/>'
                f'<text x="{left + 14:.1f}" y="{ky:.1f}" font-size="10.5" fill="{colour}">'
                f"{_esc(text)}</text>"
            )
    return _svg(
        width,
        height,
        "".join(body),
        "Facility power and five-year cost against host count, with the allocation as a wall",
    )


#: The power wall's words: the two panel titles, the axis title, the allocation's label, the
#: money panel's note, and the key under each panel. Every number in them is from the sweep.
WALL_WORDS = {
    "watts": "Watts: a wall",
    "money": "Money: a slope",
    "hosts": "hosts in the fleet",
    "allocation": "allocation {kw:g} kW",
    "no_wall": "no wall: a price can be argued with",
    "fits": "fits: {n} hosts, {value}",
    "demand": "demand asked for {n}: {value}",
    "one_more": "one more, {n}: over the wall",
}


#: The label on the seam figure's tick, which marks the upstream median.
SEAM_TICK = "what crosses a seam: the median, {median}"


def seam(result: str, other: str) -> str:
    """Two models' beliefs about one price, on one axis, and the number that crosses between them.

    The observability model buys storage at a price it assumes. The web service model computes
    what a stored terabyte-month costs on its fleet. Same quantity, same unit, each drawn from its
    own stamped histogram on one logarithmic axis, and nothing in the repository joins them. The
    tick is the upstream median: the one number that crosses a seam in practice, and everything
    the upper panel's width says that a number does not.
    """
    upstream = load_result(other)["summary"]["nodes"]["cost_per_stored_tb_month"]
    downstream = load_result(result)["summary"]["nodes"]["storage_price"]
    unit = upstream["unit"]
    width, height = 560.0, 262.0
    plot_left, plot_right = 46.0, width - 24
    panels = ((upstream, "computed", 58.0, 126.0), (downstream, "assumed", 154.0, 222.0))
    low = min(node["histogram"]["edges"][0] for node, *_ in panels)
    high = max(node["histogram"]["edges"][-1] for node, *_ in panels)
    span = math.log10(high / low)

    def at_x(value: float) -> float:
        return plot_left + math.log10(max(value, low) / low) / span * (plot_right - plot_left)

    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">'
        f"One price, two models, no join</text>",
        f'<text x="{MARGIN}" y="34" font-size="{TEXT}" fill="#546e7a">{_esc(unit_label(unit))} '
        f"on a logarithmic axis · each panel from its own stamped result</text>",
    ]
    for node, kind, top, bottom in panels:
        counts, edges, summary = (
            node["histogram"]["counts"],
            node["histogram"]["edges"],
            node["summary"],
        )
        tallest = max(counts) or 1
        for i, count in enumerate(counts):
            x1, x2 = at_x(edges[i]), at_x(edges[i + 1])
            bar = count / tallest * (bottom - top)
            inside = summary["p5"] <= (edges[i] + edges[i + 1]) / 2 <= summary["p95"]
            body.append(
                f'<rect x="{x1:.2f}" y="{bottom - bar:.2f}" '
                f'width="{max(x2 - x1 - 0.3, 0.3):.2f}" height="{bar:.2f}" '
                f'fill="{"#9fc0dd" if inside else "#dde5ec"}"/>'
            )
        body.append(
            f'<line x1="{plot_left}" y1="{bottom}" x2="{plot_right}" y2="{bottom}" '
            f'stroke="#cfd8dc" stroke-width="1"/>'
        )
        label = (
            f"{kind}: {node['label']}, 90% interval {fmt(summary['p5'], unit)} to "
            f"{fmt(summary['p95'], unit)}"
        )
        body.append(
            f'<text x="{plot_left:.0f}" y="{top - 6:.0f}" font-size="{TEXT}" fill="#37474f">'
            f"{_esc(label)}</text>"
        )
    median = upstream["summary"]["p50"]
    x = at_x(median)
    body.append(
        f'<line x1="{x:.1f}" y1="{panels[0][2] - 2:.0f}" x2="{x:.1f}" y2="{panels[1][3]:.0f}" '
        f'stroke="#b3413a" stroke-width="1.2"/>'
        f'<text x="{x - 6:.1f}" y="{panels[1][2] - 18:.0f}" font-size="{TEXT}" text-anchor="end" '
        f'fill="#b3413a">{_esc(SEAM_TICK.format(median=fmt(median, unit)))}</text>'
    )
    axis_y = panels[1][3]
    for value, anchor in _ticks(low, high, True):
        tx = at_x(value)
        body.append(
            f'<line x1="{tx:.1f}" y1="{axis_y}" x2="{tx:.1f}" y2="{axis_y + 4}" stroke="#90a4ae"/>'
            f'<text x="{tx:.1f}" y="{axis_y + 16}" font-size="{TEXT}" text-anchor="{anchor}" '
            f'fill="#546e7a">{_esc(fmt(value, unit))}</text>'
        )
    return _svg(
        width,
        height,
        "".join(body),
        "Two models' distributions for one price on a shared axis, and the single number that "
        "crosses between them",
    )


#: The seller's figure: each curve's colour and dash, by provenance, because that is what each
#: one rests on. The brochure is the vendor's claim; the seller's guesses are assumptions.
SELLER_CURVES = {
    "brochure": ("#c8791a", PROVENANCE_DASH["vendor_claim"], "the brochure: every dollar scales"),
    "bottom_up_assumptions": ("#4a7ba7", "", "the share that scales in {ch22}'s comparison"),
    "sellers_guesses": ("#b3413a", PROVENANCE_DASH["assumption"], "the seller's guess at it"),
}


def seller_transfer(result: str) -> str:
    """The saving for one customer against how much of the benchmark carries over (ch23).

    One line per guess at the share of the spend that scales. Where each line crosses zero is
    that guess's break-even, and it moves further right as the share falls: the less of the bill
    moves with the hosts, the more of the benchmark has to survive. ch22's bottom-up answer is
    the dot, at a transfer of one, because that comparison sized the challenger by its cores.
    """
    from bench.outline import label_of

    summary = load_result(result)["summary"]
    transfers, curves = summary["transfers"], summary["curves"]
    bottom_up = next(row for row in summary["ladder"] if row["key"] == "bottom_up")
    ch22 = label_of("comparing_two_tcos")

    width, height = 440.0, 360.0
    left, right, top, bottom = 20.0, width - 20, 128.0, height - 44
    low_x, high_x = transfers[0], transfers[-1]
    values = [v for curve in curves for v in curve["saving"]] + [0.0, bottom_up["point"]]
    low_y, high_y = min(values), max(values)
    span_y = (high_y - low_y) or 1.0

    def at(transfer: float, saving: float) -> tuple[float, float]:
        return (
            left + (transfer - low_x) / (high_x - low_x) * (right - left),
            bottom - (saving - low_y) / span_y * (bottom - top),
        )

    body = [
        f'<text x="{MARGIN}" y="22" font-size="15" fill="#263238">Five-year saving for '
        f"{_esc(ch22)}'s customer</text>",
        f'<text x="{MARGIN}" y="42" font-size="13.5" fill="#546e7a">against the share of the '
        f"benchmark that carries over</text>",
    ]
    for i, curve in enumerate(curves):
        colour, dash, label = SELLER_CURVES[curve["key"]]
        y = 64 + i * 18
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        body.append(
            f'<line x1="{MARGIN}" y1="{y - 4}" x2="{MARGIN + 22}" y2="{y - 4}" stroke="{colour}" '
            f'stroke-width="2"{dash_attr}/>'
            f'<text x="{MARGIN + 28}" y="{y}" font-size="13.5" fill="#37474f">'
            f"{_esc(label.format(ch22=ch22))}, {curve['scaling_share']:.0%}</text>"
        )
        path = " L".join(
            f"{x:.1f},{yy:.1f}"
            for x, yy in (at(t, s) for t, s in zip(transfers, curve["saving"], strict=True))
        )
        body.append(
            f'<path d="M{path}" fill="none" stroke="{colour}" stroke-width="2"{dash_attr}/>'
        )
        even = curve["break_even_transfer"]
        if low_x <= even <= high_x:
            x, zy = at(even, 0.0)
            body.append(
                f'<circle cx="{x:.1f}" cy="{zy:.1f}" r="3.5" fill="#ffffff" stroke="{colour}" '
                f'stroke-width="1.5"/>'
            )
    # Labels sit where the curves are not: "no saving" above the line at the middle, where every
    # curve but the brochure's is below it and the brochure's is far above.
    _, zy = at(low_x, 0.0)
    mid, _ = at(0.7, 0.0)
    body.append(
        f'<line x1="{left}" y1="{zy:.1f}" x2="{right}" y2="{zy:.1f}" stroke="#263238" '
        f'stroke-width="1"/>'
        f'<text x="{mid:.1f}" y="{zy - 6:.1f}" font-size="13.5" text-anchor="middle" '
        f'fill="#263238">no saving</text>'
    )
    bx, by = at(1.0, bottom_up["point"])
    body.append(
        f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="4.5" fill="#263238"/>'
        f'<text x="{bx - 8:.1f}" y="{by - 10:.1f}" font-size="13.5" text-anchor="end" '
        f'fill="#263238">{_esc(ch22)} bottom-up</text>'
    )
    body.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>')
    for value, anchor in ((low_x, "start"), (0.7, "middle"), (high_x, "end")):
        x, _ = at(value, low_y)
        body.append(
            f'<line x1="{x:.1f}" y1="{bottom}" x2="{x:.1f}" y2="{bottom + 5}" stroke="#90a4ae"/>'
            f'<text x="{x:.1f}" y="{bottom + 21}" font-size="13.5" text-anchor="{anchor}" '
            f'fill="#546e7a">{value:.0%}</text>'
        )
    # The highest saving at the top left, where every curve is low; the lowest at the bottom
    # right, where every curve is near zero.
    _, top_y = at(low_x, high_y)
    _, bottom_y = at(low_x, low_y)
    body.append(
        f'<text x="{left:.1f}" y="{top_y + 4:.1f}" font-size="13.5" fill="#546e7a">'
        f"{_esc(signed_money(high_y))}</text>"
        f'<text x="{right:.1f}" y="{bottom_y - 5:.1f}" font-size="13.5" text-anchor="end" '
        f'fill="#546e7a">{_esc(signed_money(low_y))}</text>'
    )
    body.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 6:.0f}" font-size="13.5" '
        f'text-anchor="middle" fill="#455a64">share of the benchmark that carries over</text>'
    )
    return _svg(width, height, "".join(body), "The seller's saving against the transfer factor")


#: The customer's own spend: a wide light line, the baseline the proposals are read against,
#: so it cannot be mistaken for the blue of ch22's assumptions.
CUSTOMER_LINE = "#bdbdbd"


def seller_by_year(result: str) -> str:
    """Each option's spend added up year by year, for one customer, with the paybacks (ch23).

    The chart a sales TCO leads with, drawn from the same model as the rest of the chapter. The
    customer's own spend starts at nothing; each proposal starts at the cost of the move and
    climbs more slowly, or does not. Where a proposal crosses the customer's line is its payback,
    a break-even in time. The lines are straight because the model is linear in time: a real
    move, with a period of running both systems, bends them.
    """
    from bench.outline import label_of

    summary = load_result(result)["summary"]["by_year"]
    years, current, options = summary["years"], summary["current"], summary["options"]
    ch22 = label_of("comparing_two_tcos")

    width, height = 440.0, 380.0
    left, right, top, bottom = 20.0, width - 20, 146.0, height - 44
    last = years[-1]
    tallest = max([*current, *(v for o in options for v in o["cumulative"])])

    def at(year: float, spend: float) -> tuple[float, float]:
        return (
            left + year / last * (right - left),
            bottom - spend / tallest * (bottom - top),
        )

    def path(values: list[float]) -> str:
        return " L".join(
            f"{x:.1f},{y:.1f}" for x, y in (at(t, v) for t, v in zip(years, values, strict=True))
        )

    body = [
        f'<text x="{MARGIN}" y="22" font-size="15" fill="#263238">Spend added up year by year, '
        f"{_esc(ch22)}'s customer</text>",
        f'<text x="{MARGIN}" y="42" font-size="13.5" fill="#546e7a">each proposal starts at the '
        f"cost of the move</text>",
    ]
    legend = [(CUSTOMER_LINE, "", "the customer as it is")] + [
        (SELLER_CURVES[o["key"]][0], SELLER_CURVES[o["key"]][1], _seller_payback_label(o, ch22))
        for o in options
    ]
    for i, (colour, dash, label) in enumerate(legend):
        y = 64 + i * 18
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        body.append(
            f'<line x1="{MARGIN}" y1="{y - 4}" x2="{MARGIN + 22}" y2="{y - 4}" stroke="{colour}" '
            f'stroke-width="{4 if colour == CUSTOMER_LINE else 2}"{dash_attr}/>'
            f'<text x="{MARGIN + 28}" y="{y}" font-size="13.5" fill="#37474f">{_esc(label)}</text>'
        )
    body.append(
        f'<path d="M{path(current)}" fill="none" stroke="{CUSTOMER_LINE}" stroke-width="4"/>'
    )
    for option in options:
        colour, dash, _ = SELLER_CURVES[option["key"]]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        body.append(
            f'<path d="M{path(option["cumulative"])}" fill="none" stroke="{colour}" '
            f'stroke-width="2"{dash_attr}/>'
        )
        payback = option["payback"]
        if 0 < payback <= last:
            x, y = at(payback, current[1] * payback)
            body.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#ffffff" stroke="{colour}" '
                f'stroke-width="1.6"/>'
            )
    body.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>')
    for year in years:
        x, _ = at(year, 0)
        anchor = "start" if year == 0 else "end" if year == last else "middle"
        body.append(
            f'<line x1="{x:.1f}" y1="{bottom}" x2="{x:.1f}" y2="{bottom + 5}" stroke="#90a4ae"/>'
            f'<text x="{x:.1f}" y="{bottom + 21}" font-size="13.5" text-anchor="{anchor}" '
            f'fill="#546e7a">{year}</text>'
        )
    _, top_y = at(0, tallest)
    body.append(
        f'<text x="{left:.1f}" y="{top_y + 4:.1f}" font-size="13.5" fill="#546e7a">'
        f"{_esc(fmt(tallest, 'USD'))}</text>"
        f'<text x="{(left + right) / 2:.0f}" y="{height - 6:.0f}" font-size="13.5" '
        f'text-anchor="middle" fill="#455a64">years after the move</text>'
    )
    return _svg(width, height, "".join(body), "Spend added up year by year, with the paybacks")


def _seller_payback_label(option: dict, ch22: str) -> str:
    """A proposal's legend entry: whose assumptions, and when it pays back, or that it never does."""
    who = {
        "brochure": "the brochure",
        "bottom_up_assumptions": f"{ch22}'s two assumptions",
        "sellers_guesses": "the seller's guesses",
    }[option["key"]]
    payback = option["payback"]
    if payback <= 0:
        return f"{who}: never pays back"
    return f"{who}: pays back after {payback:.1f} years"


#: The parts of a proposal's five-year spend, bottom to top, and their fills.
SELLER_PARTS = (
    ("stays", "#bdbdbd", "today's spend that stays"),
    ("proposed_hosts", "#5b8fb9", "the proposed hosts"),
    ("move", "#c98a6b", "the move"),
)


def seller_breakdown(result: str) -> str:
    """Where each proposal's five-year spend goes, against the customer's own total (ch23).

    One bar per setting of the two hidden assumptions. The line across is what the customer
    spends as it is, so a bar below it is a saving and the gap is its size. The brochure's bar
    has no grey block: it scaled the whole bill, people included, and so assumed they go away.
    """
    from bench.outline import label_of

    summary = load_result(result)["summary"]["breakdown"]
    current, options = summary["current"], summary["options"]
    ch22 = label_of("comparing_two_tcos")
    names = {
        "brochure": ("the", "brochure"),
        "bottom_up_assumptions": (f"{ch22}'s", "assumptions"),
        "sellers_guesses": ("the seller's", "guesses"),
    }

    width, height = 440.0, 380.0
    left, right, top, bottom = 20.0, width - 20, 140.0, height - 50
    totals = [sum(o[p] for p, _, _ in SELLER_PARTS) for o in options]
    tallest = max([current, *totals]) * 1.08

    def y_of(value: float) -> float:
        return bottom - value / tallest * (bottom - top)

    body = [
        f'<text x="{MARGIN}" y="22" font-size="15" fill="#263238">Five-year spend, '
        f"{_esc(ch22)}'s customer</text>",
    ]
    for i, (_, fill, label) in enumerate(SELLER_PARTS):
        y = 46 + i * 18
        body.append(
            f'<rect x="{MARGIN}" y="{y - 10}" width="11" height="11" fill="{fill}"/>'
            f'<text x="{MARGIN + 17}" y="{y}" font-size="13.5" fill="#37474f">{_esc(label)}</text>'
        )
    y = 46 + len(SELLER_PARTS) * 18
    body.append(
        f'<line x1="{MARGIN}" y1="{y - 4}" x2="{MARGIN + 11}" y2="{y - 4}" stroke="#263238" '
        f'stroke-width="1.4" stroke-dasharray="5 3"/>'
        f'<text x="{MARGIN + 17}" y="{y}" font-size="13.5" fill="#37474f">'
        f"the customer as it is, {_esc(fmt(current, 'USD'))}</text>"
    )
    slot = (right - left) / len(options)
    bar = slot * 0.46
    for i, (option, total) in enumerate(zip(options, totals, strict=True)):
        x = left + slot * i + (slot - bar) / 2
        base = 0.0
        for part, fill, _ in SELLER_PARTS:
            value = option[part]
            if value <= 0:
                continue
            body.append(
                f'<rect x="{x:.1f}" y="{y_of(base + value):.1f}" width="{bar:.1f}" '
                f'height="{y_of(base) - y_of(base + value) - 2:.1f}" fill="{fill}"/>'
            )
            base += value
        gap = current - total
        body.append(
            f'<text x="{x + bar / 2:.1f}" y="{y_of(total) - 6:.1f}" font-size="13.5" '
            f'text-anchor="middle" fill="#263238">{_esc(signed_money(gap))}</text>'
        )
        first, second = names[option["key"]]
        for j, word in enumerate((first, second)):
            body.append(
                f'<text x="{x + bar / 2:.1f}" y="{bottom + 18 + 16 * j}" font-size="13.5" '
                f'text-anchor="middle" fill="#455a64">{_esc(word)}</text>'
            )
    line_y = y_of(current)
    body.append(
        f'<line x1="{left}" y1="{line_y:.1f}" x2="{right}" y2="{line_y:.1f}" stroke="#263238" '
        f'stroke-width="1.4" stroke-dasharray="5 3"/>'
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>'
    )
    return _svg(width, height, "".join(body), "Where each proposal's five-year spend goes")


#: The break-even map's three marked settings: colour, and the legend's words.
SELLER_POINTS = {
    "brochure": ("#c8791a", "the brochure"),
    "bottom_up_assumptions": ("#4a7ba7", "{ch22}'s two assumptions"),
    "sellers_guesses": ("#b3413a", "the seller's guesses, at their middle"),
}


def seller_plane(result: str) -> str:
    """The two hidden assumptions as a plane, split where the saving is zero (ch23).

    Right of the line the product pays for ch22's customer; left of it, it loses. The dots are
    a few hundred of the seller's own futures, so the share of them on the paying side is how
    often the seller's own guesses say the product pays. The break-even is a line, not a number:
    any pair of assumptions on it ties.
    """
    from bench.outline import label_of

    plane = load_result(result)["summary"]["plane"]
    ch22 = label_of("comparing_two_tcos")
    width, height = 440.0, 420.0
    left, right, top, bottom = 76.0, width - 20, 118.0, height - 56
    x_low, x_high, y_low, y_high = 0.4, 1.2, 0.2, 1.0

    def at(transfer: float, share: float) -> tuple[float, float]:
        return (
            left + (transfer - x_low) / (x_high - x_low) * (right - left),
            bottom - (share - y_low) / (y_high - y_low) * (bottom - top),
        )

    body = [
        f'<text x="{MARGIN}" y="22" font-size="15" fill="#263238">Where the product pays, '
        f"{_esc(ch22)}'s customer</text>",
    ]
    for i, (colour, label) in enumerate(SELLER_POINTS.values()):
        y = 46 + i * 18
        body.append(
            f'<circle cx="{MARGIN + 5}" cy="{y - 4}" r="5" fill="{colour}"/>'
            f'<text x="{MARGIN + 17}" y="{y}" font-size="13.5" fill="#37474f">'
            f"{_esc(label.format(ch22=ch22))}</text>"
        )
    # The paying side: every point right of the boundary, clipped to the plot.
    edge = [
        at(min(max(p["break_even_transfer"], x_low), x_high), p["scaling_share"])
        for p in plane["boundary"]
        if p["break_even_transfer"] > 0
    ]
    region = [*edge, at(x_high, y_high), at(x_high, plane["boundary"][0]["scaling_share"])]
    body.append(
        '<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in region) + '" fill="#dde5ec"/>'
    )
    line = [
        at(p["break_even_transfer"], p["scaling_share"])
        for p in plane["boundary"]
        if x_low <= p["break_even_transfer"] <= x_high
    ]
    body.append(
        '<path d="M'
        + " L".join(f"{x:.1f},{y:.1f}" for x, y in line)
        + '" fill="none" stroke="#263238" stroke-width="1.6"/>'
    )
    cloud = plane["cloud"]
    for transfer, share in zip(cloud["transfer_factor"], cloud["scaling_share"], strict=True):
        x, y = at(transfer, share)
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="#78909c"/>')
    for point in plane["points"]:
        colour, _ = SELLER_POINTS[point["key"]]
        x, y = at(point["transfer_factor"], point["scaling_share"])
        body.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{colour}" stroke="#ffffff" '
            f'stroke-width="1.5"/>'
        )
    lx, ly = at(1.18, 0.92)
    body.append(
        f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="13.5" text-anchor="end" fill="#263238">'
        f"pays</text>"
    )
    lx, ly = at(0.42, 0.23)
    body.append(
        f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="13.5" fill="#263238">loses</text>'
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#90a4ae"/>'
    )
    for value, anchor in ((x_low, "start"), (0.8, "middle"), (x_high, "end")):
        x, _ = at(value, y_low)
        body.append(
            f'<text x="{x:.1f}" y="{bottom + 18}" font-size="13.5" text-anchor="{anchor}" '
            f'fill="#546e7a">{value:.0%}</text>'
        )
    for value in (y_low, 0.6, y_high):
        _, y = at(x_low, value)
        body.append(
            f'<text x="{left - 4}" y="{y + 4:.1f}" font-size="13.5" text-anchor="end" '
            f'fill="#546e7a">{value:.0%}</text>'
        )
    body.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 16:.0f}" font-size="13.5" '
        f'text-anchor="middle" fill="#455a64">share of the benchmark that carries over</text>'
        f'<text transform="rotate(-90 16 {(top + bottom) / 2:.0f})" x="16" '
        f'y="{(top + bottom) / 2:.0f}" font-size="13.5" text-anchor="middle" fill="#455a64">'
        f"share of the spend that scales</text>"
    )
    return _svg(width, height, "".join(body), "Where the product pays, by the two assumptions")
