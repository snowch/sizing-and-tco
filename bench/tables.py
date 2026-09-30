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

import inspect
import math
import re
from collections import Counter

import yaml

from bench.stamp import ROOT, load_result
from sizing import mc
from sizing.dsl import PROVENANCE_MEANING, discover
from sizing.units import parse as parse_unit

#: How a provenance kind is shown. The symbol is carried into the graph viewer and the tornado so
#: that one glance answers "how much of this model is somebody's guess".
PROVENANCE_MARK = {"fact": "●", "vendor_claim": "◐", "assumption": "○"}

#: The short form of each mark, for the key under a table. PROVENANCE_MEANING is the long form.
CLAIM_KEY = {
    "fact": "traceable to a measurement or a definition",
    "vendor_claim": "supplied by the vendor selling it",
    "assumption": "an assumption",
}

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
    if "[currency_" in dimensions:
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
        "second * core / request": "core-seconds / request",
    }
    return pretty.get(unit, unit)


def _with_unit(label: str, unit: str) -> str:
    """A column heading that says what its figures are in, where the cells do not.

    Money carries its own mark in every cell, a count says what it counts in its label, and a
    label that already names its unit (*active series*, in series) does not need it twice. What
    is left is a column of large figures with nothing to say whether they are kilowatt-hours a
    year or dollars, which is how ch16's energy table was read.
    """
    shown = unit_label(unit)
    if (
        not shown
        or unit in ("node", "drive", "core", "host")
        or shown in label
        or "[currency_" in str(parse_unit(unit).dimensionality)
    ):
        return label
    return f"{label} ({shown})"


def _value_with_unit(value: float, unit: str) -> str:
    """A value with its unit after it, unless `fmt` has already marked it as money."""
    shown = fmt(value, unit)
    label = unit_label(unit)
    if not label or "[currency_" in str(parse_unit(unit).dimensionality):
        return shown
    return f"{shown} {label}"


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
    return [_code_names(str(produced[key])) for key in keys if produced.get(key)]


#: A dotted module name, such as `sizing.mc`, set as code. As plain text MyST read it as a web
#: address -- `.mc` is a country's domain -- and linked every Source line naming the sampler to
#: a site in Monaco.
MODULE_NAME = re.compile(r"(?<![`\w.])([a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)+)(?![`\w])")


def _code_names(text: str) -> str:
    return MODULE_NAME.sub(r"`\1`", text)


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
    # A list, not a chain of "and"s: a table drawn from four results read as a run-on.
    parts = [links[0] if len(links) == 1 else ", ".join(links[:-1]) + " and " + links[-1]]

    if load_result(name).get("kind") == "model":
        # Said plainly, because on a model result *Source* now names something a reader can do
        # rather than something they can download. A figure may say something else instead:
        # ch01's table is computed from the finished model, and a reader on page one who follows
        # the link should be told that is what they are about to see.
        parts.append(note or "the model to explore; each input with a range has a slider")
    else:
        # What a measurement is of, for the results where that is the point.
        parts += _what_it_measured(name)

    # And the one thing a reader must not have to click for.
    # Counted once per model and constant: two scenarios of one model share their constants.
    blocked = len(
        {
            (load_result(one).get("summary", {}).get("model", one), constant)
            for one in names
            for constant in load_result(one).get("produced_by", {}).get("unmeasured") or []
        }
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


#: ch01's taxi example, which problem 1.2's test reads too.
COMMUTE = ROOT / "tests" / "point_estimates" / "fixtures" / "commute.yaml"
#: The commute table's words: the first column's heading, its first and last rows, the suffix on
#: a row where one input moves alone, and the last column's heading.
COMMUTE_WORDS = {
    "moves": "What moves to its most",
    "nothing": "Nothing: the usual commute",
    "alone": "{name} only",
    "everything": "Everything",
    "total": "Fares for the year",
}


def commute_table(_name: None = None) -> str:
    """ch01's taxi example: a year's fares with each input moved alone, then all of them at once.

    Rendered from the file problem 1.2 is graded against, so the page and the test cannot
    disagree about the example. There is no column of multiples: working those out from the
    fares is the problem.
    """
    raw = yaml.safe_load(COMMUTE.read_text())
    names = list(raw)
    usual = {name: float(raw[name]["usual"]) for name in names}
    most = {name: float(raw[name]["most"]) for name in names}
    cases = [(COMMUTE_WORDS["nothing"], usual)]
    cases += [
        (COMMUTE_WORDS["alone"].format(name=name.capitalize()), {**usual, name: most[name]})
        for name in names
    ]
    cases.append((COMMUTE_WORDS["everything"], most))

    def shown_as(name: str, value: float) -> str:
        return f"£{value:,.2f}" if raw[name].get("pounds") else f"{value:,.0f}"

    rows = [
        f"| {COMMUTE_WORDS['moves']} | "
        + " | ".join(raw[name]["label"].capitalize() for name in names)
        + f" | {COMMUTE_WORDS['total']} |",
        "|---|" + "---:|" * (len(names) + 1),
    ]
    for label, values in cases:
        cells = " | ".join(shown_as(name, values[name]) for name in names)
        rows.append(f"| {label} | {cells} | £{math.prod(values.values()):,.0f} |")
    return "\n".join(rows)


def stage_outputs(name: str, *only: str) -> str:
    """What the model says while the book is still building it.

    One column, not two. `outputs_table` puts a 90% interval beside every point estimate, and
    that column is ch13's: a reader in ch02 has not been told what an interval is, and a header
    naming one would be the book teaching a term by using it. The chapters that build the model
    show what it computes; the chapter that teaches sampling adds the second column.

    ``only`` names the outputs to show, in order, as in `outputs_table`, and a name the model
    does not declare raises.
    """
    payload = load_result(name)["summary"]
    labels = row_labels(payload)
    shown = only or tuple(payload["outputs"])
    unknown = [output for output in shown if output not in payload["outputs"]]
    if unknown:
        raise KeyError(f"{name} has no output(s) {unknown}; it declares {payload['outputs']}")
    rows = ["| Output | What the model says | Unit |", "|---|---:|---|"]
    for output in shown:
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


def ceilings_table(name: str, *only: str) -> str:
    """Every declared ceiling, where the plan sits against it, and how often it breaks.

    The last column is the one this book exists for. A sizing answer is not a number; it is a
    number together with how much of the model's own uncertainty puts it over the edge.

    ``only`` names the ceilings to show, in the order to show them, for a page whose argument is
    about some of them. Without it the table is every declared ceiling, sorted by name. A named
    ceiling the model does not declare raises, so a rename fails the build rather than silently
    dropping a row from a page that talks about it.
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
    unknown = [node_name for node_name in only if node_name not in declared]
    if unknown:
        raise KeyError(f"{name} declares no ceiling(s) {unknown}; it declares {sorted(declared)}")
    shown = [(node_name, declared[node_name]) for node_name in only] or sorted(declared.items())
    rows = [
        "| Ceiling | At the plan | Headroom | Allowed | Limit | Verdict "
        "| Over allowed | Over limit |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for _node_name, node in shown:
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


#: The band table's headings, in the model viewer's plain words for the two ends.
BANDS_HEADER = (
    "| Quantity | 1 future in 20 is below | 1 in 20 is above | Top ÷ bottom |",
    "|---|---:|---:|---:|",
)


def bands_in_plain_words(name: str, *nodes: str) -> str:
    """Each named quantity's band across the futures, and its top divided by its bottom.

    For a page before ch13, in the model viewer's plain words: the band runs from the value one
    future in twenty comes in under to the one that one future in twenty comes in over. The last
    column is the band's width as a ratio, because a ratio is what multiplying compounds: a
    product's band can be set against its inputs' bands on that scale and on no other.

    ``nodes`` names the rows, in order. A node with one value in every future has no band, and
    raises rather than printing a row of equal ends.
    """
    payload = load_result(name)["summary"]
    unknown = [node_name for node_name in nodes if node_name not in payload["nodes"]]
    if not nodes or unknown:
        raise KeyError(f"{name}: name the rows to show; unknown: {unknown}")
    rows = list(BANDS_HEADER)
    for node_name in nodes:
        node = payload["nodes"][node_name]
        summary = node.get("summary")
        if not summary:
            raise KeyError(f"{name}: {node_name} has one value in every future, so no band")
        low, high = summary["p5"], summary["p95"]
        rows.append(
            f"| {node['label']} | {fmt(low, node['unit'])} | {fmt(high, node['unit'])} "
            f"| {high / low:.1f}x |"
        )
    return "\n".join(rows)


#: The spread table's three headings: the quantity, its 90% interval, and the top over the bottom.
SPREAD_HEADINGS = ("Quantity", "90% interval", "Top ÷ bottom")


def spread_table(name: str, *nodes: str) -> str:
    """How wide each named quantity is: its 90% interval, and the top of it over the bottom.

    For the factors of a product and the product itself, on a page after ch13 (the plain-words
    form is :func:`bands_in_plain_words`). The question a reader brings is whether the product is
    wider than its factors and by how much, and a ratio answers it on any scale: factors
    multiply, so their spreads compare by division. A node the result does not have, or one with
    no sampled range, raises rather than printing a row with nothing in it.
    """
    payload = load_result(name)["summary"]
    unknown = [node_name for node_name in nodes if node_name not in payload["nodes"]]
    if not nodes or unknown:
        raise KeyError(f"{name}: name the rows to show; unknown: {unknown}")
    rows = ["| " + " | ".join(SPREAD_HEADINGS) + " |", "|---|---:|---:|"]
    for node_name in nodes:
        node = payload["nodes"][node_name]
        summary = node.get("summary")
        if node.get("blocked_by") or not summary:
            raise KeyError(f"{name}: {node_name} has no sampled range")
        low, high = summary["p5"], summary["p95"]
        rows.append(
            f"| {_named(node, node_name)} | {fmt(low, node['unit'])} to {fmt(high, node['unit'])} "
            f"| {high / low:.1f}x |"
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


def _named(node: dict, node_name: str) -> str:
    """A node's label with its identifier under it, in one cell.

    Formulas and problems refer to a node by its identifier and the tables show its label; a
    reader matching one to the other needs both, and a column of its own would widen every
    table that has them on a phone.
    """
    return f"{node['label']}<br>`{node_name}`"


#: The line standing in for the rows of one provenance kind a page leaves out.
OMITTED = "*{count} more, not listed here*"


def provenance_table(name: str, *kinds: str) -> str:
    """Every input, by how much somebody is claiming when they wrote it down.

    The count at the bottom is the honest summary of any model: this many of the numbers are
    traceable, this many are somebody's sales material, and this many were decided in a meeting.

    ``kinds`` names the provenance kinds to list, for a page that has earned those rows and not
    the rest. The rows it leaves out are counted in one line, and the tally still counts every
    input, so a shorter table cannot make a model look better sourced than it is.
    """
    unknown = [kind for kind in kinds if kind not in PROVENANCE_MEANING]
    if unknown:
        raise KeyError(f"no provenance kind(s) {unknown}; there are {list(PROVENANCE_MEANING)}")
    payload = load_result(name)["summary"]
    counts: dict[str, int] = {}
    rows = ["| | Input | Provenance | Source |", "|---|---|---|---|"]
    for node_name in payload["order"]:
        node = payload["nodes"][node_name]
        if node["kind"] != "input":
            continue
        kind = node["provenance"]["kind"]
        counts[kind] = counts.get(kind, 0) + 1
        if kinds and kind not in kinds:
            continue
        source = node["provenance"]["source"].replace("\n", " ").strip()
        rows.append(
            f"| {PROVENANCE_MARK.get(kind, '?')} | {_named(node, node_name)} "
            f"| {kind.replace('_', ' ')} | {source} |"
        )
    for kind in PROVENANCE_MEANING:
        if kinds and kind not in kinds and counts.get(kind):
            rows.append(
                f"| {PROVENANCE_MARK[kind]} | {OMITTED.format(count=counts[kind])} "
                f"| {kind.replace('_', ' ')} | |"
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
    for node_name, node in sorted(measured.items()):
        found = node.get("measured")
        if not found:
            rows.append(
                f"| {_named(node, node_name)} | *not yet measured* | — "
                f"| {unit_label(node['unit'])} "
                f"| `bench/results/{node['result']}.json` does not exist |"
            )
            continue
        rows.append(
            f"| {_named(node, node_name)} | {fmt(found['value'], node['unit'])} "
            f"| ± {fmt(found['sd'], node['unit'])} | {unit_label(node['unit'])} "
            f"| {found['stack']} |"
        )
    return "\n".join(rows)


#: The claim-beside-measurement table's headings, and what its last column says of a measured
#: constant: what took it, or that its result does not exist yet.
CLAIM_HEADER = (
    "| | Quantity | What the model says | Unit | Where it comes from |",
    "|---|---|---:|---|---|",
)
CLAIM_MEASURED = "measured: {stack}"
CLAIM_UNMEASURED = "measured: `bench/results/{result}.json` does not exist"


def claim_beside_measurement(name: str, *nodes: str) -> str:
    """One quantity as a vendor quoted it and as it was measured, and what each lets the model
    compute.

    The page names the rows, in its order. A node the model cannot compute is shown as *not yet
    measured*, never filled in, so the row that rests on a claim and the row that waits for a
    measurement sit side by side. A named node the model does not have raises, so a rename fails
    the build rather than dropping a row from a page that talks about it.
    """
    payload = load_result(name)["summary"]
    unknown = [node_name for node_name in nodes if node_name not in payload["nodes"]]
    if not nodes or unknown:
        raise KeyError(f"{name}: name the rows to show; unknown: {unknown}")
    rows = list(CLAIM_HEADER)
    for node_name in nodes:
        node = payload["nodes"][node_name]
        mark = ""
        if node["kind"] == "input":
            kind = node["provenance"]["kind"]
            mark, origin = PROVENANCE_MARK[kind], kind.replace("_", " ")
        elif node["kind"] == "measured":
            found = node.get("measured")
            origin = (
                CLAIM_MEASURED.format(stack=found["stack"])
                if found
                else CLAIM_UNMEASURED.format(result=node["result"])
            )
        else:
            origin = f"`{node['formula']}`"
        value = (
            "*not yet measured*" if node.get("blocked_by") else fmt(node.get("point"), node["unit"])
        )
        rows.append(
            f"| {mark} | {node['label']} | {value} | {unit_label(node['unit'])} | {origin} |"
        )
    return "\n".join(rows)


def tornado_table(
    name: str,
    output: str,
    limit: int = 8,
    ends: tuple[str, str] = ("at its p10", "at its p90"),
    moving_only: bool = False,
    heading: str | None = None,
    count_still: bool = False,
) -> str:
    """Which input moves one output most, when swung on its own across its middle 80%.

    ``moving_only`` drops the inputs whose swing is zero before ``limit`` applies; with
    ``count_still`` as well, one last row counts them, as the tornado chart does. ``heading``
    replaces the output's label, with its unit, over the third column.
    """
    payload = load_result(name)["summary"]
    declared = payload["tornado"].get(output, [])
    bars = [bar for bar in declared if bar["span"] > 0] if moving_only else declared
    bars = bars[:limit]
    if not bars:
        return f"*No uncertain input feeds `{output}`.*"
    unit = payload["nodes"][output]["unit"]
    title = heading or _with_unit(payload["nodes"][output]["label"], unit)
    rows = [
        f"| Input | Kind | {title} {ends[0]} | {ends[1]} | Swing |",
        "|---|---|---:|---:|---:|",
    ]
    for bar in bars:
        rows.append(
            f"| {bar['label']} | {bar['kind']} | {fmt(bar['low'], unit)} "
            f"| {fmt(bar['high'], unit)} | {fmt(bar['span'], unit)} |"
        )
    still = sum(1 for bar in declared if bar["span"] <= 0)
    if moving_only and count_still and still:
        rows.append(f"| {STILL_ROW.format(count=still)} | | | | 0 |")
    return "\n".join(rows)


#: The row that counts the inputs a tornado table leaves out because they do not move the output.
STILL_ROW = "*{count} more with a range, which do not reach it*"


def tornado_of_what_reaches(name: str, output: str) -> str:
    """The tornado table with the same bars the chart beside it draws, and the rest counted.

    For an output some inputs cannot reach. Appendix F's table printed the first eight of twelve
    bars, four of them zero and chosen by sort order, beside a chart that drew the four that move
    it and said how many do not.
    """
    return tornado_table(name, output, moving_only=True, count_still=True)


#: The straight-line table's headings, and the name of each row's point in the growth band.
STRAIGHT_LINE_HEADINGS = (
    "Annual growth factor",
    "Held at the horizon (times day one)",
    "Straight-line average (times day one)",
    "Compounding average (times day one)",
    "Straight line too high by",
)
STRAIGHT_LINE_POINTS = ("p10", "median", "p90")


def straight_line_overstatement(_name: str | None, model_name: str) -> str:
    """How far a straight line from day one to the horizon overstates a compounding holding (ch17).

    A holding that compounds at a steady factor ``g`` a year for ``n`` years sits at ``g ** t``
    times day one's in year ``t``. Its average over the horizon is ``(g ** n - 1) / ln(g ** n)``
    times day one's; the straight line between the two ends averages ``(1 + g ** n) / 2``. The
    rows are the model's own growth band: its declared p10 and p90, and the median between them,
    which for a lognormal is their geometric mean. Every holding is a multiple of day one's, so
    the table holds for any starting size, and for the request rate, which grows by the same
    factor.

    It reads the declared band, not a slider, so the zero-over-zero case that keeps the exact
    average out of the model (a factor of one) cannot reach it: the declared p10 is above one.
    """
    from bench.stages import model_path
    from sizing.dsl import load_model

    model = load_model(model_path(model_name))
    growth = model.nodes["annual_growth"].distribution["lognormal"]
    horizon = model.nodes["horizon"]
    if horizon.unit != "year":
        raise ValueError(f"{model_name}: the horizon is in {horizon.unit}, not years")
    low, high = growth["p10"], growth["p90"]
    rows = [
        "| " + " | ".join(STRAIGHT_LINE_HEADINGS) + " |",
        "|---|---:|---:|---:|---:|",
    ]
    factors = (low, math.sqrt(low * high), high)
    for where, factor in zip(STRAIGHT_LINE_POINTS, factors, strict=True):
        end = factor**horizon.value
        line = (1 + end) / 2
        curve = (end - 1) / math.log(end)
        rows.append(
            f"| {where}, {fmt(factor)} | x{fmt(end)} | x{fmt(line)} | x{fmt(curve)} "
            f"| {line / curve - 1:.0%} |"
        )
    return "\n".join(rows)


#: Where the tornado swung each input, in words a page before ch13 has defined beside the table.
PLAIN_ENDS = ("with the input at its low end", "at its high end")


def tornado_in_plain_words(name: str, output: str, limit: int = 8) -> str:
    """The tornado table for a chapter that comes before ch13 names a percentile.

    Same rows. The two middle columns say where the input was set in words ch04 defines beside
    the table: its low end, which one future in ten comes in under, and its high end, which one
    in ten comes in over. ``limit`` caps the rows, as in :func:`tornado_table`.
    """
    return tornado_table(name, output, limit, ends=PLAIN_ENDS)


#: ch19's residence table: the heading over its third column, with the unit a duration's cells
#: do not carry.
RESIDENCE_HEADING = "residence time in seconds"


def tornado_of_what_moves(name: str, output: str, heading: str) -> str:
    """A tornado table of only the inputs that move the output, under a heading that has its unit.

    For an output few inputs reach. Padded to eight rows with inputs whose swing is zero, ch19's
    residence table listed five that do not move it, beside prose saying nothing else does.
    """
    return tornado_table(name, output, moving_only=True, heading=heading)


#: The five quantiles a stamped summary keeps, with the share of futures below each, and that
#: share in words. A result holds no draws, so these points are all a page can say from it.
_QUANTILES = (("p5", 0.05), ("p25", 0.25), ("p50", 0.5), ("p75", 0.75), ("p95", 0.95))
SHARE_WORDS = {
    0.05: "one in twenty",
    0.25: "a quarter",
    0.5: "half",
    0.75: "three quarters",
    0.95: "nineteen in twenty",
}
#: The share-past table's column heading, and how its one cell reads at each kind of bound.
SHARE_HEADER = "Futures the model drew"
SHARE_EVERY = "every one"
SHARE_NONE = "none"
SHARE_AT_MOST = "some, and no more than {high}"
SHARE_MORE_THAN = "more than {low}"
SHARE_BETWEEN = "more than {low}, and no more than {high}"


def share_past(name: str, node: str, threshold: float, what: str) -> str:
    """How often a node ends up past a threshold, as a bound the stamped quantiles make exact.

    The result keeps a summary, not the draws, so the share cannot be counted here. It can be
    bounded: if the 75th percentile is above the threshold, more than a quarter of the futures
    are; if the median is not, no more than half are. That bound is exact, it is read from the
    stamp, and it moves when the model does, which a share typed into the prose would not.
    """
    summary = load_result(name)["summary"]["nodes"][node]["summary"]
    if summary["min"] > threshold:
        share = SHARE_EVERY
    elif summary["max"] <= threshold:
        share = SHARE_NONE
    else:
        above = [q for key, q in _QUANTILES if summary[key] > threshold]
        not_above = [q for key, q in _QUANTILES if summary[key] <= threshold]
        low = SHARE_WORDS[round(1 - min(above), 2)] if above else None
        high = SHARE_WORDS[round(1 - max(not_above), 2)] if not_above else None
        if low is None:
            share = SHARE_AT_MOST.format(high=high)
        elif high is None:
            share = SHARE_MORE_THAN.format(low=low)
        else:
            share = SHARE_BETWEEN.format(low=low, high=high)
    return "\n".join([f"| | {SHARE_HEADER} |", "|---|---|", f"| {what} | {share} |"])


#: The value-of-information table's headings, and its two closing rows.
INFORMATION_HEADINGS = (
    "If this were known exactly",
    "Removed, if found at its low end",
    "at its middle",
    "at its high end",
)
INFORMATION_EVERYTHING = "every one of them"
INFORMATION_TOTAL = ("the rows above total {total}", "and are not shares of anything")


def _share_removed(value: float) -> str:
    """A share of the interval removed, where a removal a hair below zero prints as 0%, not -0%.

    Rounded before it is formatted; a negative share keeps a true minus sign, because it means
    the interval came back wider.
    """
    return f"{round(value, 2) + 0.0:.0%}".replace("-", "\u2212")


def value_of_information_table(name: str, model: str, output: str) -> str:
    """What knowing one input exactly would do to the interval, by where the knowledge landed.

    A perfect measurement can come back anywhere in the input's band, and where it lands decides
    what it removes. So each input is pinned three times: at the two ends the tornado swings it
    between, and at its median. A negative share means the interval came back wider: an input that
    multiplies others, found high, scales up their spread. No column is the most a measurement
    could remove.

    The middle column's total is printed because it is not a hundred per cent. The rows are not
    shares of anything; a chain of multiplications does not divide its uncertainty between its
    inputs (ch19).
    """
    payload = load_result(name)["summary"]
    rows = [row for row in payload["rows"] if row["model"] == model and row["output"] == output]
    totals = next(
        (t for t in payload["totals"] if t["model"] == model and t["output"] == output), None
    )
    if not rows or totals is None:
        return f"*Nothing uncertain feeds `{output}` in `{model}`.*"
    everything = 1.0 - totals["all_known"] / totals["half_width"] if totals["half_width"] else 1.0
    out = ["| " + " | ".join(INFORMATION_HEADINGS) + " |", "|---|---:|---:|---:|"]
    for row in sorted(rows, key=lambda r: -r["removed"]):
        out.append(
            f"| {row['label']} | {_share_removed(row['removed_low'])} "
            f"| {_share_removed(row['removed'])} | {_share_removed(row['removed_high'])} |"
        )
    out.append(f"| **{INFORMATION_EVERYTHING}** | | **{_share_removed(everything)}** | |")
    total, shares = INFORMATION_TOTAL
    out.append(
        f"| | | *{total.format(total=_share_removed(totals['sum_of_removals']))}* | *{shares}* |"
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
        # The unit beside the name, as the book's other input tables give it: "9,905" on its own
        # is a count of nothing. In the cell rather than a column, to keep the table narrow.
        rows.append(
            f"| {_with_unit(row['label'], unit)} | {fmt(row['overall'], unit)} "
            f"| {fmt(row['in_failures'], unit)} "
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


#: ch20's hard case: the table's heading and its rows, in order. ``{problem}`` is the problem's
#: number, derived from the outline so that inserting a chapter cannot leave it stale.
FIXTURE_HEADING = "The model file under problem {problem}"
FIXTURE_ROWS = (
    "Kind of model, by [ch01](#point-estimates)'s test",
    "Monthly cost, point estimate",
    "Monthly cost, 90% interval",
    "Average of twelve invoices, invented for the exercise",
    "The model's futures at or above that average",
)
FIXTURE_RANGE = "{low} to {high}"


def fixture_against_invoice(name: str) -> str:
    """ch20's hard case: a model file missing one cost line, beside the figure it cannot reach.

    The rows are the ones the argument needs and no others: what kind of model it is by ch01's
    test, what it says, and how much of what it says reaches the invoice. The invoice is
    invented for the problem, and the row says so where a reader sees it.
    """
    from bench.outline import label_of

    summary = load_result(name)["summary"]
    unit = "USD/month"
    problem = f"{int(label_of('the_missing_node').removeprefix('ch'))}.3"
    values = (
        summary["classification"],
        fmt(summary["point"], unit),
        FIXTURE_RANGE.format(low=fmt(summary["p5"], unit), high=fmt(summary["p95"], unit)),
        fmt(summary["invoice_average"], unit),
        f"{summary['share_at_or_above_invoice']:.0%}",
    )
    rows = [f"| {FIXTURE_HEADING.format(problem=problem)} | |", "|---|---:|"]
    rows += [f"| {label} | {value} |" for label, value in zip(FIXTURE_ROWS, values, strict=True)]
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
        node_name
        for node_name, node in payload["nodes"].items()
        if node.get("blocked_by") and node_name not in missing
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
        f"{len(blocked)} node(s) downstream of those cannot be computed. In the book's tables "
        "they are shown as *not yet measured*; on the interactive model page their boxes show —. "
        "Nothing is estimated in their place: this book publishes measurements or it publishes "
        "nothing.",
        ":::",
    ]
    return "\n".join(lines)


# -- ch14's two experiments ---------------------------------------------------------------


#: The convergence table's headings; ``{runs}`` is the number of runs at each sample count.
CONVERGENCE_HEADINGS = (
    "Samples",
    "90% interval half-width",
    "Run-to-run spread of p95, {runs} runs each",
    "Fall in spread from the row above",
)


def convergence_table(name: str) -> str:
    """Two columns that behave differently, which is the whole of the figure.

    The interval settles. The run-to-run spread falls. A reader who has only ever been told
    "use ten thousand samples" has generally conflated the two, and conflating them is what makes
    "how many samples is enough" feel like a matter of taste rather than a calculation.

    The run count is read from the result, because ch14's problem 14.1 and Appendix B both send
    the reader to this heading for it.
    """
    summary = load_result(name)["summary"]
    points = summary["convergence"]
    runs = {point["replicates"] for point in points}
    if len(runs) != 1:
        raise ValueError(f"{name}: every sample count should have the same number of runs")
    (count,) = runs
    headings = [heading.format(runs=count) for heading in CONVERGENCE_HEADINGS]
    rows = [
        "| " + " | ".join(headings) + " |",
        "|---:|---:|---:|---:|",
    ]
    previous = None
    for point in points:
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


#: The correlation-effect table's two half-width columns.
CORRELATION_HEADINGS = (
    "90% interval half-width, correlations declared",
    "90% interval half-width, inputs independent",
)


def correlation_table(name: str) -> str:
    """What declaring that two inputs move together was worth, per output.

    Both columns are the half-width of the 90% interval, in the output's own unit, and are named
    as the convergence table names it: one quantity, one name, on every page that shows it.
    """
    rows_in = load_result(name)["summary"]["rows"]
    rows = [
        f"| Model | Output | {CORRELATION_HEADINGS[0]} | {CORRELATION_HEADINGS[1]} | Difference |",
        "|---|---|---:|---:|---:|",
    ]
    for row in rows_in:
        unit = row.get("unit", "dimensionless")
        rows.append(
            f"| `{row['model']}` | {row['output']} | {_value_with_unit(row['declared'], unit)} "
            f"| {_value_with_unit(row['independent'], unit)} | {row['change']:+.1%} |"
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


#: The ratio table's first and last column headings.
RATIO_HEADINGS = ("Output", "Ratio")


def scenario_ratios(name: str, other: str, *only: str) -> str:
    """Two scenarios of one model, on rows somebody chose, with the second divided by the first.

    ``scenario_comparison`` prints every declared output, which is right for a page comparing two
    whole designs and wrong for a page making one argument about them. This prints the rows the
    page argues from, in the order it argues, and may name any node the two results carry, not
    only a declared output: ch07's argument is about throughput and efficiency, which the model
    computes and does not publish.

    The last column is the second scenario's point value divided by the first's. It is there so
    the page can say "read the ratio" instead of spelling a figure as a word, which is how a claim
    goes stale without a check noticing. Point values only: a ratio of two ranges is not a range.
    """
    left, right = load_result(name)["summary"], load_result(other)["summary"]
    unknown = [n for n in only if n not in left["nodes"] or n not in right["nodes"]]
    if not only or unknown:
        raise KeyError(f"{name} / {other}: name the rows to show; unknown: {unknown}")
    rows = [
        f"| {RATIO_HEADINGS[0]} | {left['scenario']['title']} | {right['scenario']['title']} "
        f"| {RATIO_HEADINGS[1]} |",
        "|---|---:|---:|---:|",
    ]
    for node_name in only:
        ours, theirs = left["nodes"][node_name], right["nodes"][node_name]
        unit = ours["unit"]
        label = _with_unit(ours.get("label") or node_name, unit)
        if ours.get("blocked_by") or theirs.get("blocked_by"):
            rows.append(f"| {label} | *not yet measured* | *not yet measured* | — |")
            continue
        a, b = ours.get("point"), theirs.get("point")
        ratio = f"{b / a:.2f}" if a else "—"
        rows.append(f"| {label} | {fmt(a, unit)} | {fmt(b, unit)} | {ratio} |")
    return "\n".join(rows)


#: The breach table's first column heading.
BREACH_HEADING = "Futures over the limit"


def breach_comparison(name: str, other: str, *only: str) -> str:
    """How often each named ceiling is over its limit, in two scenarios of one model.

    ``scenario_comparison`` ends with these rows for every ceiling. A page that argues from a few
    of them names them here: one scenario's rate is a position, and beside the other's it is a
    change. A named node that is not a ceiling in both results raises, so a renamed ceiling fails
    the build rather than dropping a row the prose points at.
    """
    left, right = load_result(name)["summary"], load_result(other)["summary"]

    def ceiling(payload: dict, node_name: str) -> dict | None:
        return (payload["nodes"].get(node_name) or {}).get("ceiling")

    unknown = [n for n in only if not ceiling(left, n) or not ceiling(right, n)]
    if not only or unknown:
        raise KeyError(f"{name} / {other}: name the ceilings to show; not in both: {unknown}")
    rows = [
        f"| {BREACH_HEADING} | {left['scenario']['title']} | {right['scenario']['title']} |",
        "|---|---:|---:|",
    ]
    for node_name in only:
        rows.append(
            f"| {left['nodes'][node_name]['label']} "
            f"| {ceiling(left, node_name)['p_over_limit']:.0%} "
            f"| {ceiling(right, node_name)['p_over_limit']:.0%} |"
        )
    return "\n".join(rows)


#: The rows a decision between two designs needs, and no others (ch21): what is bought, what
#: it costs and when it is paid, the total three ways, and how often the busy hour breaks it.
#: Each is (node, what to read from it, its label). "point" is the value with every input at its
#: point estimate; "cell" is that value with the 90% interval under it; a percentile key reads
#: the node's summary; "over" is how often the ceiling on that node crosses its limit, and its
#: row takes the ceiling's own label, as the full comparison labels it.
DECISION_ROWS = (
    ("hosts", "point", "hosts in the fleet"),
    ("capex", "cell", "capex, paid once"),
    ("annual_opex", "cell", "annual opex, paid in each year"),
    ("tco", "point", "five-year total, at the point estimate"),
    ("tco", "p50", "five-year total, median"),
    ("tco", "p95", "five-year total, 95th percentile"),
    ("queueing_headroom", "over", None),
)
DECISION_OVER = "*{label}* — over its limit"


def scenario_decision(name: str, other: str) -> str:
    """Two designs, with only the rows a decision between them needs (ch21).

    :func:`scenario_comparison` prints every output and every ceiling. That is the right table for
    the appendix that documents the model and the wrong one to hand to the person who signs, and
    two of its rows are one figure under two names. This one says what each design buys, what it
    costs, and how often the busy hour is more than it can serve. A named node the model does not
    have raises, so a rename fails the build rather than dropping a row.
    """
    runs = [load_result(one)["summary"] for one in (name, other)]
    rows = [
        f"| | {runs[0]['scenario']['title']} | {runs[1]['scenario']['title']} |",
        "|---|---:|---:|",
    ]
    for node_name, read, label in DECISION_ROWS:
        cells = []
        for run in runs:
            node = run["nodes"][node_name]
            if node.get("blocked_by"):
                cells.append("*not yet measured*")
            elif read == "cell":
                cells.append(_cell(node))
            elif read == "point":
                cells.append(fmt(node.get("point"), node["unit"]))
            elif read == "over":
                cells.append(f"{node['ceiling']['p_over_limit']:.0%}")
            else:
                cells.append(fmt(node["summary"][read], node["unit"]))
        shown = label or DECISION_OVER.format(label=runs[0]["nodes"][node_name]["label"])
        rows.append(f"| {shown} | {' | '.join(cells)} |")
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


#: How the binding table writes a share of the model's futures, and its row for the gap that
#: one future in twenty exceeds.
BINDING_SHARE = "{:.0%} of futures"
BINDING_P95_GAP = "Gap exceeded in one future in twenty"


def binding_table(name: str) -> str:
    """Which of three chains decides the answer, and how often.

    The last row is the one to read against the three above it. Each chain's median is a
    perfectly good number; the answer is the largest of the three in every future, and the
    largest of three uncertain numbers sits well above where any one of them usually does.
    """
    s = load_result(name)["summary"]
    share = BINDING_SHARE
    return "\n".join(
        [
            "| | |",
            "|---|---:|",
            f"| The request rate decides the host count | {share.format(s['requests_binds'])} |",
            f"| The working set decides it | {share.format(s['memory_binds'])} |",
            f"| The data on disk decides it | {share.format(s['storage_binds'])} |",
            f"| Two chains ask for the same count | {share.format(s['tied'])} |",
            f"| Sized on the request chain alone, too small "
            f"| {share.format(s['short_if_requests'])} |",
            f"| Sized on the memory chain alone, too small | {share.format(s['short_if_memory'])} |",
            f"| Sized on the disk chain alone, too small | {share.format(s['short_if_storage'])} |",
            f"| Median gap between the winner and the runner-up | {s['median_gap']:,.0f} hosts |",
            f"| {BINDING_P95_GAP} | {s['p95_gap']:,.0f} hosts |",
            f"| Median of the request chain alone | {s['median_requests_hosts']:,.0f} hosts |",
            f"| Median of the memory chain alone | {s['median_memory_hosts']:,.0f} hosts |",
            f"| Median of the disk chain alone | {s['median_storage_hosts']:,.0f} hosts |",
            f"| Median of the largest of the three | {s['median_largest']:,.0f} hosts |",
        ]
    )


#: How the binding-constraint sweep names each chain, and how the page names it.
CHAIN_WORDS = {"requests": "request", "memory": "memory", "storage": "disk"}
#: The shortfall table's two row labels; ``{chain}`` is the page's name for the usual winner.
SHORTFALL_MEDIAN = "Median shortfall across all futures, sized on the {chain} chain alone"
SHORTFALL_MEAN = "Average shortfall across all futures, sized on the {chain} chain alone"


def binding_shortfall_table(name: str) -> str:
    """How far short a fleet sized on the usual winner falls, counted over every future.

    The median of that is small, because every future the chosen chain won adds a zero. The
    average is not, because a few futures where a neglected chain wins by a lot pull it up. The
    page shows both so that "the shortfall looks small" names the summary that makes it look
    small. The median over the short futures alone is problem 10.2's answer, and it is not here.

    The usual winner is read from the sweep rather than named here, as problem 10.2 reads it.
    """
    s = load_result(name)["summary"]
    winner = max(CHAIN_WORDS, key=lambda chain: s[f"{chain}_binds"])
    chain = CHAIN_WORDS[winner]
    return "\n".join(
        [
            "| | |",
            "|---|---:|",
            f"| {SHORTFALL_MEDIAN.format(chain=chain)} "
            f"| {s[f'shortfall_median_all_if_{winner}']:,.0f} hosts |",
            f"| {SHORTFALL_MEAN.format(chain=chain)} "
            f"| {s[f'shortfall_mean_all_if_{winner}']:,.0f} hosts |",
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
    groups: dict[str, list[str]] = {"outside": [], "you": [], "definition": []}
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
        "| **Outside your control** | | | |",
        *(groups["outside"] or empty),
        "| **What you decide** | | | |",
        *(groups["you"] or empty),
    ]
    # A year is a year whoever asks. Nobody decides it, and it is not the world's doing either.
    if groups["definition"]:
        rows += ["| **True by definition** | | | |", *groups["definition"]]
    # The key sits under the table rather than in a paragraph after it: a reader who meets the
    # symbols should not have to scroll past the table to learn what they mean.
    key = " · ".join(f"{PROVENANCE_MARK[kind]} {words}" for kind, words in CLAIM_KEY.items())
    return "\n".join(rows) + f"\n\n**Claim:** {key}"


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


#: The seam tables' headings, and the words after each end's label: which side computed the
#: price and which assumed it.
SEAM_HEADINGS = ("Unit", "Median", "90% interval")
SEAM_GROWTH_HEADINGS = ("Unit", "Slow growth", "Fast growth")
SEAM_SIDES = ("Web service model", "Observability model")
SEAM_COMPUTED = "computed"
SEAM_ASSUMED = "assumed"


def seam_table(name: str, other: str) -> str:
    """The two ends of a seam, and nothing else: one price computed, one assumed, and what it buys.

    ``name`` is the downstream result (the observability model), ``other`` the upstream one (the
    web service). The median, not the point estimate, because the median is what crosses a seam
    in practice and what the figure below it marks. The unit is the second column so that it is
    the last one a narrow screen hides rather than the first.
    """
    down, up = load_result(name)["summary"]["nodes"], load_result(other)["summary"]["nodes"]
    rows = ["| | " + " | ".join(SEAM_HEADINGS) + " |", "|---|---|---:|---:|"]

    def line(nodes: dict, key: str, how: str = "") -> str:
        node = nodes[key]
        summary, unit = node["summary"], node["unit"]
        label = f"{node['label']}, {how}" if how else node["label"]
        return (
            f"| {label} | {unit_label(unit)} | {fmt(summary['p50'], unit)} "
            f"| {fmt(summary['p5'], unit)} to {fmt(summary['p95'], unit)} |"
        )

    rows += [
        f"| **{SEAM_SIDES[0]}** | | | |",
        line(up, "cost_per_stored_tb_month", SEAM_COMPUTED),
        f"| **{SEAM_SIDES[1]}** | | | |",
        line(down, "storage_price", SEAM_ASSUMED),
        line(down, "known_stored"),
        line(down, "known_storage_cost"),
    ]
    return "\n".join(rows)


def seam_growth_table(name: str, other: str) -> str:
    """What one input, growth, does to each side of a seam when it is swung on its own.

    Read from each result's own swing of its growth factor between its p10 and its p90, every
    other input held at its point estimate: the same numbers ch19's tornado draws, one row of
    each. ``name`` is the downstream result, ``other`` the upstream one. If growth ever stops
    feeding either output, this raises: the page's claim would then be false.
    """
    rows = ["| | " + " | ".join(SEAM_GROWTH_HEADINGS) + " |", "|---|---|---:|---:|"]
    for result, heading, output in (
        (other, SEAM_SIDES[0], "cost_per_stored_tb_month"),
        (name, SEAM_SIDES[1], "known_stored"),
    ):
        payload = load_result(result)["summary"]
        bar = next(b for b in payload["tornado"][output] if b["node"] == "annual_growth")
        node = payload["nodes"][output]
        rows += [
            f"| **{heading}**: {bar['label']} | | {fmt(bar['low_input'])} "
            f"| {fmt(bar['high_input'])} |",
            f"| {node['label']} | {unit_label(node['unit'])} | {fmt(bar['low'], node['unit'])} "
            f"| {fmt(bar['high'], node['unit'])} |",
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


#: The shapes table's two headings.
SHAPE_HEADINGS = ("Shape", "Keys under it")


def distribution_keys(_name: str = "") -> str:
    """Each shape a model file may declare, and the keys it writes under it.

    Read from the percentile functions themselves: `sizing.mc.sample` passes a distribution's
    keys to its function by name, so a function's parameters are exactly what a file may write.
    """
    rows = ["| " + " | ".join(SHAPE_HEADINGS) + " |", "|---|---|"]
    for shape, percentile in mc.SHAPES.items():
        keys = [name for name in inspect.signature(percentile).parameters if name != "u"]
        rows.append(f"| `{shape}` | " + ", ".join(f"`{key}`" for key in keys) + " |")
    return "\n".join(rows)


#: A conversion factor in words, as the build applies it. ``{factor}`` is already a printed number.
FACTOR_TIMES = "multiplies by {factor}"
FACTOR_OVER = "divides by {factor}"


def _factor_words(factor: float) -> str:
    """A conversion factor as the build applies it, in words a reader can check by hand.

    ``divides by 12`` rather than ``multiplies by 0.0833333``, and never ``1e-06``: a factor that
    is a whole number, or one over a whole number, is printed as that whole number.
    """
    if factor >= 1 and abs(factor - round(factor)) < 1e-9 * factor:
        return FACTOR_TIMES.format(factor=f"{round(factor):,}")
    inverse = 1 / factor
    if factor < 1 and abs(inverse - round(inverse)) < 1e-6 * inverse:
        return FACTOR_OVER.format(factor=f"{round(inverse):,}")
    return FACTOR_TIMES.format(factor=f"{factor:.6g}")


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
        "the seconds cancel, and the link was quoted in bits: eight to a byte",
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
            shown += f", and the build {_factor_words(factor)}"
        rows.append(f"| {what} | {_spelled(units, operation)} | {shown} | {why} |")
    return "\n".join(rows)


#: What a node declares against what its formula makes, and what the build does: accept, convert,
#: or refuse for one of two reasons. Each row is run through the build's own unit check.
#: (the case, {input: unit}, the formula, the unit the node declares)
UNIT_VERDICTS: tuple[tuple[str, dict[str, str], str, str], ...] = (
    (
        "a request rate, for a duration",
        {"rate": "request/second", "window": "second"},
        "rate * window",
        "request",
    ),
    (
        "a request rate, times a plain number",
        {"rate": "request/second", "copies": "dimensionless"},
        "rate * copies",
        "request",
    ),
    ("a price per terabyte-year", {"price": "USD/TB/year"}, "price", "USD/TB/month"),
    (
        "watts, times the hours in a year",
        {"power": "W", "hours": "hour/year"},
        "power * hours",
        "kWh/year",
    ),
    ("a drive as the sheet quotes it", {"drive": "TB"}, "drive", "TiB"),
    (
        "a link rate, for a duration",
        {"link": "Mbit/second", "window": "second"},
        "link * window",
        "MB",
    ),
    (
        "bytes per span, times spans per request",
        {"size": "byte/span", "spans": "span/request"},
        "size * spans",
        "byte/request",
    ),
    (
        "bytes per span, times spans per request",
        {"size": "byte/span", "spans": "span/request"},
        "size * spans",
        "byte/second",
    ),
    (
        "raw data, plus a spare drive quoted in binary",
        {"raw": "TB", "spare": "TiB"},
        "raw + spare",
        "TB",
    ),
    (
        "a working set over memory per host, rounded up to whole hosts",
        {"working_set": "TB", "memory": "GiB/host"},
        "ceil(working_set / memory)",
        "host",
    ),
)

#: The verdicts table's headings, and the words its cells are built from.
VERDICT_HEADINGS = ("Case", "Formula", "Node declares", "Verdict")
FORMULA_UNIT = "`{name}` in `{unit}`"
REFUSED_KIND = (
    "the formula makes {produced} and the node declares {declared}, "
    "and no factor turns one into the other"
)
REFUSED_SUM = (
    "two units of one kind meet in a sum, "
    "and the build converts a formula's result once, not each number inside it"
)
REFUSED_ROUNDS = "the formula rounds before the build converts, so it rounds the wrong number"


def _spelled_formula(formula: str, inputs: dict[str, str]) -> str:
    """A row's formula and the unit of each name in it: `raw + spare`, `raw` in `TB`, ..."""
    units = ", ".join(FORMULA_UNIT.format(name=name, unit=unit) for name, unit in inputs.items())
    return units if formula in inputs else f"`{formula}`, {units}"


def unit_check_table(_name: str = "") -> str:
    """What the unit check does with each hand-picked formula, reached by the check itself.

    Each row becomes a model of one derived node over its inputs and goes through
    :func:`sizing.evaluate.check_units`, so the table cannot show a verdict the build would not
    reach. A refusal says which of the two reasons applies, in the words the build's own message
    uses for the kinds of quantity.
    """
    from sizing.dsl import Model, _node_from
    from sizing.evaluate import (
        UNIT_FUNCTIONS,
        _mixed_operands,
        _rounds_in_the_wrong_unit,
        _units_of,
        _walk,
        check_units,
        plausible_magnitudes,
    )
    from sizing.units import UNITS, compatible, described

    rows = ["| " + " | ".join(VERDICT_HEADINGS) + " |", "|---|---|---|---|"]
    for what, inputs, formula, declared in UNIT_VERDICTS:
        spec = {
            name: {
                "kind": "input",
                "unit": unit,
                "value": 2.0,
                "provenance": {"kind": "assumption", "source": "a row of this table"},
            }
            for name, unit in inputs.items()
        }
        spec["result"] = {"kind": "derived", "unit": declared, "formula": formula}
        nodes = {name: _node_from(name, node, "appendix D") for name, node in spec.items()}
        model = Model(name="row", title=what, currency="USD", nodes=nodes, outputs=("result",))
        problems, factors = check_units(model)
        magnitudes = plausible_magnitudes(model)
        quantities = {
            name: UNITS.Quantity(magnitudes[name], parse_unit(node.unit))
            for name, node in nodes.items()
        }
        tree = nodes["result"].formula
        produced = str(_units_of(_walk(tree, quantities, UNIT_FUNCTIONS)))
        if not compatible(produced, declared):
            verdict = "**refused**: " + REFUSED_KIND.format(
                produced=described(produced), declared=described(declared)
            )
        elif _mixed_operands(tree, quantities, formula, declared):
            verdict = "**refused**: " + REFUSED_SUM
        elif _rounds_in_the_wrong_unit(tree, quantities, formula, declared):
            verdict = "**refused**: " + REFUSED_ROUNDS
        elif problems:
            raise AssertionError(f"{what}: a refusal this table has no words for: {problems}")
        elif abs(factors["result"] - 1.0) < 1e-12:
            verdict = "accepted as written"
        else:
            verdict = f"converted: the build {_factor_words(factors['result'])}"
        rows.append(f"| {what} | {_spelled_formula(formula, inputs)} | `{declared}` | {verdict} |")
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
        "| Model | Node | Formula produces | Node declares | The build |",
        "|---|---|---|---|---|",
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
                f"| `{model.name}` | {node.display} | `{produced}` | `{node.unit}` "
                f"| {_factor_words(factor)} |"
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
        return format(_units_of(_walk(tree, quantities, UNIT_FUNCTIONS)), "C")
    except Exception:  # pragma: no cover - a model that does not typecheck is skipped above
        return "?"


#: Every word the book uses in a technical sense: term -> (the chapter that introduces it,
#: what it means here, and the plain-English phrase it replaces). Six of them are the
#: rationed statistics words, and tests/test_vocabulary.py reads their chapters from here.
#: The glossary table is rendered from this in alphabetical order, and the site links a
#: term's first prose mention on any page after that chapter to its entry, with the
#: meaning as the link's title. So a meaning uses none of the six before the six's own
#: chapter: tests/test_vocabulary.py holds it to that.
GLOSSARY: dict[str, tuple[str, str, str]] = {
    "binding constraint": (
        "bandwidth_and_the_binding_constraint",
        "the chain that decides the answer, out of several that could",
        "whichever runs out first",
    ),
    "busy hour": (
        "peak_mean_and_growth",
        "the stretch of heaviest demand that sizes the fleet; you decide how long that stretch "
        "is, from how long your system takes to fail and how long your users will wait for it "
        "to recover",
        "peak demand time",
    ),
    "ceiling": (
        "point_estimates",
        "a limit past which a chain of multiplications stops describing anything",
        "where it breaks",
    ),
    "conditional model": (
        "point_estimates",
        "a model with a measured constant or a ceiling in it, which must keep headroom below each "
        "ceiling",
        "every input can be right and the answer still wrong",
    ),
    "convergence": (
        "correlation_and_convergence",
        "the answer ceasing to move between runs",
        "it has settled",
    ),
    "correlation": (
        "correlation_and_convergence",
        "the tendency of two inputs to move together",
        "they move together",
    ),
    "definitional model": (
        "point_estimates",
        "a model built only from relationships true by definition—accounting identities and "
        "physics—and working its arithmetic across its inputs' ranges shows all the doubt in the "
        "terms it has",
        "if its structure is right, only wrong through inputs",
    ),
    "distribution": (
        "monte_carlo",
        "the bag of values an uncertain quantity could take",
        "a range of plausible values",
    ),
    "duration": (
        "what_a_workload_is",
        "a length of time — a horizon, a retention period, the time one request spends in the system",
        "how long",
    ),
    "failure domain": (
        "headroom_and_failure_domains",
        "the set of hosts one fault takes out together; one host is the smallest failure domain; "
        "a larger failure domain is worse because more hosts go at once",
        "hosts failing together",
    ),
    "flow": (
        "what_a_workload_is",
        "a rate — requests per second, bytes per second, dollars per year",
        "something that arrives",
    ),
    "futures": (
        "peak_mean_and_growth",
        "the possible outcomes a model works out, each one a run of the arithmetic with every "
        "uncertain input set to one value picked at random; the book reports the share of them "
        "where something happens",
        "all possible outcomes",
    ),
    "headroom": (
        "point_estimates",
        "the margin a design keeps below a ceiling, and the reason for it",
        "the slack you keep",
    ),
    "interval": ("monte_carlo", "the gap between two percentiles", "how wide the answer is"),
    "knee": (
        "queueing_and_the_knee",
        "where people say response time starts climbing steeply as a system gets busier; the "
        "curve is smooth and has no such point, so what people call the knee is where the climb "
        "passed what they would accept; this book declares a margin with a reason instead",
        "where the wait passed what people would accept",
    ),
    "measured constant": (
        "point_estimates",
        "an empirical number belonging to one implementation at one version",
        "a number somebody measured",
    ),
    "median": (
        "bandwidth_and_the_binding_constraint",
        "the middle answer: put every outcome in order and take the one in the middle; half the "
        "outcomes come in above it",
        "the middle answer",
    ),
    "percentile": (
        "monte_carlo",
        "the value that a given share of a distribution's values fall below",
        "where a share falls below",
    ),
    "point estimate": (
        "point_estimates",
        "the number you get from running the arithmetic once, with one value for every input, "
        "usually the middle of its range",
        "what a spreadsheet gives",
    ),
    "provenance": (
        "what_a_workload_is",
        "the record every input in a model file carries of where its number came from and what "
        "kind of source it is, whether a fact, vendor claim or assumption",
        "where it came from",
    ),
    "regime change": (
        "regime_changes",
        "a point at which a system stops obeying one rule and starts obeying another; a chain of "
        "multiplications cannot express one",
        "the system changed",
    ),
    "residence time": (
        "littles_law",
        "the time a request spends in the system from arriving to leaving, including any time "
        "waiting in a queue",
        "time in queue and service",
    ),
    "sample": ("monte_carlo", "one value drawn at random from a distribution", "one guess"),
    "service demand": (
        "littles_law",
        "the processor time one request costs, in core-seconds; not how long the request takes",
        "CPU time per request",
    ),
    "service time": (
        "littles_law",
        "how long one request takes when it waits for nothing",
        "time per request",
    ),
    "sizing chain": (
        "what_a_workload_is",
        "the string of multiplications that runs from a workload to a number of machines",
        "how you calculate hosts needed",
    ),
    "standard error": (
        "where_the_numbers_come_from",
        "how far a measured average would typically move if you repeated the whole measurement; "
        "how uncertain a measured constant is in the model; it shrinks slowly as you measure more",
        "how much to trust it",
    ),
    "stock": (
        "what_a_workload_is",
        "a level — terabytes held, series alive, requests in flight",
        "how much there is right now",
    ),
    "structural error": (
        "monte_carlo",
        "a model that is wrong in shape rather than in its numbers",
        "something is missing",
    ),
    "tornado": (
        "peak_mean_and_growth",
        "a chart showing which input moves an answer most; each uncertain input swings from a low "
        "to a high end of its range whilst every other input stays at its central value; the bars "
        "are sorted longest first, into a funnel",
        "chart of what matters most",
    ),
    "transfer factor": (
        "the_sellers_tco",
        "the share of a benchmark's advantage that carries over to the customer's own workload",
        "how much of the benchmark applies to you",
    ),
    "unit economics": (
        "unit_economics",
        "a cost divided by a denominator you can defend",
        "cost per something",
    ),
    "utilisation": (
        "littles_law",
        "the fraction of a system that is busy",
        "how busy it is",
    ),
}


def glossary_table(_name: str = "") -> str:
    """Every word the book uses in a technical sense, and the chapter that introduces it.

    Generated from ``bench/outline.py`` rather than written out, so a term whose chapter moves
    cannot end up pointing at the wrong one. Sorted alphabetically, because a reader comes here
    to look one word up; the chapter column gives the book's order.
    """
    from bench.outline import BY_SLUG

    rows = ["| Term | Introduced in | What it means here | Said plainly |", "|---|---|---|---|"]
    for term, (slug, meaning, plain) in sorted(GLOSSARY.items()):
        chapter = BY_SLUG[slug]
        rows.append(f"| **{term}** | [{chapter.label}](#{chapter.anchor}) | {meaning} | {plain} |")
    return "\n".join(rows)


#: The targets table's two headings.
TARGETS_HEADINGS = ("Target", "What it means")


def targets_table(_name: str = "") -> str:
    """The four targets a stamped result can declare, and what each one means.

    Rendered from ``bench.stamp.TARGET_MEANING``, the source of truth, so the glossary cannot
    say something the stamp no longer does. A table rather than the dict quoted as code: on a
    phone a code block runs off the edge, and this is the only place the four are defined in one
    list.
    """
    from bench.stamp import TARGET_MEANING

    rows = [f"| {TARGETS_HEADINGS[0]} | {TARGETS_HEADINGS[1]} |", "|---|---|"]
    rows += [f"| `{target}` | {meaning} |" for target, meaning in TARGET_MEANING.items()]
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
        # A ceiling is named as the graph names its box. It borrows the label of the quantity it
        # watches, so without the prefix two rows read the same and a box in the graph has no row.
        shown = f"limit on {node.display}" if isinstance(node, Ceiling) else node.display
        row = f"| {shown} (`{name}`) | {formula} | {unit_label(node.unit)} |"
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


#: The totals table's headings, and its two rows.
TOTALS_HEADINGS = ("Five-year total", "At the point estimate", "Middle nine in ten")
TOTALS_ROWS = (("incumbent", "Incumbent"), ("challenger", "Challenger"))


def comparison_totals(name: str) -> str:
    """The two five-year totals, each on its own: the point and the middle nine in ten.

    The two intervals nearly coincide, which is what the paired difference below them is set
    against: two totals this wide, and a difference a fraction of either (ch22).
    """
    designs = load_result(name)["summary"]["designs"]
    rows = ["| " + " | ".join(TOTALS_HEADINGS) + " |", "|---|---:|---:|"]
    for key, label in TOTALS_ROWS:
        total = designs[key]["tco"]
        rows.append(
            f"| {label} | {_money(total['point'])} "
            f"| {_money(total['p5'])} to {_money(total['p95'])} |"
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


#: What the break-even table says of a line the challenger's side carries that is not the
#: vendor's, and of a shared input's tie against the values the model drew for it.
ASSUMED_WHOSE = "an assumption, on the challenger's side"
ASSUMED_VERDICT = "{change} on the assumption"
TIE_IN_DRAWS = "outside the middle eighty per cent, inside the values the model draws"
TIE_BELOW_DRAWS = "below every value the model draws"
TIE_ABOVE_DRAWS = "above every value the model draws"


def comparison_break_even(name: str) -> str:
    """Where the two totals tie, input by input, and whether that value is one to worry about."""
    summary = load_result(name)["summary"]
    rows_in = summary["break_even"]
    # Whose each line is comes from the challenger's quote, where the mark is: two of the lines a
    # break-even moves on the challenger's side are not the vendor's (the move, the host count).
    kinds = {row["input"]: row["provenance"] for row in summary["designs"]["challenger"]["quote"]}
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
            elif row["whose"] == "challenger" and kinds.get(row["input"]) == "assumption":
                verdict = ASSUMED_VERDICT.format(change=f"{row['from_quote']:+.1%}")
            elif row["whose"] == "challenger":
                verdict = f"{row['from_quote']:+.1%} on the quote"
            elif row["in_swing"]:
                verdict = "inside the middle eighty per cent of what it could be"
            elif row.get("in_draws"):
                verdict = TIE_IN_DRAWS
            elif row.get("drawn_low") is not None and row["ties_at"] < row["drawn_low"]:
                verdict = TIE_BELOW_DRAWS
            elif row.get("drawn_high") is not None and row["ties_at"] > row["drawn_high"]:
                verdict = TIE_ABOVE_DRAWS
            elif row["in_range"]:
                verdict = "outside the middle eighty per cent, inside the range the model admits"
            else:
                verdict = "outside the range the model admits"
        if row["input"] == "staff_fte":
            whose = "a claim about your people"
        elif row["whose"] == "challenger" and kinds.get(row["input"]) == "assumption":
            whose = ASSUMED_WHOSE
        elif row["whose"] == "challenger":
            whose = "the challenger's quote"
        else:
            whose = "shared by both"
        rows.append(f"| {row['label']} | {whose} | {at} | {tie} | {verdict} |")
    return "\n".join(rows)


# -- two generations in one pool (ch10, ch11, ch22) ---------------------------------------------


def mixed_pool_chains(name: str) -> str:
    """New hosts each chain asks for, three ways: all new, and the mixed pool routed two ways.

    The point of the table is the row that changes hands. An all-new fleet is bound by one chain;
    old hosts that are rich in one resource move the binding to another, and routing requests
    equally moves the answer again, because the smallest host sets the pace (ch10).
    """
    rows = [
        "| Chain | All new hosts | Old hosts kept, routed by capacity "
        "| Old hosts kept, routed equally |",
        "|---|---:|---:|---:|",
    ]
    chains = load_result(name)["summary"]["chains"]
    for i, row in enumerate(chains):
        label = f"**{row['label']}**" if i == len(chains) - 1 else row["label"]
        rows.append(
            f"| {label} | {fmt(row['all_new'], 'host')} | {fmt(row['by_capacity'], 'host')} "
            f"| {fmt(row['equally'], 'host')} |"
        )
    return "\n".join(rows)


def mixed_pool_ceilings(name: str) -> str:
    """Each ceiling of the pool as bought, kept and retired, beside an all-new fleet.

    Each cell is two readings: the share of futures past the allowed line, and what the plan
    itself says at the point estimates. The pool bought for capacity-weighted routing is checked
    as planned, after the old hosts have gone and before demand stops growing (ch11), and against
    the fleet that replaced them outright (ch22).
    """
    rows = [
        "| Ceiling | Over allowed, old hosts kept | Over allowed, old hosts retired "
        "| Over allowed, all new hosts |",
        "|---|---:|---:|---:|",
    ]
    for row in load_result(name)["summary"]["ceilings"]:
        # The book's own verdict words, never the evaluator's: "inside headroom" reads as
        # reassurance, and here it sits on a pool a hair under its limit.
        cells = [
            f"{row[column]:.0%}; plan: {VERDICT_MARK[row['verdict_' + column]]}"
            for column in ("kept", "retired", "all_new")
        ]
        rows.append(f"| {row['label']} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def _share_of_futures(share: float) -> str:
    """A share of futures, never rounded to all or none: 99.997% is not a certainty."""
    if 0.0 < share < 0.005:
        return "less than 1%"
    if 0.995 <= share < 1.0:
        return "more than 99%"
    return f"{share:.0%}"


def mixed_pool_keep_vs_replace(name: str) -> str:
    """Keep the old hosts or replace them: each total, and the difference future by future.

    The two totals overlap; the difference, taken on shared futures, does not straddle zero.
    Subtracting the two intervals' ends instead would count the shared uncertainty twice (ch22).
    The last two rows are the same subtraction with requests routed equally, which is the
    condition the first verdict rests on.
    """
    k = load_result(name)["summary"]["keep_vs_replace"]
    e = k["routed_equally"]
    rows = [
        "| | At the point estimate | Middle nine in ten |",
        "|---|---:|---:|",
        f"| Keep the old hosts, buy {fmt(k['new_hosts']['keep'], 'host')} new "
        f"| {_money(k['keep']['point'])} | {_money(k['keep']['p5'])} to {_money(k['keep']['p95'])} |",
        f"| Replace them, buy {fmt(k['new_hosts']['replace'], 'host')} new "
        f"| {_money(k['replace']['point'])} "
        f"| {_money(k['replace']['p5'])} to {_money(k['replace']['p95'])} |",
        f"| Keep minus replace, future by future | {signed_money(k['difference']['point'])} "
        f"| {signed_money(k['difference']['p5'])} to {signed_money(k['difference']['p95'])} |",
        f"| Futures in which keeping is cheaper | | {_share_of_futures(k['share_keep_cheaper'])} |",
        f"| Keep minus replace, routed equally, buying {fmt(e['new_hosts'], 'host')} new "
        f"| {signed_money(e['point'])} | {signed_money(e['p5'])} to {signed_money(e['p95'])} |",
        f"| Futures in which keeping is cheaper, routed equally | "
        f"| {_share_of_futures(e['share_keep_cheaper'])} |",
    ]
    return "\n".join(rows)


def mixed_pool_keep_vs_replace_lines(name: str) -> str:
    """Which lines the keep-or-replace difference is made of, at the point estimate (ch22)."""
    rows = [
        "| Line | Keep the old hosts | Replace them | Keep minus replace |",
        "|---|---:|---:|---:|",
    ]
    for line in load_result(name)["summary"]["keep_vs_replace"]["lines"]:
        rows.append(
            f"| {line['label']} | {_money(line['keep'])} | {_money(line['replace'])} "
            f"| {signed_money(line['keep'] - line['replace'])} |"
        )
    return "\n".join(rows)


# -- ch23 The seller's TCO ------------------------------------------------------------------------


#: The ladder's rows, in the order the page reads them: from the brochure down to the bottom-up.
#: Chapter labels come from the outline, so a renumbering cannot leave a stale one in a table.
def _seller_ladder_labels() -> dict[str, str]:
    from bench.outline import label_of

    ch22 = label_of("comparing_two_tcos")
    return {
        "brochure": "The brochure",
        "bottom_up_assumptions": f"Top down, with {ch22}'s two assumptions",
        "sellers_guesses": "Top down, with the seller's guesses",
        "bottom_up": f"{ch22}'s bottom-up comparison",
    }


def _saving(value: float) -> str:
    """A saving: a loss is written as a negative saving, never as a positive cost."""
    return signed_money(value)


def seller_ladder(name: str) -> str:
    """One customer, four answers: what each version of the seller's TCO says it saves (ch23).

    Every row is ch22's incumbent. The two columns in the middle are the two assumptions a
    top-down TCO hides; the bottom row has neither, because it priced every line instead.
    """
    from bench.outline import label_of

    labels = _seller_ladder_labels()
    rows = [
        f"| Five-year saving for {label_of('comparing_two_tcos')}'s customer "
        "| Benchmark that carries over "
        "| Share of the spend that scales | Proposed hosts | At the point estimate "
        "| Middle nine in ten | Futures with a saving |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in load_result(name)["summary"]["ladder"]:
        transfer = "—" if row["transfer_factor"] is None else f"{row['transfer_factor']:.0%}"
        share = "—" if row["scaling_share"] is None else f"{row['scaling_share']:.0%}"
        spread = (
            f"{_saving(row['p5'])} to {_saving(row['p95'])}" if row.get("p5") is not None else "—"
        )
        futures = (
            _share_of_futures(row["share_positive"])
            if row.get("share_positive") is not None
            else "—"
        )
        hosts = row["proposed_hosts"]
        hosts_text = f"{hosts:,.0f}" if float(hosts).is_integer() else f"{hosts:,.1f}"
        rows.append(
            f"| {labels[row['key']]} | {transfer} | {share} | {hosts_text} "
            f"| {_saving(row['point'])} | {spread} | {futures} |"
        )
    return "\n".join(rows)


def _break_even_usage(value: float, margin: float) -> str:
    """Hosts at which the saving is zero, or the plain fact that none exists."""
    if margin <= 0:
        return "none: no size of customer pays for the move"
    return f"{value:,.1f} hosts"


def _break_even_transfer(value: float) -> str:
    if value < 0:
        return "none: no transfer pays for the move"
    return f"{value:.0%}"


def seller_scenarios(name: str) -> str:
    """The seller's model for a customer it has not met, as a brochure and as it should be (ch23).

    Point, spread and share of futures from the stamped scenario runs; the break-evens at the
    point, where the seller's own guesses sit.
    """
    summary = load_result(name)["summary"]["scenarios"]
    columns = (("brochure", "The brochure"), ("reference", "The seller's honest model"))
    runs = {key: load_result(f"sellers_tco-{key}")["summary"]["nodes"] for key, _ in columns}
    rows = [
        "| For a customer the seller has not met | " + " | ".join(t for _, t in columns) + " |",
        "|---|---:|---:|",
    ]

    def line(label: str, cell) -> str:
        return f"| {label} | " + " | ".join(cell(key) for key, _ in columns) + " |"

    rows += [
        line("Five-year saving, at the point estimate", lambda k: _saving(summary[k]["saving"])),
        line(
            "Middle nine in ten",
            lambda k: (
                f"{_saving(runs[k]['saving']['summary']['p5'])} to "
                f"{_saving(runs[k]['saving']['summary']['p95'])}"
            ),
        ),
        line("Futures with a saving", lambda k: _share_of_futures(summary[k]["saving_positive"])),
        line(
            "Saving per current host a year, before the move",
            lambda k: _saving(summary[k]["margin_per_host_year"]),
        ),
        line(
            "Benchmark that must carry over to break even",
            lambda k: _break_even_transfer(summary[k]["break_even_transfer"]),
        ),
        line(
            "Years until the move is paid back",
            lambda k: (
                "never" if summary[k]["payback"] <= 0 else f"{summary[k]['payback']:.1f} years"
            ),
        ),
        line(
            "Customer size at which the move pays for itself",
            lambda k: _break_even_usage(
                summary[k]["break_even_usage"], summary[k]["margin_per_host_year"]
            ),
        ),
    ]
    return "\n".join(rows)


# -- ch02 What a workload is: one horizon, three ways ---------------------------------------------


def horizon_three_ways(name: str) -> str:
    """The same horizon typed three ways, and how many times each applies the yearly factor (ch02).

    In years, divided by one year; in months, converted to years first; and as a bare number in a
    spreadsheet cell, where the unit is gone and a formula has to guess. The growth factor and the
    horizon are the model's point values; the months come from the unit registry.
    """
    from sizing.units import UNITS

    nodes = load_result(name)["summary"]["nodes"]
    growth, horizon = nodes["annual_growth"]["point"], nodes["horizon"]["point"]
    months = UNITS.Quantity(horizon, "year").to("month").magnitude
    years = f"{horizon:g} years"

    def grows(times: float) -> str:
        value = growth**times
        return f"×{value:,.1f}" if value < 100 else f"×{value:,.0f}"

    rows = [
        "| The horizon, typed as | Before counting | Times the yearly factor is applied "
        "| Demand grows |",
        "|---|---|---:|---:|",
        f"| {years} | divided by one year | {horizon:g} | {grows(horizon)} |",
        f"| {months:g} months | converted to {years}, then divided by one year | {horizon:g} "
        f"| {grows(horizon)} |",
        f"| a bare {months:g}, in a spreadsheet cell | nothing: the unit is gone "
        f"| {months:g}, if the formula assumes years | {grows(months)} |",
    ]
    return "\n".join(rows)
