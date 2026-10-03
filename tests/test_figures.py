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
        two = ("scenario_comparison", "scenario_ratios", "breach_comparison", "scenario_decision")
        if not isinstance(figure, Table) or figure.render.__name__ not in two:
            continue
        other = figure.args[0] if figure.args else None
        assert other in figure.also, (
            f"figure {name!r} compares against {other!r} and does not list it in `also`, so its "
            "conditions line names one of the two results its columns come from."
        )


def test_the_unmeasured_box_counts_what_waits_not_what_is_missing():
    """A missing constant lists itself in its own ``blocked_by``, so counting every node with one
    counted the two observability constants as their own downstream: eight where six wait."""
    from bench.stamp import load_result
    from bench.tables import not_yet_measured

    for path in sorted((ROOT / "bench" / "results").glob("*.json")):
        payload = load_result(path.stem).get("summary") or {}
        missing = payload.get("unmeasured") or []
        if not missing:
            continue
        waiting = [
            name
            for name, node in payload["nodes"].items()
            if node.get("blocked_by") and name not in missing
        ]
        assert f"\n{len(waiting)} node(s) downstream" in not_yet_measured(path.stem), (
            f"{path.stem}: the box does not count the {len(waiting)} node(s) that wait on "
            "the missing constants"
        )


def test_two_scenarios_of_one_model_count_its_missing_constants_once():
    """The scenarios table names two runs of the observability model, which share their two
    missing constants; the Source line said four."""
    from bench.stamp import load_result
    from bench.tables import source

    one = load_result("observability-reference")["produced_by"]["unmeasured"]
    both = source("observability-reference", "observability-knobs_turned_down")
    assert one and f"**{len(one)} constant(s) not yet measured**" in both, both


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
        name
        for name in DECLARED
        if f"{name}.md" not in pages
        and f"{name}.svg" not in pages
        # An explorer is placed by an empty box that names it (bench/render.py).
        and f":class: explorer {name}" not in pages
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


def test_every_colour_a_figure_is_drawn_in_has_one_for_the_dark():
    """A figure is drawn once, in daylight, and read in both.

    The figures go into the page inline, so the stylesheet reaches every fill and stroke in
    them and `scripts/build-site.py` swaps each colour for a dark counterpart. A colour with no
    counterpart stays as it was drawn, which on a dark page is a white slab or a black label on
    a dark panel. The book had 38 of those. This is what stops the thirty-ninth.
    """
    from bench.diagrams import DARK_FIGURE

    used: dict[str, str] = {}
    for path in sorted((ROOT / "chapters" / "_figures").glob("*.svg")):
        for colour in re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,8})"', path.read_text()):
            used.setdefault(colour.lower(), path.name)
    missing = {colour: where for colour, where in used.items() if colour not in DARK_FIGURE}
    assert not missing, (
        "these are drawn in colours bench.diagrams.DARK_FIGURE does not name, so they keep "
        "them on a dark page:\n  "
        + "\n  ".join(f"{colour} first in {where}" for colour, where in sorted(missing.items()))
    )


# -- the book's smallest text, and the graph's key -----------------------------------------------


@pytest.mark.parametrize("path", FIGURES, ids=lambda p: p.name)
def test_no_text_is_smaller_than_the_floor(path):
    """A figure is inlined at its natural width wherever the column has room, so a label drawn
    at eight and a half units is read at eight and a half pixels: under the nine the review
    flags, on a desktop, where nothing squeezed it."""
    from bench.diagrams import TEXT

    sizes = [float(size) for size in re.findall(r'font-size="([0-9.]+)"', path.read_text())]
    assert all(size >= TEXT for size in sizes), (
        f"{path.name} prints text at {min(sizes)} units; bench.diagrams.TEXT ({TEXT}) is the "
        "smallest any figure may use."
    )


def _graph(**kwargs) -> str:
    from bench.diagrams import dependency_graph

    return dependency_graph("web_service_littles_law-reference", **kwargs)


def test_every_edge_in_a_graph_has_a_head():
    """The docstring says arrows point from cause to effect; a line with no head says neither."""
    svg = _graph()
    assert svg.count("<path ") == svg.count("<polygon "), "an edge was drawn without its head"
    assert "marker" not in svg, (
        "a marker needs an id, and every figure on a page shares one document"
    )


def test_the_you_decide_bar_is_one_colour_in_the_graph_and_its_key():
    """The bar used to take the box's border colour, which is the input's provenance, so no bar
    on any box matched the blue one in the legend."""
    from bench.diagrams import DECIDED_BAR

    svg = _graph()
    bars = re.findall(
        r'<rect x="[^"]*" y="[^"]*" width="3" height="[^"]*" rx="1.5" fill="([^"]*)"', svg
    )
    assert len(bars) >= 2, "the key and at least one chosen input each carry the bar"
    assert set(bars) == {DECIDED_BAR}


def test_the_key_says_what_an_input_border_means():
    from bench.diagrams import PROVENANCE_STROKE

    svg = _graph()
    for kind, colour in PROVENANCE_STROKE.items():
        assert f">{kind.replace('_', ' ')}</text>" in svg, kind
        assert f'stroke="{colour}"' in svg, kind


def test_a_graph_drawn_for_one_output_alone_leaves_out_what_does_not_feed_it():
    """Faded nodes cost columns, and columns cost the labels their size."""
    from bench.stamp import load_result

    whole = _graph(focus="in_flight_unqueued")
    alone = _graph(focus="in_flight_unqueued", only_focus=True)
    nodes = load_result("web_service_littles_law-reference")["summary"]["nodes"]
    fed = [name for name in nodes if name == "in_flight_unqueued" or name in _feeding()]
    assert alone.count('rx="3"') == len(fed) < whole.count('rx="3"')
    assert "#fafafa" not in alone, "a faded box was drawn in a graph that leaves them out"
    assert canvas(alone)[0] < canvas(whole)[0]
    assert whole == _graph(focus="in_flight_unqueued", only_focus=False)


def _feeding() -> set[str]:
    from bench.diagrams import _ancestry
    from bench.stamp import load_result

    payload = load_result("web_service_littles_law-reference")["summary"]
    return _ancestry(payload, "in_flight_unqueued")


def test_the_plain_distribution_uses_no_word_ch13_introduces():
    """ch04 prints it; sample, interval, median and percentile arrive in ch13."""
    from bench.diagrams import distribution, distribution_in_plain_words

    plain = distribution_in_plain_words("web_service_uncertainty-reference", "peak_request_rate")
    words = html.unescape(" ".join(match[1] for match in TEXT.findall(plain))).lower()
    for word in ("sample", "interval", "median", "p5", "p95"):
        assert word not in words, word
    usual = distribution("web_service_uncertainty-reference", "peak_request_rate")
    assert "samples" in usual and "median" in usual, "the default drawing is unchanged"


def test_the_two_zoomed_stretches_are_drawn_as_one_shape():
    """ch06's second figure: each stretch fills its own axes, and the two come out the same."""
    from bench.diagrams import queueing_zoom

    paths = re.findall(r'<path d="M([^"]*)"', queueing_zoom("queueing-curve"))
    assert len(paths) == 2
    first, second = (
        [tuple(float(v) for v in point.split(",")) for point in path.split(" L")] for path in paths
    )
    dx = second[0][0] - first[0][0]
    import numpy as np

    xs = np.array([x for x, _ in first])
    ys = np.array([y for _, y in first])
    for x, y in second:
        assert np.interp(x - dx, xs, ys) == pytest.approx(y, abs=1.0)


def test_the_queueing_curve_marks_the_model_margin():
    """The dashed line is the ceilings table's *Allowed*, read from the result, not typed."""
    from bench.diagrams import queueing_curve
    from bench.stamp import load_result

    summary = load_result("queueing-curve")["summary"]
    svg = queueing_curve("queueing-curve")
    assert svg.count('stroke-dasharray="3 3"') == 1
    left, right = 52.0, 480.0
    x = left + (1 - summary["queueing_margin"]) * (right - left)
    assert f'x1="{x:.1f}"' in svg


# -- tables that choose their rows ------------------------------------------------------------


def test_a_provenance_table_that_lists_some_kinds_still_counts_every_input():
    from bench import tables

    whole = tables.provenance_table("observability-reference")
    short = tables.provenance_table("observability-reference", "fact", "vendor_claim")
    assert whole.splitlines()[-1] == short.splitlines()[-1], "the tally counts every input"
    assert "| assumption |" not in short.replace("| assumption | |", "")
    omitted = [line for line in short.splitlines() if "| assumption | |" in line]
    assert len(omitted) == 1, "the left-out kind is counted in one line"
    assert whole == tables.provenance_table("observability-reference", *())
    with pytest.raises(KeyError):
        tables.provenance_table("observability-reference", "rumour")


def test_the_provenance_and_measured_tables_name_each_node_under_its_label():
    """Formulas and problems use the identifier; the tables show the label; one cell has both."""
    from bench import tables

    assert "collector throughput, as quoted<br>`collector_throughput_quoted`" in (
        tables.provenance_table("observability-reference")
    )
    measured = tables.measured_table("observability-reference")
    assert "<br>`collector_throughput_measured`" in measured
    assert len(measured.splitlines()[0].split("|")) == len(measured.splitlines()[2].split("|"))


def test_a_ceilings_table_shows_the_ceilings_named_in_the_order_named():
    from bench import tables

    named = ("scaling_loss", "queueing_headroom")
    table = tables.ceilings_table("web_service-reference", *named).splitlines()[2:]
    assert [row.split("|")[1].strip() for row in table] == [
        "fraction of the fleet doing nothing useful",
        "utilisation at the busy hour",
    ]
    assert tables.ceilings_table("web_service-reference") == tables.ceilings_table(
        "web_service-reference", *()
    )
    with pytest.raises(KeyError):
        tables.ceilings_table("web_service-reference", "no_such_ceiling")


def test_the_ratio_column_is_the_second_scenario_over_the_first():
    from bench import tables
    from bench.stamp import load_result

    table = tables.scenario_ratios(
        "web_service-reference", "web_service-twice_the_hosts", "hosts", "waiting_time"
    )
    rows = table.splitlines()[2:]
    assert len(rows) == 2
    a = load_result("web_service-reference")["summary"]["nodes"]["waiting_time"]["point"]
    b = load_result("web_service-twice_the_hosts")["summary"]["nodes"]["waiting_time"]["point"]
    assert rows[1].rstrip(" |").split("|")[-1].strip() == f"{b / a:.2f}"
    assert "(second)" in rows[1] and "(" not in rows[0].split("|")[1], (
        "a unit goes in the label, except for a count, which names what it counts"
    )
    with pytest.raises(KeyError):
        tables.scenario_ratios("web_service-reference", "web_service-twice_the_hosts")


def test_the_share_past_a_threshold_is_bounded_by_the_stamped_quantiles(monkeypatch):
    from bench import tables

    def stamped(p5, p25, p50, p75, p95, low=0.0, high=10.0):
        summary = {
            "p5": p5,
            "p25": p25,
            "p50": p50,
            "p75": p75,
            "p95": p95,
            "min": low,
            "max": high,
        }
        return lambda name: {"summary": {"nodes": {"x": {"summary": summary}}}}

    def share(*quantiles, **ends):
        monkeypatch.setattr(tables, "load_result", stamped(*quantiles, **ends))
        return tables.share_past("r", "x", 1.0, "what").splitlines()[-1]

    between = share(0.2, 0.5, 0.9, 1.1, 2.0)
    words = tables.SHARE_WORDS
    assert tables.SHARE_BETWEEN.format(low=words[0.25], high=words[0.5]) in between
    assert tables.SHARE_MORE_THAN.format(low=words[0.95]) in share(1.2, 1.3, 1.4, 1.5, 1.6)
    assert tables.SHARE_AT_MOST.format(high=words[0.05]) in share(0.2, 0.3, 0.4, 0.5, 0.6)
    assert tables.SHARE_EVERY in share(1.2, 1.3, 1.4, 1.5, 1.6, low=1.1)
    assert tables.SHARE_NONE in share(0.2, 0.3, 0.4, 0.5, 0.6, high=0.9)


def test_a_band_is_the_stamped_ends_and_their_ratio():
    from bench import tables
    from bench.stamp import load_result

    table = tables.bands_in_plain_words("observability-reference", "label_cardinality")
    summary = load_result("observability-reference")["summary"]["nodes"]["label_cardinality"][
        "summary"
    ]
    assert table.splitlines()[-1].endswith(f"| {summary['p95'] / summary['p5']:.1f}x |")
    with pytest.raises(KeyError):
        tables.bands_in_plain_words("observability-reference", "one_year")


def test_a_claim_sits_beside_the_measurement_that_would_replace_it():
    from bench import tables

    table = tables.claim_beside_measurement(
        "observability-reference", "collector_throughput_quoted", "collector_throughput_measured"
    )
    rows = table.splitlines()[2:]
    assert rows[0].startswith(f"| {tables.PROVENANCE_MARK['vendor_claim']} |")
    assert "*not yet measured*" in rows[1], "an unmeasured constant is never filled in"
    with pytest.raises(KeyError):
        tables.claim_beside_measurement("observability-reference", "no_such_node")


def test_the_plain_tornado_has_the_rows_of_the_usual_one():
    from bench import tables

    plain = tables.tornado_in_plain_words("web_service_uncertainty-reference", "peak_request_rate")
    usual = tables.tornado_table("web_service_uncertainty-reference", "peak_request_rate")
    assert plain.splitlines()[1:] == usual.splitlines()[1:]
    assert "p10" not in plain and "p90" not in plain


def test_the_commute_table_is_the_product_of_the_file_problem_1_2_reads():
    import math

    import yaml

    from bench import tables

    raw = yaml.safe_load(tables.COMMUTE.read_text())
    rows = tables.commute_table().splitlines()[2:]
    assert len(rows) == len(raw) + 2, "the usual commute, one row per input moved alone, and all"
    usual = math.prod(float(entry["usual"]) for entry in raw.values())
    most = math.prod(float(entry["most"]) for entry in raw.values())
    assert rows[0].endswith(f"£{usual:,.0f} |") and rows[-1].endswith(f"£{most:,.0f} |")


# -- figures batch 2: ch09 to ch18 --------------------------------------------------------------


def test_the_plain_tornado_takes_a_row_limit():
    from bench import tables

    three = tables.tornado_in_plain_words("web_service_capacity-reference", "raw_data", 3)
    usual = tables.tornado_table("web_service_capacity-reference", "raw_data", 3)
    assert len(three.splitlines()) == 5
    assert three.splitlines()[1:] == usual.splitlines()[1:]


def test_a_heading_carries_the_unit_its_cells_do_not():
    """Money marks itself in every cell and a count names itself; anything else needs a unit."""
    from bench import tables

    assert tables._with_unit("annual energy", "kWh/year") == "annual energy (kWh / year)"
    assert tables._with_unit("capex", "USD") == "capex"
    assert tables._with_unit("cost per million requests", "USD/megarequest") == (
        "cost per million requests"
    )
    assert tables._with_unit("hosts in the fleet", "host") == "hosts in the fleet"
    assert tables._with_unit("utilisation", "dimensionless") == "utilisation"
    header = tables.tornado_table("web_service-reference", "annual_energy", 2).splitlines()[0]
    assert "annual energy (kWh / year)" in header


def test_the_stage_table_shows_the_outputs_named_in_the_order_named():
    from bench import tables

    named = ("hosts_for_storage", "hosts_for_requests")
    rows = tables.stage_outputs("web_service_binding-reference", *named).splitlines()[2:]
    assert [row.split("|")[1].strip() for row in rows] == [
        "hosts for storage",
        "hosts for requests",
    ]
    assert tables.stage_outputs("web_service_binding-reference") == tables.stage_outputs(
        "web_service_binding-reference", *()
    )
    with pytest.raises(KeyError):
        tables.stage_outputs("web_service_binding-reference", "no_such_output")


def test_the_shortfall_table_is_the_usual_winner_over_every_future():
    """Median and average across all futures, zeros included; the median over the short futures
    alone is problem 10.2's answer and must not be stamped."""
    from bench import tables
    from bench.stamp import load_result

    summary = load_result("binding-constraint")["summary"]
    assert not [key for key in summary if "short_only" in key or "conditional" in key]
    winner = max(tables.CHAIN_WORDS, key=lambda chain: summary[f"{chain}_binds"])
    rows = tables.binding_shortfall_table("binding-constraint").splitlines()[2:]
    assert len(rows) == 2
    assert rows[0].endswith(f"| {summary[f'shortfall_median_all_if_{winner}']:,.0f} hosts |")
    assert rows[1].endswith(f"| {summary[f'shortfall_mean_all_if_{winner}']:,.0f} hosts |")
    assert tables.CHAIN_WORDS[winner] in rows[0]


def test_the_median_line_is_drawn_only_where_it_is_asked_for():
    from bench import diagrams

    result, node = "web_service_sizing-reference", "hosts_recommended"
    plain = diagrams.distribution_in_plain_words(result, node)
    middle = diagrams.distribution_against_the_middle(result, node)
    assert f">{diagrams.MIDDLE_LABEL}</text>" in middle
    assert f">{diagrams.MIDDLE_LABEL}</text>" not in plain
    # One more line in the median's colour. Not one more line in all: a linear axis loses its
    # midpoint tick when the median is drawn.
    assert middle.count('stroke="#263238"') == plain.count('stroke="#263238"') + 1
    assert plain == diagrams.distribution(result, node, plain=True, middle=False)


def test_the_correlation_table_prints_each_half_width_in_its_unit():
    from bench import tables
    from bench.stamp import load_result

    rows_in = load_result("correlation-effect")["summary"]["rows"]
    rows = tables.correlation_table("correlation-effect").splitlines()[2:]
    assert len(rows) == len(rows_in)
    for row, stamped in zip(rows, rows_in, strict=True):
        cells = [cell.strip() for cell in row.split("|")[3:5]]
        assert "e+" not in row
        assert cells[0] == tables._value_with_unit(stamped["declared"], stamped["unit"])


def test_the_convergence_table_says_how_many_runs_each_row_took():
    from bench import tables
    from bench.stamp import load_result

    points = load_result("convergence-tco")["summary"]["convergence"]
    header = tables.convergence_table("convergence-tco").splitlines()[0]
    assert tables.CONVERGENCE_HEADINGS[2].format(runs=points[0]["replicates"]) in header


def test_the_breach_table_names_ceilings_both_scenarios_declare():
    from bench import tables
    from bench.stamp import load_result

    a, b = "web_service-reference", "web_service-power_first"
    rows = tables.breach_comparison(a, b, "disk_fill").splitlines()[2:]
    over = [
        load_result(n)["summary"]["nodes"]["disk_fill"]["ceiling"]["p_over_limit"] for n in (a, b)
    ]
    assert rows == [f"| disk fill at horizon | {over[0]:.0%} | {over[1]:.0%} |"]
    with pytest.raises(KeyError):
        tables.breach_comparison(a, b, "hosts")
    with pytest.raises(KeyError):
        tables.breach_comparison(a, b)


def test_the_straight_line_table_reads_the_declared_growth_band():
    import math

    from bench import tables
    from bench.stages import model_path
    from sizing.dsl import load_model

    model = load_model(model_path("web_service"))
    band = model.nodes["annual_growth"].distribution["lognormal"]
    rows = tables.straight_line_overstatement(None, "web_service").splitlines()[2:]
    assert len(rows) == 3
    for row, factor in zip(
        rows, (band["p10"], math.sqrt(band["p10"] * band["p90"]), band["p90"]), strict=True
    ):
        end = factor ** model.nodes["horizon"].value
        too_high = (1 + end) / 2 / ((end - 1) / math.log(end)) - 1
        assert row.endswith(f"| {too_high:.0%} |")
    shares = [int(row.rstrip(" |%").split("|")[-1]) for row in rows]
    assert shares == sorted(shares), "the faster the growth, the more the straight line overstates"


def test_the_seam_tables_read_both_results():
    from bench import tables
    from bench.stamp import load_result

    down, up = "observability-reference", "web_service-reference"
    ends = tables.seam_table(down, up)
    median = load_result(up)["summary"]["nodes"]["cost_per_stored_tb_month"]["summary"]["p50"]
    assert tables.fmt(median, "USD/TB/month") in ends
    growth = tables.seam_growth_table(down, up).splitlines()[2:]
    assert len(growth) == 4
    bar = next(
        b
        for b in load_result(up)["summary"]["tornado"]["cost_per_stored_tb_month"]
        if b["node"] == "annual_growth"
    )
    assert growth[1].endswith(
        f"| {tables.fmt(bar['low'], 'USD/TB/month')} | {tables.fmt(bar['high'], 'USD/TB/month')} |"
    )


def test_the_targets_table_is_the_stamp_s_own_dict():
    from bench import tables
    from bench.stamp import TARGET_MEANING

    rows = tables.targets_table().splitlines()[2:]
    assert rows == [f"| `{target}` | {meaning} |" for target, meaning in TARGET_MEANING.items()]


def test_the_power_wall_names_each_marked_point_in_a_key():
    """Every point marked on a line has a matching mark and name under its panel."""
    from bench import diagrams
    from bench.stamp import load_result

    svg = diagrams.power_wall("power-first-sweep")
    payload = load_result("power-first-sweep")["summary"]
    fits = int(round(payload["fits"]))
    assert svg.count('r="4"') == 2 * 5, "five marks on the lines, each with its twin in a key"
    assert diagrams.WALL_WORDS["one_more"].format(n=fits + 1) in svg


def test_a_packed_graph_puts_each_input_beside_what_it_feeds():
    """ch09's chain drew *disk per host* two columns from the box it feeds, and its edge ran
    behind *raw disk needed at horizon*, so the picture said the one fed the other."""
    from bench import diagrams

    svg = diagrams.dependency_graph("web_service_capacity-reference", "hosts_for_storage", True)
    boxes_at = {
        html.unescape(label): float(x) - 6
        for x, label in re.findall(
            r'<text x="([0-9.]+)" y="[0-9.]+" font-size="[0-9.]+" '
            r'fill="#263238">([^<]*)</text>',
            svg,
        )
    }
    assert boxes_at["disk per host"] == boxes_at["disk margin"]
    assert boxes_at["hosts for storage"] - boxes_at["disk per host"] == diagrams.COLUMN_WIDTH


# -- figures batch 3: ch19 to the appendices and the cover ---------------------------------------


def test_a_tornado_of_what_moves_drops_the_inputs_that_do_not():
    """ch19's residence table listed five inputs that do not move it, beside prose saying so."""
    from bench import tables
    from bench.stamp import load_result

    bars = load_result("web_service-reference")["summary"]["tornado"]["residence_time"]
    moving = [bar for bar in bars if bar["span"] > 0]
    assert 0 < len(moving) < len(bars), "the premise: some inputs do not move it"
    table = tables.tornado_of_what_moves("web_service-reference", "residence_time", "HEADING")
    assert len(table.splitlines()) == 2 + len(moving)
    assert "| Input | Kind | HEADING " in table.splitlines()[0]
    assert tables.tornado_table("web_service-reference", "residence_time") == (
        tables.tornado_table("web_service-reference", "residence_time", moving_only=False)
    ), "the defaults are unchanged"


def test_the_value_of_information_table_has_three_places_and_no_minus_zero():
    """A perfect measurement found at the low end, the middle and the high end of the band."""
    from bench import tables
    from bench.stamp import load_result

    rows = load_result("value-of-information")["summary"]["rows"]
    for model, output in (("web_service", "hosts_recommended"), ("observability", "known_stored")):
        table = tables.value_of_information_table("value-of-information", model, output)
        lines = table.splitlines()
        mine = [r for r in rows if r["model"] == model and r["output"] == output]
        assert len(lines) == 2 + len(mine) + 2
        assert all(line.count("|") == 5 for line in lines)
        assert "-0%" not in table and "−0%" not in table
        assert "−" in table, "a share that widened the interval keeps its minus sign"
    assert tables._share_removed(-0.004) == "0%"
    assert tables._share_removed(-0.19) == "−19%"


def test_the_missing_node_table_reads_the_invoice_the_test_grades_against():
    """ch20's hard case: the invoice on the page is the one in the test, and the problem's number
    comes from the outline."""
    from bench import tables
    from bench.outline import label_of
    from bench.run_missing_node import invoice_average
    from bench.stamp import load_result
    from tests.the_missing_node.test_problem_3_missing_node import OBSERVED_MONTHLY

    assert invoice_average() == OBSERVED_MONTHLY
    summary = load_result("the-missing-node-fixture")["summary"]
    assert summary["invoice_average"] == OBSERVED_MONTHLY
    assert summary["p95"] < summary["invoice_average"], "the premise: the model cannot reach it"
    table = tables.fixture_against_invoice("the-missing-node-fixture")
    assert f"{label_of('the_missing_node').removeprefix('ch')}.3" in table.splitlines()[0]
    assert len(table.splitlines()) == 2 + len(tables.FIXTURE_ROWS)
    assert tables.fmt(OBSERVED_MONTHLY, "USD/month") in table


def test_the_decision_table_has_its_rows_in_order_and_adds_up():
    """ch21: seven rows, and the capex and opex rows add to the point-estimate total."""
    from bench import tables
    from bench.stamp import load_result

    table = tables.scenario_decision("web_service-reference", "web_service-sized_for_growth")
    lines = table.splitlines()
    assert len(lines) == 2 + len(tables.DECISION_ROWS)
    label = load_result("web_service-reference")["summary"]["nodes"]["queueing_headroom"]["label"]
    assert lines[-1].startswith(f"| {tables.DECISION_OVER.format(label=label)} |")
    for name in ("web_service-reference", "web_service-sized_for_growth"):
        nodes = load_result(name)["summary"]["nodes"]
        horizon = nodes["horizon"]["point"]
        total = nodes["capex"]["point"] + horizon * nodes["annual_opex"]["point"]
        assert total == pytest.approx(nodes["tco"]["point"], rel=1e-9), name


def test_a_marked_median_leaves_a_linear_axis_labelled_at_its_ends():
    """ch21: the midpoint tick sat beside the point estimate's line and was read as its figure."""
    from bench.diagrams import distribution, distribution_with_median

    def ticks(svg: str) -> int:
        return svg.count('font-size="10" text-anchor="middle" fill="#546e7a"')

    usual = distribution("web_service-reference", "tco")
    marked = distribution_with_median("web_service-reference", "tco")
    assert ticks(usual) == 1 and ticks(marked) == 0


def test_the_break_even_table_says_whose_each_line_is():
    """ch22: the move and the host count are on the challenger's side and are not the vendor's."""
    from bench import tables
    from bench.stamp import load_result

    summary = load_result("comparison")["summary"]
    kinds = {row["input"]: row["provenance"] for row in summary["designs"]["challenger"]["quote"]}
    lines = tables.comparison_break_even("comparison").splitlines()[2:]
    for row, line in zip(summary["break_even"], lines, strict=True):
        assumed = row["whose"] == "challenger" and kinds.get(row["input"]) == "assumption"
        assert (f"| {tables.ASSUMED_WHOSE} |" in line) == assumed, row["input"]
        if row["whose"] == "shared" and row["ties_at"] is not None and not row["in_swing"]:
            if row["ties_at"] < row["drawn_low"]:
                assert line.endswith(f"| {tables.TIE_BELOW_DRAWS} |"), row["input"]
            elif row["ties_at"] > row["drawn_high"]:
                assert line.endswith(f"| {tables.TIE_ABOVE_DRAWS} |"), row["input"]
            else:
                assert line.endswith(f"| {tables.TIE_IN_DRAWS} |"), row["input"]


def test_the_totals_table_prints_each_design_once():
    from bench import tables
    from bench.stamp import load_result

    designs = load_result("comparison")["summary"]["designs"]
    lines = tables.comparison_totals("comparison").splitlines()
    assert len(lines) == 2 + len(tables.TOTALS_ROWS)
    for (key, _), line in zip(tables.TOTALS_ROWS, lines[2:], strict=True):
        assert tables._money(designs[key]["tco"]["point"]) in line


def test_the_difference_axis_is_labelled_at_its_ends_and_the_tie_only():
    """ch22: a midpoint tick fell beside the p5 line and read as its value."""
    from bench.diagrams import paired_difference

    svg = paired_difference("comparison")
    ticks = re.findall(
        r'font-size="13.5" text-anchor="(?:start|middle|end)" fill="#546e7a">([^<]*)<', svg
    )
    assert len(ticks) in (2, 3)
    if len(ticks) == 3:
        assert "$0" in ticks


def test_a_compact_graph_is_narrower_and_changes_no_other_graph():
    """Appendix A's graph, drawn for a phone; every other graph is drawn as it was."""
    from bench.diagrams import COMPACT_LINES, dependency_graph

    result = "web_service_demand-reference"
    usual = dependency_graph(result)
    compact = dependency_graph(result, None, False, True)
    assert canvas(compact)[0] < canvas(usual)[0]
    assert usual == dependency_graph(result, None, False, False)
    assert "…" not in compact
    sizes = {float(size) for size in re.findall(r'font-size="([0-9.]+)"', compact)}
    from bench.diagrams import TEXT as FLOOR

    assert min(sizes) >= FLOOR
    assert COMPACT_LINES == 3


def test_the_shape_table_lists_the_keys_the_sampler_takes():
    """Appendix A: a file writes exactly the parameters each percentile function takes."""
    import inspect

    from bench import tables
    from sizing import mc

    rows = tables.distribution_keys().splitlines()[2:]
    assert len(rows) == len(mc.SHAPES)
    for row, (shape, function) in zip(rows, mc.SHAPES.items(), strict=True):
        assert row.startswith(f"| `{shape}` |")
        for key in inspect.signature(function).parameters:
            assert (f"`{key}`" in row) == (key != "u"), (shape, key)


def test_a_ceiling_in_the_formula_sheet_is_named_as_its_graph_box_is():
    """Appendix E and F: "limit on …", so no two rows read the same and every box has a row."""
    from bench import tables
    from sizing.dsl import Ceiling, discover

    for model in discover():
        sheet = tables.formulas_table(None, model.name)
        for name, node in model.nodes.items():
            if isinstance(node, Ceiling):
                assert f"| limit on {node.display} (`{name}`) |" in sheet, (model.name, name)


def test_a_tornado_of_what_reaches_counts_the_rest():
    """Appendix F: the table shows the chart's bars, and one row counts the inputs left out."""
    from bench import tables
    from bench.stamp import load_result

    bars = load_result("observability-reference")["summary"]["tornado"]["active_series"]
    still = sum(1 for bar in bars if bar["span"] <= 0)
    lines = tables.tornado_of_what_reaches("observability-reference", "active_series").splitlines()
    assert still and len(lines) == 2 + (len(bars) - still) + 1
    assert lines[-1].startswith(f"| {tables.STILL_ROW.format(count=still)} |")


def test_the_spread_table_refuses_a_node_it_cannot_show():
    from bench import tables

    with pytest.raises(KeyError):
        tables.spread_table("observability-reference", "no_such_node")
    with pytest.raises(KeyError):
        tables.spread_table("observability-reference")
    with pytest.raises(KeyError):
        tables.spread_table("observability-reference", "traces_ingest")


def test_the_attribution_table_gives_each_input_its_unit():
    """ch23: a request rate and a CPU cost read the same without one."""
    from bench import tables

    table = tables.postmortem_table("postmortem", "complete")
    for unit in ("request/second", "second * core / request"):
        assert f"({tables.unit_label(unit)})" in table, unit
