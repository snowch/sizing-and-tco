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
from sizing.dsl import PROVENANCE_MEANING, discover
from sizing.units import parse as parse_unit

#: How a provenance kind is shown. The symbol is carried into the graph viewer and the tornado so
#: that one glance answers "how much of this model is somebody's guess".
PROVENANCE_MARK = {"fact": "●", "vendor_claim": "◐", "assumption": "○"}

#: What a measurement says about itself, in the order a reader needs it.
MEASURED_KEYS = ("corpus", "codec", "stack", "system", "window")

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


def _said_by(name: str) -> list[str]:
    """What one stamped result says about how it was produced."""
    result = load_result(name)
    produced = result.get("produced_by", {})
    said = [f"target `{result['target']}`"]
    if result.get("kind") == "model":
        said += [
            f"model `{produced.get('model_file')}`",
            f"scenario `{produced.get('scenario')}`",
            f"{produced.get('samples'):,} samples",
            f"seed `{produced.get('seed')}`",
        ]
        if produced.get("unmeasured"):
            said.append(f"**{len(produced['unmeasured'])} constant(s) not yet measured**")
    else:
        said += [str(produced[key]) for key in MEASURED_KEYS if produced.get(key)]
    return said


def _from_source(what: str) -> str:
    """What a fragment assembled at build time says instead of naming a run.

    There is no single result to point at, and naming one anyway is what put a compression
    benchmark under a table of unit conversions. Saying so is the honest option and the short one.
    """
    return (
        f"*Conditions — assembled at build time from {what} · no single stamped run*\\\n"
        "*Re-run — `make figures`*"
    )


def conditions(name: str | None, *also: str, computed_from: str | None = None) -> str:
    """Where this figure came from, under every table that shows it.

    ``name`` is ``None`` for a fragment computed from the model files rather than from a run, and
    ``also`` names any further results the fragment draws on — a scenario comparison prints two
    columns from two runs, and naming one of them is a disclosure that is quietly false.

    Two lines rather than one, split where the content already splits: the first is what a reader
    needs in order to **disagree** with the figure, the second is what they need in order to
    **re-run** it. As one line it reached two hundred and ninety-three characters, which on a
    phone is five wrapped lines of italic — and a provenance note nobody reads is worth the same
    as no provenance note. Nothing is dropped to get there. A book whose argument is that every
    number carries its conditions does not then abbreviate them.
    """
    if name is None:
        return _from_source(computed_from or "this repository")
    # What was computed, and against what. This is the half somebody argues with. Every result
    # the fragment draws on gets its own clause, because a table with two columns from two runs
    # has two sets of conditions and a reader checking either one needs both.
    names = (name, *also)
    # Every scenario table in the book is one model run twice, so repeating the model and the
    # sample count would be noise. Where the runs share a model, they share one clause and the
    # scenarios are listed; where they do not, each gets its own.
    models = {load_result(one).get("produced_by", {}).get("model_file") for one in names}
    if also and len(models) == 1:
        scenarios = [load_result(one).get("produced_by", {}).get("scenario") for one in names]
        said = " · ".join(_said_by(name)).replace(
            f"scenario `{scenarios[0]}`",
            "scenarios " + " and ".join(f"`{one}`" for one in scenarios),
        )
    else:
        said = " · ".join(_said_by(name))
        for extra in also:
            said += " · and " + " · ".join(_said_by(extra))
    # And how to check it for yourself, which is a different question and gets its own line.
    check = [f"`bench/results/{one}.json`" for one in names]
    check.append(f"code hash `{load_result(name)['code_fingerprint']}`")
    check.append(f"stamped {load_result(name)['generated_at'][:10]}")
    return "*Conditions — " + said + "*\\\n*Re-run — " + " · ".join(check) + "*"


# -- model tables -----------------------------------------------------------------------------


def row_labels(payload: dict) -> dict[str, str]:
    """Row labels for a table of outputs, disambiguated where two of them share one.

    A ceiling carries the label of the quantity it watches. That is right in a ceilings table,
    where the column is headed *Ceiling* — and it prints the same line twice in a table of
    outputs, when a model publishes both the quantity and the ceiling on it. The ceiling is the
    one that gets the suffix, because it is the one whose name was borrowed.
    """
    nodes, outputs = payload["nodes"], payload["outputs"]
    labels = [nodes[name]["label"] for name in outputs]
    return {
        name: (
            f"{nodes[name]['label']}, against its limit"
            if labels.count(nodes[name]["label"]) > 1 and nodes[name].get("ceiling")
            else nodes[name]["label"]
        )
        for name in outputs
    }


def outputs_table(name: str) -> str:
    """What the model says, at a point and across its uncertainty.

    Two columns that a spreadsheet would give one. The point estimate is what a plan is usually
    built on; the interval beside it is the same model saying how much that point is worth.
    """
    payload = load_result(name)["summary"]
    labels = row_labels(payload)
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
        rows.append(f"| {labels[output]} | {point} | {interval} | {unit_label(node['unit'])} |")
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


def value_of_information_table(name: str, model: str, output: str) -> str:
    """What knowing one input exactly would do to the interval, per input.

    The column that matters is the last one, and it is a *ceiling*: no real measurement is
    perfect, so nothing anybody can go and do buys more than this. A small number in it is the
    useful case — it says a measurement is not worth commissioning however well it goes.

    The total row is the one to read twice. The individual figures do not add to a hundred per
    cent and are not shares of anything; a chain of multiplications does not divide its
    uncertainty between its inputs (ch19).
    """
    payload = load_result(name)["summary"]
    rows = [row for row in payload["rows"] if row["model"] == model and row["output"] == output]
    totals = next(
        (t for t in payload["totals"] if t["model"] == model and t["output"] == output), None
    )
    if not rows or totals is None:
        return f"*Nothing uncertain feeds `{output}` in `{model}`.*"
    unit = _output_unit(model, output)
    out = [
        "| If this were known exactly | Kind | The interval would be | Most it could remove |",
        "|---|---|---:|---:|",
    ]
    for row in sorted(rows, key=lambda r: -r["removed"]):
        out.append(
            f"| {row['label']} | {row['kind']} | {fmt(row['if_known'], unit)} "
            f"| {row['removed']:.0%} |"
        )
    out.append(f"| **every one of them** | | **{fmt(totals['all_known'], unit)}** | **100%** |")
    out.append(
        f"| | | *now: {fmt(totals['half_width'], unit)}* "
        f"| *the rows above total {totals['sum_of_removals']:.0%}, which is not how this works* |"
    )
    return "\n".join(out)


def postmortem_table(name: str, which: str) -> str:
    """Where each input sat in the futures where the design failed, against where it usually sits.

    Two columns do the work. *Shift* says how far an input had to be from its ordinary self for
    the ceiling to break; a figure near zero is a bystander. *Extreme in* says how often it was
    genuinely unusual rather than merely high — which is the column that decides whether the
    story afterwards gets to be about one dramatic thing.
    """
    payload = load_result(name)["summary"][which]
    rows = [
        "| Input | Its usual value | In the failures | Shift | Extreme in |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        unit = _output_unit(payload["model"], row["input"])
        rows.append(
            f"| {row['label']} | {fmt(row['overall'], unit)} | {fmt(row['in_failures'], unit)} "
            f"| {'none' if abs(row['shift']) < 0.005 else format(row['shift'], '+.0%')} "
            f"| {row['extreme_in_failures']:.0%} of them |"
        )
    rows.append(
        f"| **{payload['inputs']} inputs** | | "
        f"*{payload['share_of_futures']:.0%} of futures ended here* "
        f"| | *something was beyond its p90 in {payload['something_extreme_share']:.0%} of them, "
        f"against {payload['something_extreme_everywhere']:.0%} of futures generally* |"
    )
    return "\n".join(rows)


def _output_unit(model: str, output: str) -> str:
    """The unit of one output, read from the model rather than carried in the experiment."""
    for candidate in discover():
        if candidate.name == model:
            return candidate.nodes[output].unit
    return "dimensionless"


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
    labels = row_labels(left)
    rows = [
        f"| Output | {left['scenario']['title']} | {right['scenario']['title']} |",
        "|---|---:|---:|",
    ]
    for output in left["outputs"]:
        node = left["nodes"][output]
        rows.append(
            f"| {labels[output]} | {_cell(node)} | {_cell(right['nodes'].get(output, {}))} |"
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


# -- Part II: the curves ------------------------------------------------------------------


def queueing_table(name: str) -> str:
    """Utilisation against what a request actually costs.

    The last column is the one people have not seen. Everybody knows a busy system is slower;
    almost nobody has looked at how the second half of that sentence behaves, which is that it
    does nothing for a long time and then does everything at once.
    """
    rows = load_result(name)["summary"]["curve"]
    out = [
        "| Utilisation | Time queueing | Time in the system | Requests in flight | Slower than idle by |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        out.append(
            f"| {row['utilisation']:.0%} | {row['waiting_time'] * 1000:,.1f} ms "
            f"| {row['residence_time'] * 1000:,.1f} ms | {row['concurrency']:,.0f} "
            f"| {row['inflation']:.1f}x |"
        )
    return "\n".join(out)


def scaling_table(name: str) -> str:
    """What each batch of machines bought, and where the curve turns over."""
    summary = load_result(name)["summary"]
    out = [
        "| Nodes | Throughput | If scaling were free | Efficiency | Per node |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in summary["curve"]:
        marker = " **peak**" if row["nodes"] == summary["peak_at_nodes"] else ""
        out.append(
            f"| {row['nodes']:,.0f}{marker} | {row['achievable_throughput']:,.0f} "
            f"| {row['linear_throughput']:,.0f} | {row['scaling_efficiency']:.0%} "
            f"| {row['throughput_per_node']:,.1f} |"
        )
    out.append(
        f"| | | | *swept peak* | *{summary['peak_at_nodes']:,.0f} nodes, against "
        f"{summary['predicted_peak']:,.1f} predicted from the two coefficients* |"
    )
    return "\n".join(out)


def binding_table(name: str) -> str:
    """Which of two chains decides the answer, and how often."""
    summary = load_result(name)["summary"]
    return "\n".join(
        [
            "| | |",
            "|---|---:|",
            f"| Capacity decides the node count | {summary['capacity_binds']:.0%} of samples |",
            f"| Bandwidth decides it | {summary['throughput_binds']:.0%} of samples |",
            f"| Median gap between the two chains | {summary['median_gap']:,.0f} nodes |",
            f"| Gap at the 95th percentile | {summary['p95_gap']:,.0f} nodes |",
            f"| Median of the capacity chain alone | {summary['median_capacity_nodes']:,.0f} nodes |",
            f"| Median of the bandwidth chain alone | {summary['median_throughput_nodes']:,.0f} nodes |",
        ]
    )


# -- Parts I, III and V --------------------------------------------------------------------


def workload_table(name: str) -> str:
    """The quantities that describe the demand, separated from the ones that describe the system.

    A model's inputs are two different kinds of thing wearing the same clothes. Some describe
    what the world is doing to you; the rest describe what you have decided to do about it. A
    table that mixes them is how a sizing conversation ends up arguing about a growth rate as
    though it were a choice.
    """
    payload = load_result(name)["summary"]
    demand, choices = [], []
    for node_name in payload["order"]:
        node = payload["nodes"][node_name]
        if node["kind"] != "input":
            continue
        row = (
            f"| {node['label']} | {fmt(node.get('point'), node['unit'])} "
            f"| {unit_label(node['unit'])} | {PROVENANCE_MARK.get(node['provenance']['kind'], '?')} |"
        )
        # A quantity with a distribution is something the world decides; a stated value with a
        # slider is something you do. It is a heuristic, and it is right far more often than the
        # alternative of not distinguishing them at all.
        (demand if node.get("distribution") else choices).append(row)
    header = ["| Quantity | At the reference point | Unit | |", "|---|---:|---|---|"]
    return "\n".join(
        [
            *header,
            "| **What the world does** | | | |",
            *demand,
            "| **What you decide** | | | |",
            *choices,
        ]
    )


def cost_split_table(name: str) -> str:
    """Capital against running cost, over the declared horizon."""
    payload = load_result(name)["summary"]
    nodes = payload["nodes"]

    def value(key: str) -> float:
        return nodes[key]["point"]

    horizon = value("horizon")
    capex, opex = value("capex"), value("lifecycle_opex")
    total = value("tco")
    rows = [
        "| | Amount | Share of the total |",
        "|---|---:|---:|",
        f"| Capital, paid once | {fmt(capex, 'USD')} | {capex / total:.0%} |",
        f"| Drives | {fmt(value('drive_capex'), 'USD')} | {value('drive_capex') / total:.0%} |",
        f"| Chassis | {fmt(value('chassis_capex'), 'USD')} | {value('chassis_capex') / total:.0%} |",
        f"| Network | {fmt(value('network_capex'), 'USD')} | {value('network_capex') / total:.0%} |",
        f"| Running, over {horizon:.0f} years | {fmt(opex, 'USD')} | {opex / total:.0%} |",
        f"| Energy | {fmt(value('annual_energy_cost') * horizon, 'USD')} "
        f"| {value('annual_energy_cost') * horizon / total:.0%} |",
        f"| Support | {fmt(value('annual_support') * horizon, 'USD')} "
        f"| {value('annual_support') * horizon / total:.0%} |",
        f"| People | {fmt(value('annual_staff_cost') * horizon, 'USD')} "
        f"| {value('annual_staff_cost') * horizon / total:.0%} |",
        f"| **Total** | **{fmt(total, 'USD')}** | |",
    ]
    return "\n".join(rows)


def node_kinds_table(name: str) -> str:
    """What a model is made of, counted.

    The census that classifies it. A model with no measured constant and no ceiling is a cost
    model and sampling its inputs is enough; one with either is a sizing model and it is not.
    """
    payload = load_result(name)["summary"]
    counts: dict[str, int] = {}
    for node in payload["nodes"].values():
        counts[node["kind"]] = counts.get(node["kind"], 0) + 1
    rows = ["| Node kind | Count | What it carries |", "|---|---:|---|"]
    meaning = {
        "input": "a value or a distribution, a provenance kind and a source",
        "derived": "a formula, whose declared unit is checked against what it produces",
        "measured": "a stamped result, a standard error, and the implementation it belongs to",
        "ceiling": "a limit, a declared headroom, and a reason",
    }
    for kind in ("input", "derived", "measured", "ceiling"):
        rows.append(f"| `{kind}` | {counts.get(kind, 0)} | {meaning[kind]} |")
    rows.append(
        f"| | | **classified as a {payload['classification']} model**"
        + (
            " — it has measured constants or ceilings in it, so sampling the inputs is not "
            "sufficient on its own"
            if payload["classification"] == "sizing"
            else " — accounting identities with uncertain parameters, and sampling the inputs is "
            "sufficient"
        )
        + " |"
    )
    return "\n".join(rows)


# -- appendices ----------------------------------------------------------------------------


def conversions_table(_name: str = "") -> str:
    """Every conversion the build applies, across every model.

    The reason this book has a unit system rather than a convention. Each row is a place where
    somebody wrote a formula in the units their invoices and datasheets came in, declared the
    answer in the unit they wanted to read it in, and the build did the arithmetic that everybody
    gets wrong by hand.

    A row with a factor of twelve is a figure that would otherwise have been twelve times too
    large, and it would have looked entirely plausible.
    """
    from sizing.dsl import discover
    from sizing.evaluate import check_units

    rows = [
        "| Model | Node | Formula produces | Node declares | Factor |",
        "|---|---|---|---|---:|",
    ]
    for model in discover():
        problems, factors = check_units(model)
        if problems:
            continue
        for key in sorted(factors):
            factor = factors[key]
            if abs(factor - 1.0) < 1e-12:
                continue
            node_name = key.split(".")[0]
            node = model.nodes[node_name]
            produced = _produced_unit(model, node_name)
            rows.append(
                f"| `{model.name}` | {node.display} | {produced} | {unit_label(node.unit)} "
                f"| x{factor:,.6g} |"
            )
    if len(rows) == 2:
        rows.append("| | *no model needs a conversion* | | | |")
    return "\n".join(rows)


def _produced_unit(model, node_name: str) -> str:
    """What a node's formula produces before conversion, for the table above."""
    from sizing.evaluate import UNIT_FUNCTIONS, _units_of, _walk, plausible_magnitudes
    from sizing.units import UNITS
    from sizing.units import parse as parse_unit

    magnitudes = plausible_magnitudes(model)
    quantities = {
        name: UNITS.Quantity(magnitudes[name], parse_unit(node.unit))
        for name, node in model.nodes.items()
    }
    node = model.nodes[node_name]
    tree = getattr(node, "formula", None) or getattr(node, "of", None)
    try:
        return unit_label(str(_units_of(_walk(tree, quantities, UNIT_FUNCTIONS))))
    except Exception:  # pragma: no cover - a model that does not typecheck is skipped above
        return "?"


def glossary_table(_name: str = "") -> str:
    """Every term the book rations, and the chapter that introduces it.

    Generated from ``bench/outline.py`` rather than written out, so a term whose chapter moves
    cannot end up pointing at the wrong one. The list is short on purpose: a book that introduces
    forty pieces of vocabulary has taught forty pieces of vocabulary and nothing else.
    """
    from bench.outline import BY_SLUG

    #: term -> (chapter slug, what it means here, and the plain-English phrase it replaces)
    terms = {
        "distribution": (
            "monte_carlo",
            "the bag of values an uncertain quantity could take",
            "a range of plausible values",
        ),
        "sample": ("monte_carlo", "one value drawn from that bag", "one guess"),
        "percentile": (
            "monte_carlo",
            "the value a given fraction of the bag is below",
            "the value nine tenths are under",
        ),
        "interval": ("monte_carlo", "the gap between two percentiles", "how wide the answer is"),
        "correlation": (
            "correlation_and_convergence",
            "the tendency of two inputs to move together",
            "they move together",
        ),
        "convergence": (
            "correlation_and_convergence",
            "the answer ceasing to move between runs",
            "it has settled",
        ),
        "provenance": (
            "where_the_numbers_come_from",
            "how much somebody is claiming when they write a number down",
            "where it came from",
        ),
        "measured constant": (
            "where_the_numbers_come_from",
            "an empirical number belonging to one implementation at one version",
            "a number somebody measured",
        ),
        "ceiling": (
            "regime_changes",
            "a limit past which a chain of multiplications stops describing anything",
            "where it breaks",
        ),
        "headroom": (
            "headroom_and_failure_domains",
            "the margin a design keeps below a ceiling, and the reason for it",
            "the slack you keep",
        ),
        "binding constraint": (
            "bandwidth_and_the_binding_constraint",
            "the chain that decides the answer, out of several that could",
            "whichever runs out first",
        ),
        "utilisation": (
            "queueing_and_the_knee",
            "the fraction of a system that is busy",
            "how busy it is",
        ),
        "unit economics": (
            "unit_economics",
            "a cost divided by a denominator you can defend",
            "cost per something",
        ),
        "structural error": (
            "the_missing_node",
            "a model that is wrong in shape rather than in its numbers",
            "something is missing",
        ),
        "measurement uncertainty": (
            "where_the_numbers_come_from",
            "the standard error beside a number somebody measured",
            "how much the measuring wobbled",
        ),
        "parameter uncertainty": (
            "monte_carlo",
            "not knowing a value in a model whose shape is right",
            "we do not know the number",
        ),
        "scenario uncertainty": (
            "the_sizing_model",
            "the world taking a path the model was not run for, which no interval covers",
            "it might go differently",
        ),
    }
    rows = ["| Term | Introduced in | What it means here | Said plainly |", "|---|---|---|---|"]
    for term, (slug, meaning, plain) in terms.items():
        chapter = BY_SLUG[slug]
        rows.append(f"| **{term}** | [{chapter.label}](#{chapter.anchor}) | {meaning} | {plain} |")
    return "\n".join(rows)
