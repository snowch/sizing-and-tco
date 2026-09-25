"""Stamped results as markdown fragments. No chapter contains a number; they contain these.

Every table here carries a *Source* line, because a figure without one is an anecdote. It went
through two wrong forms before this one, and both failed the same test: could the reader actually
use it?

First it printed the conditions — target, model file, scenario, sample count, seed, result path,
fingerprint, date — across two lines. Three of the eight were identical on every result in the
book, so on ninety tables half the line was the same words again, and the fields somebody would
use to re-run something are only useful to somebody who has cloned the repository and is
therefore not reading the page.

Then it linked the stamped result instead, on the argument that a reader can look rather than
take it on trust. They cannot: a model run stamps every node, every unit conversion, every
scenario and the whole tornado, which comes to two hundred kilobytes of JSON. Offering that as
evidence is offering it in a form nobody can take.

So a model result now links the interactive page built from it, which has the same numbers with a
slider on every input and the scenario, sample count and seed in its header, and which links the
stamp in turn. The JSON has not gone anywhere and has not stopped mattering: it is what
``scripts/verify-numbers.py`` reads on every push, and its fingerprint covers the whole DSL core,
so editing the sampler fails the build until every result is re-run. That is a check for the
machine to run, not a document to hand a reader.

Two things stay on the page rather than going behind the link. A constant nobody has measured is a
fact about the figure, not a filing detail (invariant 3). And what a measured constant was measured
*against* is what the number means.
"""

from __future__ import annotations

import math
from collections import Counter

from bench.stamp import load_result
from sizing.dsl import PROVENANCE_MEANING, discover
from sizing.units import parse as parse_unit

#: How a provenance kind is shown. The symbol is carried into the graph viewer and the tornado so
#: that one glance answers "how much of this model is somebody's guess".
PROVENANCE_MARK = {"fact": "●", "vendor_claim": "◐", "assumption": "○"}

#: What a measurement says about itself, in the order a reader needs it.
MEASURED_KEYS = ("corpus", "codec", "stack", "system", "window")

#: How a verdict is shown. `inside headroom` is the evaluator's word and it reads as reassurance
#: — two readers coming to the book cold took it to mean "comfortable". It means the plan is past
#: the allowed line and spending the reserve that was declared to protect it, so the table says
#: that instead.
VERDICT_MARK = {"ok": "ok", "inside headroom": "into the margin", "over": "**over**"}


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
        # The minus goes before the dollar sign: "$-10,722" is nobody's notation.
        sign = "\u2212" if value < 0 else ""
        if abs(value) >= 1000:
            return f"{sign}${abs(value):,.0f}"
        return f"{sign}${abs(value):,.2f}"
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


#: Where a reader goes to see a stamped result in full. `main` rather than the commit being
#: built: the build stamp in the preface already names that commit, and one mechanism per job.
REPOSITORY = "https://github.com/snowch/sizing-and-tco/blob/main"


def _what_it_measured(name: str) -> list[str]:
    """For a measurement, what the number is *of* — which is not the same as where it is filed.

    A compression ratio belongs to a codec and a body of data. That is what the figure means, so
    it stays on the page rather than going behind a link with the filing details.
    """
    produced = load_result(name).get("produced_by", {})
    keys = list(MEASURED_KEYS)
    # `codec` and `stack` say the same thing on every corpus result here — "zlib 1.3, DEFLATE
    # level 6" beside "python zlib (DEFLATE level 6)". CLAUDE.md says a measured constant names
    # the *implementation* it belongs to, so the stack is the one that survives.
    if produced.get("stack") and produced.get("codec"):
        keys.remove("codec")
    return [str(produced[key]) for key in keys if produced.get(key)]


def _where(name: str) -> str:
    """Where a reader should be sent to check a figure.

    Every result of kind ``model`` has an interactive page built from it under the same name --
    ``scripts/build-viewers.py`` selects on exactly this test -- with a slider on every input and
    the scenario, sample count and seed in its header. That is something a reader can check.

    The stamped JSON is the machine's copy. ``scripts/verify-numbers.py`` reads it on every push
    and fails the build when its fingerprint no longer matches the code that produced it, which is
    the job it exists to do. At two hundred kilobytes of nodes, factors and scenarios it is not
    something a person reads, and sending one there was offering evidence in a form nobody can
    take. The viewer links it for anybody who wants the file itself.

    A corpus measurement has no interactive page, because there is nothing to move: it is one
    number over one declared body of data. Those still point at the stamp, where the corpus and
    the codec are.
    """
    if load_result(name).get("kind") == "model":
        return f"/models/{name}.html"
    return f"{REPOSITORY}/bench/results/{name}.json"


def source(
    name: str | None, *also: str, computed_from: str | None = None, note: str | None = None
) -> str:
    """One line under every figure: where it came from, as a link.

    The name carries the two things worth knowing without following it: `web_service-reference`
    is the model and the scenario. Where the link goes is :func:`_where`'s decision, and it turns
    on whether there is anything a reader can do at the other end.

    Two things stay on the page because they are not filing details. A constant nobody has
    measured is a fact about the figure (invariant 3), and what a measured constant was measured
    *against* is what the number means.
    """
    if name is None:
        return f"*Source — {computed_from or 'this repository'}*"

    names = (name, *also)
    links = [f"[`{one}`]({_where(one)})" for one in names]
    parts = [" and ".join(links)]

    if load_result(name).get("kind") == "model":
        # Said plainly, because on a model result *Source* now names something a reader can do
        # rather than something they can download. A figure may say something else instead:
        # ch01's table is computed from the finished model, and a reader on page one who follows
        # the link should be told that is what they are about to see.
        parts.append(note or "every input on a slider")
    else:
        # What a measurement is of, for the results where that is the point.
        parts += _what_it_measured(name)

    # And the one thing a reader must not have to click for.
    blocked = sum(
        len(load_result(one).get("produced_by", {}).get("unmeasured") or []) for one in names
    )
    if blocked:
        parts.append(f"**{blocked} constant(s) not yet measured**")

    return "*Source — " + " · ".join(parts) + "*"


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


def outputs_table(
    name: str, *only: str, spread: str = "90% interval", ends: tuple[str, str] = ("p5", "p95")
) -> str:
    """What the model says, at a point and across its uncertainty.

    Two columns that a spreadsheet would give one. The point estimate is what a plan is usually
    built on; the interval beside it is the same model saying how much that point is worth.

    ``only`` names the outputs to show, in the order to show them. Without it the table is every
    output the model declares, in the order the model file happens to declare them — which is the
    right table for the chapter that has earned all of them and the wrong one for a page that has
    earned two. A named output that the model does not have raises, so a renamed output fails the
    build rather than silently removing a row from a page that talks about it.
    """
    payload = load_result(name)["summary"]
    labels = row_labels(payload)
    shown = only or tuple(payload["outputs"])
    unknown = [output for output in shown if output not in payload["outputs"]]
    if unknown:
        raise KeyError(f"{name} has no output(s) {unknown}; it declares {payload['outputs']}")
    rows = [
        f"| Output | Point estimate | {spread} | Unit |",
        "|---|---:|---:|---|",
    ]
    for output in shown:
        node = payload["nodes"][output]
        summary = node.get("summary")
        if node.get("blocked_by"):
            # Not a dash because the number is small. A dash because nobody has measured the
            # constant this depends on, and the box below the table says which.
            point = interval = "*not yet measured*"
        else:
            point = fmt(node.get("point"), node["unit"])
            interval = (
                f"{fmt(summary[ends[0]], node['unit'])} to {fmt(summary[ends[1]], node['unit'])}"
                if summary
                else "*fixed*"
            )
        rows.append(f"| {labels[output]} | {point} | {interval} | {unit_label(node['unit'])} |")
    return "\n".join(rows)


def outputs_in_plain_words(name: str, *only: str) -> str:
    """The outputs table for the one chapter that comes before any statistical word (ch01).

    Same rows. The second column is the smallest and the largest of the repeated answers,
    because those are the two numbers that need no convention to read. Every later table
    reports a narrower band than this, and ch13 is where the book says why and names it.
    """
    return outputs_table(name, *only, spread="Smallest and largest answer", ends=("min", "max"))


def stage_outputs(name: str) -> str:
    """What the model says while the book is still building it.

    One column, not two. `outputs_table` puts a 90% interval beside every point estimate, and
    that column is ch13's: a reader in ch02 has not been told what an interval is, and a header
    naming one would be the book teaching a term by using it. The chapters that build the model
    show what it computes; the chapter that teaches sampling adds the second column.
    """
    payload = load_result(name)["summary"]
    labels = row_labels(payload)
    rows = ["| Output | What the model says | Unit |", "|---|---:|---|"]
    for output in payload["outputs"]:
        node = payload["nodes"][output]
        value = (
            "*not yet measured*" if node.get("blocked_by") else fmt(node.get("point"), node["unit"])
        )
        rows.append(f"| {labels[output]} | {value} | {unit_label(node['unit'])} |")
    return "\n".join(rows)


def stage_shape(name: str) -> str:
    """How big the model is at this point in the book, and what the toolkit makes of it.

    The last row is the one the book is built on, and it is not an assertion: `sizing/dsl.py`
    decides it from the file, and `bench/run_models.py` stamps what it decided.
    """
    result = load_result(name)
    payload = result["summary"]
    kinds = Counter(node.get("kind") for node in payload["nodes"].values())
    classification = result["produced_by"]["classification"]
    rows = ["| | |", "|---|---:|"]
    for kind in ("input", "derived", "measured", "ceiling"):
        if kinds.get(kind):
            rows.append(f"| `{kind}` nodes | {kinds[kind]} |")
    rows.append(f"| **What the toolkit calls it** | **{classification} model** |")
    return "\n".join(rows)


def ceilings_table(name: str) -> str:
    """Every declared ceiling, where the plan sits against it, and how often it breaks.

    The last column is the one this book exists for. A sizing answer is not a number; it is a
    number together with how much of the model's own uncertainty puts it over the edge.
    """
    payload = load_result(name)["summary"]
    # Every *declared* ceiling, not only the ones that could be computed. A ceiling whose
    # constant has not been measured used to be dropped here without trace, which is the one
    # place the blocked-state machinery was failing to show a hole — and the observability
    # model's honest ingest ceiling is exactly that case.
    declared = {
        node_name: node
        for node_name, node in payload["nodes"].items()
        if node.get("kind") == "ceiling"
    }
    if not declared:
        return "*This model declares no ceilings. It is a definitional model: see ch01.*"
    rows = [
        "| Ceiling | At the plan | Headroom | Allowed | Limit | Verdict "
        "| Over allowed | Over limit |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for _node_name, node in sorted(declared.items()):
        label = node["label"]
        ceiling = node.get("ceiling")
        if not ceiling:
            rows.append(f"| {label} | *not yet measured* |  |  |  |  |  |  |")
            continue
        rows.append(
            f"| {label} | {ceiling['value']:.2f} | {ceiling['headroom']:.0%} "
            f"| {ceiling['allowed']:.2f} | {ceiling['limit']:.2f} "
            f"| {VERDICT_MARK[ceiling['verdict']]} "
            f"| {ceiling.get('p_over_allowed', 0):.0%} | {ceiling.get('p_over_limit', 0):.0%} |"
        )
    return "\n".join(rows)


def margins_table(name: str) -> str:
    """Every declared ceiling's margin, and the model's own reason for it.

    ``ceilings_table`` says where the plan sits against each ceiling. This says why the margins
    differ: the reason is the ``because`` the model file declares beside each one, so the words
    are the modeller's rather than this book's, and a ceiling declared without a reason shows an
    empty cell rather than one written here.
    """
    payload = load_result(name)["summary"]
    declared = {
        node_name: node
        for node_name, node in payload["nodes"].items()
        if node.get("kind") == "ceiling"
    }
    if not declared:
        return "*This model declares no ceilings. It is a definitional model: see ch01.*"
    rows = ["| Ceiling | Margin | Why this margin |", "|---|---:|---|"]
    for _node_name, node in sorted(declared.items()):
        ceiling = node.get("ceiling")
        if not ceiling:
            rows.append(f"| {node['label']} | *not yet measured* |  |")
            continue
        rows.append(
            f"| {node['label']} | {ceiling['headroom']:.0%} | {ceiling.get('because', '')} |"
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
        "| Hosts | Throughput | If scaling were free | Efficiency | Per host |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in summary["curve"]:
        marker = " **peak**" if row["hosts"] == summary["peak_at_hosts"] else ""
        out.append(
            f"| {row['hosts']:,.0f}{marker} | {row['achievable_throughput']:,.0f} "
            f"| {row['linear_throughput']:,.0f} | {row['scaling_efficiency']:.0%} "
            f"| {row['throughput_per_host']:,.1f} |"
        )
    out.append(
        f"| | | | *swept peak* | *{summary['peak_at_hosts']:,.0f} hosts, against "
        f"{summary['predicted_peak']:,.1f} predicted from the two coefficients* |"
    )
    return "\n".join(out)


def binding_table(name: str) -> str:
    """Which of three chains decides the answer, and how often.

    The last row is the one to read against the three above it. Each chain's median is a
    perfectly good number; the answer is the largest of the three in every draw, and the largest
    of three uncertain numbers sits well above where any one of them usually does.
    """
    s = load_result(name)["summary"]
    return "\n".join(
        [
            "| | |",
            "|---|---:|",
            f"| The request rate decides the host count | {s['requests_binds']:.0%} of samples |",
            f"| The working set decides it | {s['memory_binds']:.0%} of samples |",
            f"| The data on disk decides it | {s['storage_binds']:.0%} of samples |",
            f"| Two chains ask for the same count | {s['tied']:.0%} of samples |",
            f"| Sized on the request chain alone, too small | {s['short_if_requests']:.0%} of samples |",
            f"| Sized on the memory chain alone, too small | {s['short_if_memory']:.0%} of samples |",
            f"| Sized on the disk chain alone, too small | {s['short_if_storage']:.0%} of samples |",
            f"| Median gap between the winner and the runner-up | {s['median_gap']:,.0f} hosts |",
            f"| Gap at the 95th percentile | {s['p95_gap']:,.0f} hosts |",
            f"| Median of the request chain alone | {s['median_requests_hosts']:,.0f} hosts |",
            f"| Median of the memory chain alone | {s['median_memory_hosts']:,.0f} hosts |",
            f"| Median of the disk chain alone | {s['median_storage_hosts']:,.0f} hosts |",
            f"| Median of the largest of the three | {s['median_largest']:,.0f} hosts |",
        ]
    )


# -- Parts I, III and V --------------------------------------------------------------------


def workload_table(name: str) -> str:
    """The quantities that describe the demand, separated from the ones that describe the system.

    A model's inputs are two different kinds of thing wearing the same clothes. Some describe
    what the world is doing to you; the rest describe what you have decided to do about it. A
    table that mixes them is how a sizing conversation ends up arguing about a growth rate as
    though it were a choice.

    Every input says which it is, in its own `decided:` line, and the table files it there. It
    used to guess from whether the input had a shape, which put the busy hour and a vendor's
    quote among the decisions while the viewer on the same page, reading the file, did not.
    """
    payload = load_result(name)["summary"]
    groups: dict[str, list[str]] = {"world": [], "you": [], "definition": []}
    for node_name in payload["order"]:
        node = payload["nodes"][node_name]
        if node["kind"] != "input":
            continue
        groups[node["decided"]].append(
            f"| {node['label']} | {fmt(node.get('point'), node['unit'])} "
            f"| {unit_label(node['unit'])} | {PROVENANCE_MARK.get(node['provenance']['kind'], '?')} |"
        )
    # The last column carries the provenance mark, and carried no heading at all until a
    # reader arriving cold asked what the three symbols were.
    header = ["| Quantity | At the reference point | Unit | Claim |", "|---|---:|---|---|"]
    # An empty half is a fact about the model, not a broken table.
    empty = ["| *none* | | | |"]
    rows = [
        *header,
        "| **What the world does** | | | |",
        *(groups["world"] or empty),
        "| **What you decide** | | | |",
        *(groups["you"] or empty),
    ]
    # A year is a year whoever asks. Nobody decides it, and it is not the world's doing either.
    if groups["definition"]:
        rows += ["| **True by definition** | | | |", *groups["definition"]]
    return "\n".join(rows)


def cost_split_table(name: str) -> str:
    """Capital against running cost, over the declared horizon."""
    payload = load_result(name)["summary"]
    nodes = payload["nodes"]

    def value(key: str) -> float:
        return nodes[key]["point"]

    horizon = value("horizon")
    capex, opex = value("capex"), value("lifecycle_opex")
    total = value("tco")

    def line(label: str, key: str, years: float = 1.0) -> str:
        amount = value(key) * years
        return f"| {label} | {fmt(amount, 'USD')} | {amount / total:.0%} |"

    rows = [
        "| | Amount | Share of the total |",
        "|---|---:|---:|",
        f"| Capital, paid once | {fmt(capex, 'USD')} | {capex / total:.0%} |",
        line("Hosts", "host_capex"),
        line("Network", "network_capex"),
        f"| Running, over {horizon:.0f} years | {fmt(opex, 'USD')} | {opex / total:.0%} |",
        line("Energy", "annual_energy_cost", horizon),
        line("Licences", "annual_licences", horizon),
        line("Support", "annual_support", horizon),
        line("People", "annual_staff_cost", horizon),
        f"| **Total** | **{fmt(total, 'USD')}** | |",
    ]
    return "\n".join(rows)


def node_kinds_table(name: str) -> str:
    """What a model is made of, counted.

    The census that classifies it. A model with no measured constant and no ceiling is a
    definitional model and sampling its inputs is enough; one with either is a conditional model
    and it is not.
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
            if payload["classification"] == "conditional"
            else " — relationships true by definition with uncertain inputs, and sampling the inputs is "
            "sufficient"
        )
        + " |"
    )
    return "\n".join(rows)


# -- appendices ----------------------------------------------------------------------------


#: How units combine: what is multiplied or divided, the unit the answer is read in, and what
#: happened. The registry the build uses works out every result; the last column is the reason.
UNIT_ALGEBRA: tuple[tuple[str, tuple[str, ...], str, str, str], ...] = (
    (
        "a request rate, for a duration",
        ("request/second", "second"),
        "*",
        "request",
        "the seconds cancel: a rate times a duration is an amount",
    ),
    (
        "a request rate, times a plain number",
        ("request/second", "dimensionless"),
        "*",
        "request/second",
        "nothing cancels: a plain number leaves a rate as it was",
    ),
    (
        "disk per host, times the hosts",
        ("TB/host", "host"),
        "*",
        "TB",
        "the hosts cancel: an amount per host times a count of hosts is an amount",
    ),
    (
        "raw data, divided by disk per host",
        ("TB", "TB/host"),
        "/",
        "host",
        "the terabytes cancel and the hosts come up: the last step of a sizing chain",
    ),
    (
        "CPU time per request, times the request rate",
        ("second*core/request", "request/second"),
        "*",
        "core",
        "the requests and the seconds both cancel, leaving cores busy (ch05)",
    ),
    (
        "watts per host, times the hosts, times a building multiplier",
        ("W/host", "host", "dimensionless"),
        "*",
        "W",
        "the hosts cancel and the multiplier changes nothing but the size",
    ),
    (
        "watts, times the hours in a year",
        ("W", "hour/year"),
        "*",
        "kWh/year",
        "power times time is energy, and the build converts to the unit the price is in",
    ),
    (
        "energy, times the price of it",
        ("kWh/year", "USD/kWh"),
        "*",
        "USD/year",
        "the kilowatt-hours cancel: energy times a price is money per year",
    ),
    (
        "a running cost, over the horizon",
        ("USD/year", "year"),
        "*",
        "USD",
        "the years cancel: a rate of spending over a duration is an amount of money",
    ),
    (
        "a per-host licence, times the hosts",
        ("USD/host/year", "host"),
        "*",
        "USD/year",
        "the hosts cancel and the years stay: still a running cost",
    ),
    (
        "a link rate, for a duration, read in bytes",
        ("Mbit/second", "second"),
        "*",
        "MB",
        "the seconds cancel and the build divides by eight, because the link was quoted in bits",
    ),
    (
        "memory per host as the sheet quotes it, times the hosts",
        ("GiB/host", "host"),
        "*",
        "TB",
        "the hosts cancel and the build converts binary gibibytes to decimal terabytes",
    ),
    (
        "a price per terabyte-year, read per month",
        ("USD/TB/year",),
        "*",
        "USD/TB/month",
        "nothing cancels and nothing is wrong: the same dimensions, a twelfth of the size",
    ),
    (
        "the horizon, divided by one year",
        ("year", "year"),
        "/",
        "dimensionless",
        "the years cancel to a plain number, which is the only thing an exponent may be",
    ),
)


def _combine(units: tuple[str, ...], operation: str):
    """The registry's answer to multiplying or dividing the given units, as a quantity of one."""
    from sizing.units import quantity

    result = quantity(1, units[0])
    for unit in units[1:]:
        result = result * quantity(1, unit) if operation == "*" else result / quantity(1, unit)
    return result


def _spelled(units: tuple[str, ...], operation: str) -> str:
    joiner = " × " if operation == "*" else " ÷ "
    return joiner.join(f"`{unit}`" for unit in units)


def unit_algebra_table(_name: str = "") -> str:
    """How units combine and cancel, every result worked out by the build's own registry.

    Nothing in the table is typed: each row multiplies or divides the units it names with
    :mod:`sizing.units` and converts to the unit the answer is read in, and a factor other than
    one is printed because it is what the build would apply. A row that could not be converted
    would raise here, so the page cannot show a combination the registry disagrees with.
    """
    rows = ["| Calculation | The units | Result | What happened |", "|---|---|---|---|"]
    for what, units, operation, target, why in UNIT_ALGEBRA:
        factor = _combine(units, operation).to(target).magnitude
        shown = f"`{target}`"
        if abs(factor - 1.0) > 1e-12:
            shown += f", and the build multiplies by {factor:,.6g}"
        rows.append(f"| {what} | {_spelled(units, operation)} | {shown} | {why} |")
    return "\n".join(rows)


#: What a node declares against what its formula produces, and the three things the check does.
UNIT_VERDICTS: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("a request rate, for a duration", ("request/second", "second"), "*", "request"),
    ("a request rate, times a plain number", ("request/second", "dimensionless"), "*", "request"),
    ("a price per terabyte-year", ("USD/TB/year",), "*", "USD/TB/month"),
    ("watts, times the hours in a year", ("W", "hour/year"), "*", "kWh/year"),
    ("a drive as the sheet quotes it", ("TB",), "*", "TiB"),
    ("a link rate, for a duration", ("Mbit/second", "second"), "*", "MB"),
    ("bytes per span, times spans per request", ("byte/span", "span/request"), "*", "byte/request"),
    ("bytes per span, times spans per request", ("byte/span", "span/request"), "*", "byte/second"),
)


def unit_check_table(_name: str = "") -> str:
    """The three verdicts the unit check can reach, on hand-picked formulas, worked out by it."""
    import pint

    rows = ["| Formula | Produces | Node declares | Verdict |", "|---|---|---|---|"]
    for what, units, operation, declared in UNIT_VERDICTS:
        produced = _combine(units, operation)
        try:
            factor = produced.to(declared).magnitude
        except pint.DimensionalityError:
            verdict = "**refused**: not the same kind of quantity, and no factor makes it one"
        else:
            verdict = (
                "accepted as written"
                if abs(factor - 1.0) < 1e-12
                else f"converted: the build multiplies by {factor:,.6g}"
            )
        rows.append(f"| {what} | {_spelled(units, operation)} | `{declared}` | {verdict} |")
    return "\n".join(rows)


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


#: Every term the book rations: term -> (the chapter that introduces it, what it means here,
#: and the plain-English phrase it replaces). The glossary table is rendered from this, and
#: the site links a term's first mention on any page after that chapter to its entry.
GLOSSARY: dict[str, tuple[str, str, str]] = {
    "definitional model": (
        "point_estimates",
        "a model built only from relationships true by definition, so sampling its inputs is enough",
        "it can only be wrong through its inputs",
    ),
    "conditional model": (
        "point_estimates",
        "a model with a measured constant or a ceiling in it, which must keep headroom below each "
        "ceiling",
        "every input can be right and the answer still wrong",
    ),
    "distribution": (
        "monte_carlo",
        "the bag of values an uncertain quantity could take",
        "a range of plausible values",
    ),
    "flow": (
        "what_a_workload_is",
        "a rate — requests per second, bytes per second, dollars per year",
        "something that arrives",
    ),
    "duration": (
        "what_a_workload_is",
        "a length of time — a horizon, a retention period, the time one request spends in the system",
        "how long",
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
    "sizing chain": (
        "what_a_workload_is",
        "the string of multiplications that runs from a workload to a number of machines",
        "how you calculate hosts needed",
    ),
    "stock": (
        "what_a_workload_is",
        "a level — terabytes held, series alive, requests in flight",
        "how much there is right now",
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


def glossary_table(_name: str = "") -> str:
    """Every term the book rations, and the chapter that introduces it.

    Generated from ``bench/outline.py`` rather than written out, so a term whose chapter moves
    cannot end up pointing at the wrong one. The list is short on purpose: a book that introduces
    forty pieces of vocabulary has taught forty pieces of vocabulary and nothing else.
    """
    from bench.outline import BY_SLUG

    rows = ["| Term | Introduced in | What it means here | Said plainly |", "|---|---|---|---|"]
    for term, (slug, meaning, plain) in GLOSSARY.items():
        chapter = BY_SLUG[slug]
        rows.append(f"| **{term}** | [{chapter.label}](#{chapter.anchor}) | {meaning} | {plain} |")
    return "\n".join(rows)


def formulas_table(_name: str | None, model_name: str) -> str:
    """Every formula in a model, in the file's order, with the chapter that introduced it.

    A summary of the formulas, made the only way this book adds a table: as a view of the
    model file rather than a copy of it, so that ``make check`` regenerates it and it cannot
    say anything the file no longer says. A ceiling is listed with what it watches, its limit
    and its margin. The last column comes from the model's build order, and a model the book
    does not build across chapters has no such column.
    """
    from bench.outline import BY_SLUG
    from bench.stages import model_path, staged_models, stages
    from sizing.dsl import Ceiling, Derived, load_model

    model = load_model(model_path(model_name))
    introduced: dict[str, str] = {}
    staged = model_name in staged_models()
    if staged:
        for stage in stages(model_name):
            for node_name in stage.introduces:
                introduced.setdefault(node_name, stage.chapter)
    head = "| Quantity | Formula | Unit |" + (" Introduced in |" if staged else "")
    rows = [head, "|---|---|---|" + ("---|" if staged else "")]
    for name, node in model.nodes.items():
        if isinstance(node, Derived):
            formula = f"`{node.formula_text}`"
        elif isinstance(node, Ceiling):
            formula = f"`{node.of_text}` against a limit of `{node.limit_text}`"
            if node.headroom_text:
                formula += f", keeping `{node.headroom_text}` below it"
        else:
            continue
        row = f"| {node.display} (`{name}`) | {formula} | {unit_label(node.unit)} |"
        if staged:
            chapter = BY_SLUG.get(introduced.get(name, ""))
            row += f" [{chapter.label}](#{chapter.anchor}) |" if chapter else " |"
        rows.append(row)
    return "\n".join(rows)


# -- two quotes for one workload (ch22) ------------------------------------------------------


#: How a quote's units read in a table. Local to these tables: the rest of the book prints an
#: input's unit as the model spells it, and changing that would move every table that does.
QUOTE_UNITS = {
    "core/host": "cores per host",
    "GiB/host": "GiB per host",
    "TB/host": "TB per host",
    "USD/host": "per host",
    "W/host": "W per host",
    "USD/core/year": "per core per year",
    "USD/host/year": "per host per year",
    "1/year": "of capital, per year",
    "host": "hosts",
    "USD": "",
}


def signed_money(value: float) -> str:
    """A difference in money: signed, to the dollar, and never "$-": a minus goes before the sign."""
    if abs(value) < 0.5:
        return "$0"
    sign = "\u2212" if value < 0 else "+"
    return f"{sign}${abs(value):,.0f}"


def _quoted(row: dict) -> str:
    unit, value = row["unit"], row["value"]
    if unit == "1/year":
        return f"{value:.1%} {QUOTE_UNITS[unit]}"
    if unit == "USD" and value == 0:
        return "$0, declared"
    if unit == "USD/core/year" and value == 0:
        return "$0 per core, declared"
    if unit == "USD/host/year" and value == 0:
        return "$0 per host, declared"
    if unit == "host":
        return f"{value:,.0f} hosts" if float(value).is_integer() else f"{value:,.1f} hosts"
    if unit == "dimensionless":
        return f"{value:.3g}"
    if unit in ("core/host", "GiB/host", "TB/host", "W/host"):
        shown = f"{value:,.0f}" if float(value).is_integer() else f"{value:.3g}"
        return f"{shown} {QUOTE_UNITS[unit]}"
    if unit == "USD/kWh":
        return f"${value:.3f} per kWh"
    return f"{fmt(value, unit)} {QUOTE_UNITS.get(unit, unit)}".rstrip()


def comparison_quotes(name: str) -> str:
    """The two quotes, line by line, with what kind of claim each line is.

    Both sides carry a mark, and most of both sides carry the same mark: a quote is a vendor's
    claim whoever the vendor is. The two lines that are not are the ones a buyer supplied.
    """
    designs = load_result(name)["summary"]["designs"]
    left = {row["input"]: row for row in designs["incumbent"]["quote"]}
    right = {row["input"]: row for row in designs["challenger"]["quote"]}
    rows = [
        "| Line | The incumbent's quote | The challenger's quote |",
        "|---|---:|---:|",
    ]
    for key, row in left.items():
        other = right[key]
        rows.append(
            f"| {row['label']} | {PROVENANCE_MARK[row['provenance']]} {_quoted(row)} "
            f"| {PROVENANCE_MARK[other['provenance']]} {_quoted(other)} |"
        )
    marks = " · ".join(
        f"{mark} {PROVENANCE_MEANING[kind]}" for kind, mark in PROVENANCE_MARK.items()
    )
    rows.append(f"| | {marks} | |")
    return "\n".join(rows)


def _money(value: float) -> str:
    return "$0" if abs(value) < 0.5 else fmt(value, "USD")


def comparison_lines(name: str) -> str:
    """Where the money moves: every line of both totals, over the same horizon, and the gap."""
    lines = load_result(name)["summary"]["lines"]
    rows = [
        "| Over five years | Incumbent | Challenger | Challenger minus incumbent |",
        "|---|---:|---:|---:|",
    ]
    for row in lines:
        label = f"**{row['label']}**" if row["node"] == "tco" else row["label"]
        gap = "none" if abs(row["difference"]) < 0.5 else signed_money(row["difference"])
        rows.append(
            f"| {label} | {_money(row['incumbent'])} | {_money(row['challenger'])} "
            f"| {'**' + gap + '**' if row['node'] == 'tco' else gap} |"
        )
    return "\n".join(rows)


def comparison_paired(name: str) -> str:
    """The difference between the two totals, four ways, only one of which is honest.

    The first row is what a spreadsheet prints. The second is what the model says about the
    difference when both designs face the same future. The third and fourth are what a reader
    gets by subtracting two independent intervals, which is the mistake two totals side by side
    invite (ch22).
    """
    summary = load_result(name)["summary"]
    node, paired = summary["nodes"]["difference"], summary["paired"]
    spread = node["summary"]

    def span(low: float, high: float) -> str:
        return f"{signed_money(low)} to {signed_money(high)}"

    rows = [
        "| Challenger minus incumbent, five-year total | |",
        "|---|---:|",
        f"| At the point estimate | {signed_money(node['point'])} |",
        f"| Across the same futures, middle nine in ten | **{span(spread['p5'], spread['p95'])}** |",
        f"| With each design in a future of its own | "
        f"{span(paired['independent']['p5'], paired['independent']['p95'])} |",
        f"| Subtracting the ends of the two intervals | "
        f"{span(paired['ends']['low'], paired['ends']['high'])} |",
        f"| Futures in which the challenger is cheaper | {paired['share_challenger_cheaper']:.0%} |",
        f"| Futures in which the incumbent is cheaper | {paired['share_incumbent_cheaper']:.0%} |",
    ]
    return "\n".join(rows)


def comparison_ceilings(name: str) -> str:
    """How often each design copes, side by side. Cheaper is a claim about a fleet that works."""
    designs = load_result(name)["summary"]["designs"]
    left, right = designs["incumbent"]["ceilings"], designs["challenger"]["ceilings"]
    rows = [
        "| Ceiling | Incumbent | Challenger |",
        "|---|---:|---:|",
    ]

    def cell(report: dict) -> str:
        return (
            f"{report['p_over_limit']:.0%} over its limit<br>"
            f"*{report['p_over_allowed']:.0%} past the allowed line*"
        )

    for key, report in left.items():
        rows.append(f"| {report['label']} | {cell(report)} | {cell(right[key])} |")
    return "\n".join(rows)


def comparison_break_even(name: str) -> str:
    """Where the two totals tie, input by input, and whether that value is one to worry about."""
    rows_in = load_result(name)["summary"]["break_even"]
    rows = [
        "| Input | Whose | As quoted, or at the point | The totals tie at | Verdict |",
        "|---|---|---:|---:|---|",
    ]
    for row in rows_in:
        unit = row["unit"]
        at = _quoted({"value": row["at"], "unit": unit})
        if row["ties_at"] is None:
            tie, verdict = "—", "no value of it moves the difference"
        else:
            tie = _quoted({"value": row["ties_at"], "unit": unit})
            if row["input"] == "staff_fte":
                verdict = (
                    f"{row['from_quote']:+.1%} of an engineer's time, on the challenger's side"
                )
            elif row["whose"] == "challenger":
                verdict = f"{row['from_quote']:+.1%} on the quote"
            elif row["in_swing"]:
                verdict = "inside the middle eighty per cent of what it could be"
            elif row["in_range"]:
                verdict = "outside the middle eighty per cent, inside the range the model admits"
            else:
                verdict = "outside the range the model admits"
        if row["input"] == "staff_fte":
            whose = "a claim about your people"
        elif row["whose"] == "challenger":
            whose = "the challenger's quote"
        else:
            whose = "shared by both"
        rows.append(f"| {row['label']} | {whose} | {at} | {tie} | {verdict} |")
    return "\n".join(rows)
