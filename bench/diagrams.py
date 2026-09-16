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
the same thing as the fills, because the PDF is printed and the fills are not.
"""

from __future__ import annotations

import html
import math

from bench.stamp import load_result
from bench.tables import fmt, unit_label

#: Node kinds, by fill. The distinction the whole book rests on is visible here: a model with no
#: amber and no red in it is a cost model, and one with either is a sizing model.
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
PROVENANCE_DASH = {"fact": "", "vendor_claim": "4 2", "assumption": "2 3"}

COLUMN_WIDTH = 188
ROW_HEIGHT = 46
BOX_WIDTH = 154
BOX_HEIGHT = 32
MARGIN = 16


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


def _wrap(text: str, width: int = 22) -> list[str]:
    """Break a label into at most two lines, because a box is a box."""
    words, lines, current = str(text).split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
        if len(lines) == 2:
            break
    if current and len(lines) < 2:
        lines.append(current)
    if len(lines) == 2 and len(words) > len(" ".join(lines).split()):
        lines[1] = lines[1][: width - 1] + "…"
    return [line for line in lines if line]


# -- the dependency graph -------------------------------------------------------------------


def dependency_graph(result: str, focus: str | None = None) -> str:
    """The model as a graph, coloured by node kind, arrows pointing from cause to effect.

    With ``focus``, everything that does not feed that output is faded: the sub-graph that
    produced one number, which on a fifty-node model is the difference between a picture and a
    diagram. The interactive version does the same thing on a click; this is the printable one.
    """
    payload = load_result(result)["summary"]
    nodes = payload["nodes"]
    keep = _ancestry(payload, focus) if focus else set(nodes)

    columns = max(node["layer"] for node in nodes.values()) + 1
    rows = max(node["row"] for node in nodes.values()) + 1
    width = MARGIN * 2 + columns * COLUMN_WIDTH
    height = MARGIN * 2 + rows * ROW_HEIGHT + 34

    def centre(name: str) -> tuple[float, float]:
        node = nodes[name]
        return (
            MARGIN + node["layer"] * COLUMN_WIDTH + BOX_WIDTH / 2,
            MARGIN + 34 + node["row"] * ROW_HEIGHT + BOX_HEIGHT / 2,
        )

    edges = []
    for name, node in sorted(nodes.items()):
        for parent in node["depends_on"]:
            lit = name in keep and parent in keep
            x1, y1 = centre(parent)
            x2, y2 = centre(name)
            x1 += BOX_WIDTH / 2
            x2 -= BOX_WIDTH / 2
            mid = (x1 + x2) / 2
            edges.append(
                f'<path d="M{x1:.1f},{y1:.1f} C{mid:.1f},{y1:.1f} {mid:.1f},{y2:.1f} '
                f'{x2:.1f},{y2:.1f}" fill="none" stroke="{"#607d8b" if lit else "#e4e7e9"}" '
                f'stroke-width="{1.1 if lit else 0.7}"/>'
            )

    boxes = []
    for name, node in sorted(nodes.items()):
        x = MARGIN + node["layer"] * COLUMN_WIDTH
        y = MARGIN + 34 + node["row"] * ROW_HEIGHT
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
        unmeasured = node["kind"] == "measured" and not node.get("measured")
        if unmeasured:
            fill, dash = "#ffffff", ' stroke-dasharray="3 3"'
        boxes.append(
            f'<rect x="{x}" y="{y}" width="{BOX_WIDTH}" height="{BOX_HEIGHT}" rx="3" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.2"{dash}/>'
        )
        lines = _wrap(node["label"])
        for i, line in enumerate(lines):
            offset = 13 if len(lines) == 1 else 9 + i * 11
            boxes.append(
                f'<text x="{x + 6}" y="{y + offset + 6}" font-size="9.5" '
                f'fill="{"#263238" if lit else "#bdbdbd"}">{_esc(line)}</text>'
            )
        if unmeasured:
            boxes.append(
                f'<text x="{x + BOX_WIDTH - 6}" y="{y + BOX_HEIGHT - 5}" font-size="8" '
                f'text-anchor="end" fill="#b3413a">not measured</text>'
            )

    legend = _legend(MARGIN, MARGIN + 8)
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


def _legend(x: float, y: float) -> str:
    out, offset = [], 0.0
    for kind in ("input", "derived", "measured", "ceiling"):
        out.append(
            f'<rect x="{x + offset}" y="{y}" width="13" height="10" rx="2" '
            f'fill="{KIND_FILL[kind]}" stroke="{KIND_STROKE[kind]}"/>'
            f'<text x="{x + offset + 17}" y="{y + 9}" font-size="9.5" fill="#455a64">{kind}</text>'
        )
        offset += 24 + len(kind) * 5.6
    return "".join(out)


# -- tornado ----------------------------------------------------------------------------------


def tornado_chart(result: str, output: str, limit: int = 9) -> str:
    """How far one output moves when each uncertain input is swung across its middle 80%.

    Sorted by swing, longest at the top, which is the only ordering that answers the question
    people bring to a tornado: *what should I go and measure first?*
    """
    payload = load_result(result)["summary"]
    bars = payload["tornado"].get(output, [])[:limit]
    node = payload["nodes"][output]
    if not bars:
        return _svg(360, 40, '<text x="8" y="24" font-size="11">no uncertain input</text>', "empty")

    label_width, chart_width, bar_height = 168.0, 300.0, 24.0
    width = label_width + chart_width + MARGIN * 2 + 96
    height = MARGIN * 2 + 42 + len(bars) * bar_height

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
        f'y2="{height - MARGIN:.0f}" stroke="#455a64" stroke-width="1" stroke-dasharray="3 2"/>',
    ]
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
            f'<text x="{MARGIN + label_width - 8}" y="{y + 12}" font-size="9.5" '
            f'text-anchor="end" fill="#263238">{_esc(bar["label"])}</text>'
        )
        body.append(
            f'<text x="{MARGIN + label_width + chart_width + 8}" y="{y + 12}" font-size="9" '
            f'fill="#546e7a">{_esc(fmt(bar["span"], node["unit"]))}</text>'
        )
    return _svg(width, height, "".join(body), f"Tornado for {node['label']}")


# -- a distribution ------------------------------------------------------------------------


def distribution(result: str, node_name: str) -> str:
    """One node's sampled distribution, with the interval and the point estimate on it.

    The point estimate is drawn as a line through the histogram deliberately. Seeing where the
    single number a plan was built on actually sits in the distribution it came from is the whole
    of ch13's argument, and it is much harder to argue with than a paragraph.
    """
    payload = load_result(result)["summary"]
    node = payload["nodes"][node_name]
    histogram, summary = node.get("histogram"), node.get("summary")
    if not histogram or not summary:
        return _svg(
            360, 40, '<text x="8" y="24" font-size="11">this node does not vary</text>', "fixed"
        )

    width, height = 520.0, 220.0
    plot_left, plot_right, plot_top, plot_bottom = 46.0, width - 16, 44.0, height - 40
    counts, edges = histogram["counts"], histogram["edges"]
    low, high = edges[0], edges[-1]
    span = (high - low) or 1.0
    tallest = max(counts) or 1

    def at_x(value: float) -> float:
        return plot_left + (value - low) / span * (plot_right - plot_left)

    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">'
        f"{_esc(node['label'])} — {payload['scenario']['samples']:,} samples</text>",
        f'<text x="{MARGIN}" y="34" font-size="9.5" fill="#546e7a">'
        f"90% interval {_esc(fmt(summary['p5'], node['unit']))} to "
        f"{_esc(fmt(summary['p95'], node['unit']))} · median "
        f"{_esc(fmt(summary['p50'], node['unit']))}</text>",
    ]
    for i, count in enumerate(counts):
        x1, x2 = at_x(edges[i]), at_x(edges[i + 1])
        bar = (count / tallest) * (plot_bottom - plot_top)
        inside = summary["p5"] <= (edges[i] + edges[i + 1]) / 2 <= summary["p95"]
        body.append(
            f'<rect x="{x1:.2f}" y="{plot_bottom - bar:.2f}" width="{max(x2 - x1 - 0.4, 0.4):.2f}" '
            f'height="{bar:.2f}" fill="{"#9fc0dd" if inside else "#dde5ec"}"/>'
        )
    for value, colour, label in (
        (summary["p5"], "#455a64", "p5"),
        (summary["p95"], "#455a64", "p95"),
        (node.get("point"), "#b3413a", "point"),
    ):
        if value is None or not low <= value <= high:
            continue
        dash = "" if label == "point" else ' stroke-dasharray="3 2"'
        x = at_x(value)
        body.append(
            f'<line x1="{x:.1f}" y1="{plot_top - 4:.0f}" x2="{x:.1f}" '
            f'y2="{plot_bottom:.0f}" stroke="{colour}" stroke-width="1.2"{dash}/>'
            f'<text x="{x:.1f}" y="{plot_top - 8:.0f}" font-size="8.5" '
            f'text-anchor="middle" fill="{colour}">{label}</text>'
        )
    body.append(
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" '
        f'stroke="#90a4ae" stroke-width="1"/>'
    )
    for fraction in (0.0, 0.5, 1.0):
        value = low + fraction * span
        x = at_x(value)
        body.append(
            f'<line x1="{x:.1f}" y1="{plot_bottom}" x2="{x:.1f}" y2="{plot_bottom + 4}" '
            f'stroke="#90a4ae"/>'
            f'<text x="{x:.1f}" y="{plot_bottom + 16}" font-size="8.5" text-anchor="middle" '
            f'fill="#546e7a">{_esc(fmt(value, node["unit"]))}</text>'
        )
    return _svg(width, height, "".join(body), f"Distribution of {node['label']}")


# -- convergence ------------------------------------------------------------------------------


def convergence(result: str) -> str:
    """Interval half-width against sample count, with the one-over-root-n law drawn beside it.

    ch14 shows this rather than asserting it. The measured points and the law are drawn on the
    same axes so the reader can see how well it holds, including where it does not.
    """
    payload = load_result(result)["summary"]
    points = payload["convergence"]
    width, height = 470.0, 230.0
    left, right, top, bottom = 58.0, width - 18, 34.0, height - 38

    counts = [p["samples"] for p in points]
    widths = [p["half_width"] for p in points]
    log_n = [math.log10(c) for c in counts]
    log_w = [math.log10(w) for w in widths]
    x_low, x_high = min(log_n), max(log_n)
    y_low, y_high = min(log_w) - 0.1, max(log_w) + 0.1

    def at(lx: float, ly: float) -> tuple[float, float]:
        return (
            left + (lx - x_low) / (x_high - x_low or 1) * (right - left),
            bottom - (ly - y_low) / (y_high - y_low or 1) * (bottom - top),
        )

    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">Half-width of the 90% '
        f"interval against sample count (both axes logarithmic)</text>"
    ]
    # The law: half-width proportional to one over the square root of n, anchored at the first
    # measured point, so the comparison is a shape rather than a fitted line.
    law = [(lx, log_w[0] - 0.5 * (lx - log_n[0])) for lx in (x_low, x_high)]
    body.append(
        '<path d="M'
        + " L".join(f"{x:.1f},{y:.1f}" for x, y in (at(*pair) for pair in law))
        + '" fill="none" stroke="#b3413a" stroke-width="1.2" stroke-dasharray="4 3"/>'
    )
    path = " L".join(
        f"{x:.1f},{y:.1f}" for x, y in (at(lx, ly) for lx, ly in zip(log_n, log_w, strict=True))
    )
    body.append(f'<path d="M{path}" fill="none" stroke="#4a7ba7" stroke-width="1.6"/>')
    for lx, ly, count in zip(log_n, log_w, counts, strict=True):
        x, y = at(lx, ly)
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#4a7ba7"/>')
        body.append(
            f'<text x="{x:.1f}" y="{bottom + 14:.0f}" font-size="8.5" text-anchor="middle" '
            f'fill="#546e7a">{count:,}</text>'
        )
    body.append(
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#90a4ae"/>'
        f'<text x="{right}" y="{top + 2:.0f}" font-size="9" text-anchor="end" fill="#b3413a">'
        f"one over the square root of n</text>"
    )
    return _svg(width, height, "".join(body), "Monte Carlo convergence")


# -- Part II's two shapes ----------------------------------------------------------------


def queueing_curve(result: str) -> str:
    """Residence time against utilisation: flat, and then vertical.

    Drawn on linear axes on purpose. A logarithmic vertical axis would make this curve look like
    a gentle slope, which is how most people have seen it and is the reason most people are
    surprised by it in production. The shape is the argument, and flattening the shape to fit the
    page would be flattening the argument.
    """
    rows = load_result(result)["summary"]["curve"]
    width, height = 500.0, 250.0
    left, right, top, bottom = 52.0, width - 20, 40.0, height - 42

    inflations = [row["inflation"] for row in rows]
    ceiling_value = max(inflations)

    def at(utilisation: float, inflation: float) -> tuple[float, float]:
        return (
            left + utilisation * (right - left),
            bottom - (inflation - 1.0) / (ceiling_value - 1.0) * (bottom - top),
        )

    path = " L".join(
        f"{x:.1f},{y:.1f}" for x, y in (at(row["utilisation"], row["inflation"]) for row in rows)
    )
    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">How much longer a request '
        f"takes than it would on an idle tier</text>",
        f'<text x="{MARGIN}" y="34" font-size="9.5" fill="#546e7a">The arrival rate moves; the '
        f"software and the machines do not</text>",
    ]
    # Where a sensible headroom rule would put you, so the curve is read against a decision
    # rather than admired.
    for mark, label, colour in ((0.7, "a 30% margin ends here", "#c8791a"), (0.9, "", "#b3413a")):
        x = left + mark * (right - left)
        body.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" stroke="{colour}" '
            f'stroke-width="1" stroke-dasharray="3 3"/>'
        )
        if label:
            body.append(
                f'<text x="{x - 6:.1f}" y="{top + 12:.0f}" font-size="9" text-anchor="end" '
                f'fill="{colour}">{_esc(label)}</text>'
            )
    body.append(f'<path d="M{path}" fill="none" stroke="#4a7ba7" stroke-width="2"/>')
    for row in rows:
        x, y = at(row["utilisation"], row["inflation"])
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="#4a7ba7"/>')

    body.append(
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#90a4ae"/>'
    )
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        x = left + fraction * (right - left)
        body.append(
            f'<text x="{x:.1f}" y="{bottom + 15:.0f}" font-size="9" text-anchor="middle" '
            f'fill="#546e7a">{fraction:.0%}</text>'
        )
    for value in (1.0, ceiling_value / 2, ceiling_value):
        y = bottom - (value - 1.0) / (ceiling_value - 1.0) * (bottom - top)
        body.append(
            f'<text x="{left - 6:.0f}" y="{y + 3:.1f}" font-size="9" text-anchor="end" '
            f'fill="#546e7a">{value:.0f}x</text>'
        )
    body.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 8:.0f}" font-size="9.5" '
        f'text-anchor="middle" fill="#455a64">utilisation</text>'
    )
    return _svg(width, height, "".join(body), "Residence time against utilisation")


def scaling_curve(result: str) -> str:
    """Throughput against node count, against the straight line nobody gets.

    Two curves and the gap between them. The straight line is what a budget assumes; the other is
    what the machines do. The place they stop diverging and start converging on nothing is the
    peak, and the peak is a property of the software.
    """
    summary = load_result(result)["summary"]
    rows = summary["curve"]
    width, height = 500.0, 260.0
    left, right, top, bottom = 56.0, width - 20, 42.0, height - 42

    most_nodes = max(row["nodes"] for row in rows)
    # Scaled to what the tier can actually reach, not to the straight line — which is nine times
    # taller and would squash the real curve onto the axis. So the line a budget assumes runs off
    # the top of the figure, which is a fair description of what it does in practice.
    tallest = max(row["achievable_throughput"] for row in rows) * 1.35

    def at(nodes: float, throughput: float) -> tuple[float, float]:
        return (
            left + nodes / most_nodes * (right - left),
            bottom - min(throughput / tallest, 1.0) * (bottom - top),
        )

    def path_of(key: str) -> str:
        return " L".join(f"{x:.1f},{y:.1f}" for x, y in (at(r["nodes"], r[key]) for r in rows))

    leaves_at = next(
        (row["nodes"] for row in rows if row["linear_throughput"] > tallest), most_nodes
    )

    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">What more machines actually '
        f"buy</text>",
        f'<text x="{MARGIN}" y="34" font-size="9.5" fill="#546e7a">The straight line is what a '
        f"budget assumes. The curve is what the machines do</text>",
        f'<path d="M{path_of("linear_throughput")}" fill="none" stroke="#b3413a" '
        f'stroke-width="1.2" stroke-dasharray="4 3"/>',
        f'<path d="M{path_of("achievable_throughput")}" fill="none" stroke="#4a7ba7" '
        f'stroke-width="2"/>',
    ]
    exit_x, _ = at(leaves_at, tallest)
    body.append(
        f'<text x="{exit_x + 6:.1f}" y="{top + 12:.0f}" font-size="9" fill="#b3413a">'
        f"the budget's line leaves the page at {leaves_at:.0f} nodes</text>"
    )

    peak = max(rows, key=lambda row: row["achievable_throughput"])
    peak_x, peak_y = at(peak["nodes"], peak["achievable_throughput"])
    body.append(
        f'<circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="4" fill="none" stroke="#b3413a" '
        f'stroke-width="1.5"/>'
        f'<text x="{peak_x:.1f}" y="{peak_y - 10:.1f}" font-size="9" text-anchor="middle" '
        f'fill="#b3413a">past here it falls</text>'
    )
    body.append(
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#90a4ae"/>'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#90a4ae"/>'
    )
    for row in rows:
        if row["nodes"] not in (1, 64, 128, 256, most_nodes):
            continue
        x, _ = at(row["nodes"], 0)
        body.append(
            f'<text x="{x:.1f}" y="{bottom + 15:.0f}" font-size="9" text-anchor="middle" '
            f'fill="#546e7a">{row["nodes"]:.0f}</text>'
        )
    body.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 8:.0f}" font-size="9.5" '
        f'text-anchor="middle" fill="#455a64">nodes</text>'
        f'<text x="{left - 6:.0f}" y="{top + 4:.0f}" font-size="9" text-anchor="end" '
        f'fill="#546e7a">{tallest / 1000:.0f}k</text>'
        f'<text x="{left - 6:.0f}" y="{bottom:.0f}" font-size="9" text-anchor="end" '
        f'fill="#546e7a">0</text>'
        f'<text x="{right:.0f}" y="{height - 8:.0f}" font-size="9" text-anchor="end" '
        f'fill="#546e7a">requests per second</text>'
    )
    return _svg(width, height, "".join(body), "Throughput against node count")


def distribution_shapes(_result: str | None = None) -> str:
    """The four shapes this book uses, drawn from their own percentile functions.

    Not illustrations of distributions — these are the actual functions in ``sizing/mc.py``,
    sampled at a thousand percentiles and plotted. If somebody changes one, this picture changes,
    which is the only kind of figure this book is willing to print.

    All four are scaled onto the same horizontal range so the *shapes* can be compared. Their
    parameters are chosen to put roughly the same mass in the same place, which is the fair
    comparison: the question is never "which is wider" but "which is the right claim about what
    can happen".
    """
    import numpy as np

    from sizing import mc

    width, height = 520.0, 300.0
    left, right = 54.0, width - 16
    panel = 62.0
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

    body = [
        f'<text x="{MARGIN}" y="20" font-size="11.5" fill="#263238">The four shapes, drawn from '
        f"the percentile functions the sampler actually uses</text>"
    ]
    for index, (name, values, caption) in enumerate(shapes):
        top = 34.0 + index * panel
        base = top + panel - 20
        counts, edges = np.histogram(values, bins=70, range=(low, high))
        tallest = max(counts.max(), 1)
        for i, count in enumerate(counts):
            x1 = left + (edges[i] - low) / span * (right - left)
            x2 = left + (edges[i + 1] - low) / span * (right - left)
            bar = (count / tallest) * (base - top)
            body.append(
                f'<rect x="{x1:.2f}" y="{base - bar:.2f}" width="{max(x2 - x1 - 0.4, 0.4):.2f}" '
                f'height="{bar:.2f}" fill="#9fc0dd"/>'
            )
        body.append(
            f'<line x1="{left}" y1="{base:.1f}" x2="{right}" y2="{base:.1f}" stroke="#90a4ae"/>'
            f'<text x="{MARGIN}" y="{top + 12:.0f}" font-size="10" fill="#263238">{_esc(name)}</text>'
            f'<text x="{MARGIN}" y="{top + 24:.0f}" font-size="8" fill="#78909c">'
            f"{_esc(caption)}</text>"
        )
    return _svg(width, height, "".join(body), "The four distributions this book uses")
