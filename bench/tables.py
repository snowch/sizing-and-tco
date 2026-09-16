"""Stamped results as markdown fragments. No chapter contains a number; they contain these.

Every table here carries a *Conditions* line, because a figure without its conditions is an
anecdote and the conditions are exactly what a reader needs in order to disagree with it. For a
measured constant that means the corpus, the codec and the stack. For a model output it means the
model file, the scenario, the seed, the sample count and the fingerprint of the code that did the
arithmetic — all of which, together, are what makes "re-run it yourself" a complete instruction.
"""

from __future__ import annotations

import math

from bench.stamp import load_result
from sizing.dsl import PROVENANCE_MEANING
from sizing.units import parse as parse_unit

#: How a provenance kind is shown. The symbol is carried into the graph viewer and the tornado so
#: that one glance answers "how much of this model is somebody's guess".
PROVENANCE_MARK = {"fact": "●", "vendor_claim": "◐", "assumption": "○"}

VERDICT_MARK = {"ok": "ok", "inside headroom": "inside headroom", "over": "**over**"}


# -- formatting -----------------------------------------------------------------------------


def fmt(value: float | None, unit: str = "dimensionless") -> str:
    """A number, at a precision that does not overstate what is known.

    Money to the dollar below a million and to three significant figures above it, because a
    five-year total written to the cent is claiming a precision no input in the model has.
    Counts as integers. Everything else to three significant figures, which is more than most of
    these deserve.
    """
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value)
    dimensions = str(parse_unit(unit).dimensionality)
    if "[currency]" in dimensions:
        # Anything with money in it gets a currency mark, including a rate like USD/year and a
        # unit cost like USD/TB/month — the "per what" lives in the column heading, and a table
        # of costs where some cells are marked and some are not reads as an error.
        if abs(value) >= 1000:
            return f"${value:,.0f}"
        return f"${value:,.2f}"
    if unit in ("node", "drive", "core", "host"):
        return f"{value:,.0f}"
    if value == 0:
        return "0"
    magnitude = math.floor(math.log10(abs(value)))
    places = max(0, 2 - magnitude)
    return f"{value:,.{min(places, 4)}f}"


def unit_label(unit: str) -> str:
    """A unit as a reader should see it, not as Pint spells it."""
    pretty = {
        "dimensionless": "",
        "USD": "USD",
        "USD/TB/month": "USD / TB / month",
        "USD/year": "USD / year",
        "byte/line": "bytes / line",
        "byte/sample": "bytes / sample",
        "byte/span": "bytes / span",
        "GB/s": "GB/s",
        "kWh/year": "kWh / year",
        "1/year": "per year",
    }
    return pretty.get(unit, unit)


def _interval(summary: dict | None) -> str:
    if not summary:
        return "—"
    return f"{summary['p5']:,.4g} to {summary['p95']:,.4g}"


# -- conditions -------------------------------------------------------------------------------


def conditions(name: str) -> str:
    """Where this figure came from, in one line, under every table that shows it."""
    result = load_result(name)
    produced = result.get("produced_by", {})
    parts = [f"target `{result['target']}`"]

    if result.get("kind") == "model":
        parts += [
            f"model `{produced.get('model_file')}`",
            f"scenario `{produced.get('scenario')}`",
            f"{produced.get('samples'):,} samples",
            f"seed `{produced.get('seed')}`",
        ]
        if produced.get("unmeasured"):
            parts.append(f"**{len(produced['unmeasured'])} constant(s) not yet measured**")
    else:
        for key in ("corpus", "codec", "stack", "system", "window"):
            if produced.get(key):
                parts.append(str(produced[key]))
    parts.append(result["generated_at"][:10])
    parts.append(f"Source: `bench/results/{name}.json`, code hash `{result['code_fingerprint']}`")
    return "*Conditions: " + " · ".join(parts) + ".*"


# -- model tables -----------------------------------------------------------------------------


def outputs_table(name: str) -> str:
    """What the model says, at a point and across its uncertainty.

    Two columns that a spreadsheet would give one. The point estimate is what a plan is usually
    built on; the interval beside it is the same model saying how much that point is worth.
    """
    payload = load_result(name)["summary"]
    rows = [
        "| Output | Point estimate | 90% interval | Unit |",
        "|---|---:|---:|---|",
    ]
    for output in payload["outputs"]:
        node = payload["nodes"][output]
        summary = node.get("summary")
        if node.get("blocked_by"):
            # Not a dash because the number is small. A dash because nobody has measured the
            # constant this depends on, and the box below the table says which.
            point = interval = "*not yet measured*"
        else:
            point = fmt(node.get("point"), node["unit"])
            interval = (
                f"{fmt(summary['p5'], node['unit'])} to {fmt(summary['p95'], node['unit'])}"
                if summary
                else "*fixed*"
            )
        rows.append(f"| {node['label']} | {point} | {interval} | {unit_label(node['unit'])} |")
    return "\n".join(rows)


def ceilings_table(name: str) -> str:
    """Every declared ceiling, where the plan sits against it, and how often it breaks.

    The last column is the one this book exists for. A sizing answer is not a number; it is a
    number together with how much of the model's own uncertainty puts it over the edge.
    """
    payload = load_result(name)["summary"]
    ceilings = {
        node_name: node["ceiling"]
        for node_name, node in payload["nodes"].items()
        if node.get("ceiling")
    }
    if not ceilings:
        return "*This model declares no ceilings. It is a cost model: see the front matter.*"
    rows = [
        "| Ceiling | At the plan | Headroom | Allowed | Verdict | Over allowed | Over limit |",
        "|---|---:|---:|---:|---|---:|---:|",
    ]
    for node_name, ceiling in sorted(ceilings.items()):
        label = payload["nodes"][node_name]["label"]
        rows.append(
            f"| {label} | {ceiling['value']:.2f} | {ceiling['headroom']:.0%} "
            f"| {ceiling['allowed']:.2f} | {VERDICT_MARK[ceiling['verdict']]} "
            f"| {ceiling.get('p_over_allowed', 0):.0%} | {ceiling.get('p_over_limit', 0):.0%} |"
        )
    return "\n".join(rows)


def provenance_table(name: str) -> str:
    """Every input, by how much somebody is claiming when they wrote it down.

    The count at the bottom is the honest summary of any model: this many of the numbers are
    traceable, this many are somebody's sales material, and this many were decided in a meeting.
    """
    payload = load_result(name)["summary"]
    counts: dict[str, int] = {}
    rows = ["| | Input | Provenance | Source |", "|---|---|---|---|"]
    for node_name in payload["order"]:
        node = payload["nodes"][node_name]
        if node["kind"] != "input":
            continue
        kind = node["provenance"]["kind"]
        counts[kind] = counts.get(kind, 0) + 1
        source = node["provenance"]["source"].replace("\n", " ").strip()
        rows.append(
            f"| {PROVENANCE_MARK.get(kind, '?')} | {node['label']} | {kind.replace('_', ' ')} "
            f"| {source} |"
        )
    total = sum(counts.values())
    tally = ", ".join(
        f"{counts.get(kind, 0)} {kind.replace('_', ' ')}" for kind in PROVENANCE_MEANING
    )
    rows.append(f"| | **{total} inputs** | | **{tally}** |")
    return "\n".join(rows)


def measured_table(name: str) -> str:
    """The empirical constants, what they are worth, and what they are *about*."""
    payload = load_result(name)["summary"]
    measured = {
        node_name: node
        for node_name, node in payload["nodes"].items()
        if node["kind"] == "measured"
    }
    if not measured:
        return "*This model has no measured constants.*"
    rows = [
        "| Constant | Value | Standard error | Unit | Measured against |",
        "|---|---:|---:|---|---|",
    ]
    for _node_name, node in sorted(measured.items()):
        found = node.get("measured")
        if not found:
            rows.append(
                f"| {node['label']} | *not yet measured* | — | {unit_label(node['unit'])} "
                f"| `bench/results/{node['result']}.json` does not exist |"
            )
            continue
        rows.append(
            f"| {node['label']} | {fmt(found['value'], node['unit'])} "
            f"| ± {fmt(found['sd'], node['unit'])} | {unit_label(node['unit'])} "
            f"| {found['stack']} |"
        )
    return "\n".join(rows)


def tornado_table(name: str, output: str, limit: int = 8) -> str:
    """Which input moves one output most, when swung on its own across its middle 80%."""
    payload = load_result(name)["summary"]
    bars = payload["tornado"].get(output, [])[:limit]
    if not bars:
        return f"*No uncertain input feeds `{output}`.*"
    unit = payload["nodes"][output]["unit"]
    rows = [
        f"| Input | Kind | {payload['nodes'][output]['label']} at its p10 | at its p90 | Swing |",
        "|---|---|---:|---:|---:|",
    ]
    for bar in bars:
        rows.append(
            f"| {bar['label']} | {bar['kind']} | {fmt(bar['low'], unit)} "
            f"| {fmt(bar['high'], unit)} | {fmt(bar['span'], unit)} |"
        )
    return "\n".join(rows)


def constant_table(name: str) -> str:
    """One corpus measurement, with its shards, so the standard error is not just asserted."""
    result = load_result(name)
    summary, units = result["summary"], result["units"]
    unit = unit_label(units.get("value", "dimensionless"))
    rows = ["| | Value |", "|---|---:|"]
    rows.append(f"| Mean over {summary['shards']} shards | {summary['value']:,.4g} {unit} |")
    rows.append(f"| Standard error of that mean | ± {summary['sd']:,.3g} {unit} |")
    if "shard_spread" in summary:
        rows.append(f"| Spread between shards | {summary['shard_spread']:,.3g} {unit} |")
    if "low" in summary:
        rows.append(f"| Lowest / highest shard | {summary['low']:,.4g} / {summary['high']:,.4g} |")
    return "\n".join(rows)


# -- the box that is not a number ---------------------------------------------------------------


def not_yet_measured(name: str) -> str:
    """What a chapter shows where a constant has not been taken yet.

    No figures, not even plausible ones. The reader of a draft sees a missing measurement; they
    never see an invented one, and a prose paragraph written around this box reads correctly the
    day the measurement lands.
    """
    payload = load_result(name)["summary"]
    missing = payload.get("unmeasured", [])
    if not missing:
        return ""
    blocked = sorted(
        node_name for node_name, node in payload["nodes"].items() if node.get("blocked_by")
    )
    lines = [
        ":::{warning} Not measured yet",
        f"`{payload['model']}` declares {len(missing)} constant(s) that nobody has measured:",
        "",
    ]
    for node_name in missing:
        node = payload["nodes"][node_name]
        lines.append(f"- **{node['label']}** — needs `bench/results/{node['result']}.json`")
    lines += [
        "",
        f"{len(blocked)} node(s) downstream of those cannot be computed and are shown as — "
        "rather than filled in. Nothing is estimated in their place: this book publishes "
        "measurements or it publishes nothing.",
        ":::",
    ]
    return "\n".join(lines)


# -- ch14's two experiments ---------------------------------------------------------------


def convergence_table(name: str) -> str:
    """Two columns that behave differently, which is the whole of the figure.

    The interval settles. The spread between runs falls. A reader who has only ever been told
    "use ten thousand samples" has generally conflated the two, and conflating them is what makes
    "how many samples is enough" feel like a matter of taste rather than a calculation.
    """
    summary = load_result(name)["summary"]
    rows = [
        "| Samples | 90% interval half-width | Spread of p95 between runs | Ratio to the row above |",
        "|---:|---:|---:|---:|",
    ]
    previous = None
    for point in summary["convergence"]:
        ratio = "—" if previous is None else f"{previous / point['p95_spread']:.2f}×"
        previous = point["p95_spread"]
        rows.append(
            f"| {point['samples']:,} | {fmt(point['half_width'], 'USD')} "
            f"| {fmt(point['p95_spread'], 'USD')} | {ratio} |"
        )
    rows.append(
        f"| | *settles* | *falls* | **{summary['overall_ratio_per_decade']:.2f}× per decade** "
        f"from {summary['law_measured_from']:,} samples up, against √10 = "
        f"{summary['root_ten']:.2f} |"
    )
    return "\n".join(rows)


def correlation_table(name: str) -> str:
    """What declaring that two inputs move together was worth, per output."""
    rows_in = load_result(name)["summary"]["rows"]
    rows = [
        "| Model | Output | Interval as declared | Assuming independence | Difference |",
        "|---|---|---:|---:|---:|",
    ]
    for row in rows_in:
        rows.append(
            f"| `{row['model']}` | {row['output']} | {row['declared']:,.4g} "
            f"| {row['independent']:,.4g} | {row['change']:+.1%} |"
        )
    return "\n".join(rows)


def declared_correlations(name: str) -> str:
    """Which pairs a model says move together, how strongly, and why."""
    payload = load_result(name)["summary"]
    correlations = payload.get("correlations", [])
    if not correlations:
        return "*This model declares no correlations — which is itself an assumption.*"
    rows = ["| Between | and | Rank correlation | Because |", "|---|---|---:|---|"]
    for pair in correlations:
        because = " ".join(str(pair.get("because", "")).split())
        rows.append(f"| {pair['a']} | {pair['b']} | {pair['rho']:+.2f} | {because} |")
    return "\n".join(rows)


def scenario_comparison(name: str, other: str) -> str:
    """Two scenarios of the same model, side by side.

    A decision is a comparison. One column of numbers is a position; two is an argument, and the
    difference between them is what somebody is being asked to buy (ch21).
    """
    left, right = load_result(name)["summary"], load_result(other)["summary"]
    rows = [
        f"| Output | {left['scenario']['title']} | {right['scenario']['title']} |",
        "|---|---:|---:|",
    ]
    for output in left["outputs"]:
        node = left["nodes"][output]
        rows.append(
            f"| {node['label']} | {_cell(node)} | {_cell(right['nodes'].get(output, {}))} |"
        )
    ceilings = [n for n, node in left["nodes"].items() if node.get("ceiling")]
    for node_name in sorted(ceilings):
        ours = left["nodes"][node_name].get("ceiling") or {}
        theirs = (right["nodes"].get(node_name) or {}).get("ceiling") or {}
        rows.append(
            f"| *{left['nodes'][node_name]['label']}* — over its limit "
            f"| {ours.get('p_over_limit', float('nan')):.0%} "
            f"| {theirs.get('p_over_limit', float('nan')):.0%} |"
        )
    return "\n".join(rows)


def _cell(node: dict) -> str:
    if not node or node.get("blocked_by"):
        return "*not yet measured*"
    summary = node.get("summary")
    point = fmt(node.get("point"), node["unit"])
    if not summary:
        return point
    return f"{point}<br>*{fmt(summary['p5'], node['unit'])} to {fmt(summary['p95'], node['unit'])}*"


def constants_index(_name: str = "") -> str:
    """Every measured constant in the repository, measured or not, in one table.

    Reads the results directory rather than a list, so a constant cannot be added without
    appearing here and a constant that is still missing cannot be quietly dropped from the book.
    """
    import json

    from bench.stamp import RESULTS_DIR

    rows = [
        "| Constant | Target | Value | Standard error | Measured against |",
        "|---|---|---:|---:|---|",
    ]
    found = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        payload = json.loads(path.read_text())
        if payload.get("kind") != "measurement" or "value" not in payload.get("summary", {}):
            continue
        unit = payload["units"].get("value", "dimensionless")
        found.append(
            f"| `{path.stem}` | `{payload['target']}` "
            f"| {fmt(payload['summary']['value'], unit)} {unit_label(unit)} "
            f"| ± {fmt(payload['summary'].get('sd'), unit)} "
            f"| {payload['produced_by'].get('stack', '—')} |"
        )
    rows += found
    for missing in sorted(_unmeasured_across_models()):
        rows.append(f"| `{missing}` | — | *not yet measured* | — | — |")
    return "\n".join(rows)


def _unmeasured_across_models() -> set[str]:
    from sizing.dsl import Measured, discover

    missing = set()
    for model in discover():
        for node in model.of_kind("measured"):
            assert isinstance(node, Measured)
            if not node.is_measured:
                missing.add(node.result)
    return missing
