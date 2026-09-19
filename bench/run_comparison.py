"""Two quotes for one workload, subtracted future by future.

    python3 -m bench.run_comparison            # run it and write the result
    python3 -m bench.run_comparison --check    # re-run and fail if a published figure moved

ch21 put two designs side by side. This runner asks the question that comparison leaves open:
**by how much is one cheaper than the other, and how often would that turn out to be wrong?**

## Subtract futures, not intervals

Each quote is a scenario of the running example with every line of the quote pinned exactly
(``incumbent.yaml`` and ``challenger.yaml``). Everything the quotes do not fix -- the growth, the
electricity price, what an engineer costs -- is drawn once and reaches both designs, because both
scenarios pin the same inputs and share a seed. So the difference between the two totals can be
taken sample by sample: the same future, both fleets, subtract.

That is not a detail. The two totals are wide and they overlap, and a reader shown two intervals
concludes that nothing can be said. Most of each interval is the same uncertainty on both sides,
and it cancels in the difference. Sampling the two designs on shared draws is the oldest trick
in Monte Carlo (Kahn and Marshall, 1953; Wright and Ramsay, 1979 on when it fails), and the
runner records what the interval would have been without it, so the page can show the gap.

## Every line on both sides

A comparison in which one side is missing a line is a comparison that side wins by omission. The
model carries a per-host licence line and a one-off cost of moving as declared zeros, so that a
quote with a different licence model or a quote that is not the incumbent has somewhere to put
its figure, and the two totals contain the same lines.

## What would flip it

The break-even table asks, for each line a quote could argue about: at what value would the two
totals tie at the point estimate? And, for the inputs both designs share: is there any value in
the range the model admits at which the ordering reverses? An input whose break-even lies outside
that range cannot flip the comparison, and an input that dominates every other tornado in this
book -- growth -- does not move the difference at all, because both fleets were bought before the
growth arrived.

## What it cannot see

Both quotes are held exactly, so nothing here is about what either vendor would actually charge
after negotiation. The move is the team's own estimate, marked as an assumption. And the whole
comparison lives inside one model: a line neither quote has is a line neither total has (ch20).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace

import numpy as np

from bench.stamp import build_result, load_result, numeric_differences, result_exists
from sizing import mc
from sizing.dsl import Input, Model, Scenario, load_model, load_scenario
from sizing.evaluate import evaluate, point, sampled_inputs, swing_of

SOURCES = ["bench/run_comparison.py"]

MODEL = "models/web_service/model.yaml"
INCUMBENT = "models/web_service/scenarios/incumbent.yaml"
CHALLENGER = "models/web_service/scenarios/challenger.yaml"

#: What the comparison is about.
TOTAL = "tco"

#: The lines a quote is made of, in the order a bill would list them. The last four are annual
#: and are multiplied out over the horizon so that every row of the table is money over the
#: same five years.
LINES = (
    ("Hosts", "host_capex", False),
    ("Network", "network_capex", False),
    ("The move", "migration_cost", False),
    ("Energy", "annual_energy_cost", True),
    ("Licences", "annual_licences", True),
    ("Support", "annual_support", True),
    ("People", "annual_staff_cost", True),
)

#: What a design is asked about, besides its price: how often it copes.
CEILINGS = (
    "queueing_headroom",
    "failure_headroom",
    "cache_fill",
    "disk_fill",
    "scaling_loss",
    "coordination_headroom",
)

#: The lines of the challenger's quote a buyer could argue about, and the inputs both designs
#: share that could flip the comparison if they turned out differently. ``whose`` says which.
BREAK_EVENS = (
    ("migration_cost", "challenger"),
    ("host_price", "challenger"),
    ("licence_per_host", "challenger"),
    ("hosts", "challenger"),
    ("staff_fte", "challenger"),
    ("electricity_price", "shared"),
    ("pue", "shared"),
    ("network_price_per_host", "shared"),
    ("annual_growth", "shared"),
)

#: A break-even that lands within this of the total is a tie; beyond it the secant was fooled.
TIE_TOLERANCE = 1e-6


def quote_of(model: Model, scenario: Scenario) -> list[dict]:
    """Every line a scenario pins, in the order the quote lists them, and what kind of claim each is."""
    rows = []
    for name in scenario.overrides:
        node = model.nodes[name]
        assert isinstance(node, Input)
        rows.append(
            {
                "input": name,
                "label": node.display,
                "unit": node.unit,
                "value": float(scenario.overrides[name]),
                "provenance": node.provenance.kind if node.provenance else "assumption",
            }
        )
    return rows


def design_summary(model: Model, scenario: Scenario, evaluation) -> dict:
    values = point(model, scenario)
    total = evaluation.summaries[TOTAL]
    return {
        "title": scenario.title,
        "hosts": values["hosts"],
        "tco": {
            "point": values[TOTAL],
            "p5": total["p5"],
            "p50": total["p50"],
            "p95": total["p95"],
        },
        "quote": quote_of(model, scenario),
        "ceilings": {
            name: {
                "label": model.nodes[name].display,
                "p_over_limit": evaluation.ceilings[name]["p_over_limit"],
                "p_over_allowed": evaluation.ceilings[name]["p_over_allowed"],
            }
            for name in CEILINGS
        },
    }


def lines_of(model: Model, incumbent: Scenario, challenger: Scenario) -> list[dict]:
    """Where the money moves, line by line, at the point estimate."""
    a, b = point(model, incumbent), point(model, challenger)
    horizon = a["horizon"]
    rows = []
    for label, node, annual in LINES:
        years = horizon if annual else 1.0
        rows.append(
            {
                "label": label,
                "node": node,
                "incumbent": a[node] * years,
                "challenger": b[node] * years,
                "difference": (b[node] - a[node]) * years,
            }
        )
    rows.append(
        {
            "label": "Five-year total",
            "node": TOTAL,
            "incumbent": a[TOTAL],
            "challenger": b[TOTAL],
            "difference": b[TOTAL] - a[TOTAL],
        }
    )
    return rows


def paired_difference(model: Model, incumbent: Scenario, challenger: Scenario) -> dict:
    """The difference between the two totals, taken over the same futures.

    The shared draws are asserted rather than assumed: every input both designs sample must have
    come out identical, or the subtraction is between two different worlds.
    """
    a, b = evaluate(model, incumbent), evaluate(model, challenger)
    if set(incumbent.overrides) != set(challenger.overrides):
        raise ValueError("the two quotes pin different inputs, so their futures are not shared")
    shared = [n for n in sampled_inputs(model) if n in a.samples and n in b.samples]
    for name in shared:
        if not np.array_equal(a.samples[name], b.samples[name]):
            raise ValueError(f"{name} was drawn differently for the two designs")
    difference = b.samples[TOTAL] - a.samples[TOTAL]

    # What a slide would print. Two intervals side by side invite the reader to subtract their
    # ends, and a difference of independent draws is the honest version of that mistake: each
    # design in its own future, the shared uncertainty counted twice.
    shuffled = np.random.default_rng(challenger.seed).permutation(b.samples[TOTAL])
    independent = shuffled - a.samples[TOTAL]
    p5, p95 = np.percentile(independent, [5, 95])
    ends_low = b.summaries[TOTAL]["p5"] - a.summaries[TOTAL]["p95"]
    ends_high = b.summaries[TOTAL]["p95"] - a.summaries[TOTAL]["p5"]
    summary = mc.summarise(difference)
    return {
        "evaluations": (a, b),
        "node": {
            "label": "challenger minus incumbent, five-year total",
            "unit": "USD",
            "point": point(model, challenger)[TOTAL] - point(model, incumbent)[TOTAL],
            "summary": summary,
            "histogram": mc.histogram(difference),
        },
        "paired": {
            "share_challenger_cheaper": float((difference < 0).mean()),
            "share_incumbent_cheaper": float((difference > 0).mean()),
            "width": summary["p95"] - summary["p5"],
            "independent": {"p5": float(p5), "p95": float(p95), "width": float(p95 - p5)},
            "ends": {"low": ends_low, "high": ends_high, "width": ends_high - ends_low},
            "shared_inputs": len(shared),
        },
    }


def _difference_with(
    model: Model, incumbent: Scenario, challenger: Scenario, name: str, value: float, whose: str
) -> float:
    """Challenger minus incumbent at the point, with one input set to ``value``.

    A line of the challenger's quote changes on that side only. A shared input changes on both:
    it is the same electricity price for both fleets, which is the whole point of pairing.
    """
    b = replace(challenger, overrides={**challenger.overrides, name: value})
    a = incumbent
    if whose == "shared":
        a = replace(incumbent, overrides={**incumbent.overrides, name: value})
    return point(model, b)[TOTAL] - point(model, a)[TOTAL]


def _tie_point(
    model: Model, incumbent: Scenario, challenger: Scenario, name: str, whose: str
) -> tuple[float, float | None, float]:
    """Where the two totals tie as one input moves, or None if no value moves the difference.

    Secant first, because every line here is linear in its input and two evaluations settle a
    line; the result is put back into the model and checked, and bisection over the declared
    range takes over if the check fails. Returns the value the quote has, the tie, and the sign
    of the slope so a table can say which way the ordering goes as the input rises.
    """
    node = model.nodes[name]
    assert isinstance(node, Input)
    at = challenger.overrides.get(name)
    if at is None:
        at = point(model, challenger)[name]
    scale = float(node.slider[1] - node.slider[0]) if node.slider else abs(at) or 1.0
    step = scale * 0.1 or 1.0
    d0 = _difference_with(model, incumbent, challenger, name, at, whose)
    d1 = _difference_with(model, incumbent, challenger, name, at + step, whose)
    slope = (d1 - d0) / step
    total = abs(point(model, incumbent)[TOTAL])
    if abs(slope * scale) < TIE_TOLERANCE * total:
        return at, None, 0.0
    tie = at - d0 / slope
    if (
        abs(_difference_with(model, incumbent, challenger, name, tie, whose))
        > TIE_TOLERANCE * total
    ):
        low, high = node.slider or (min(at, tie), max(at, tie))
        f_low = _difference_with(model, incumbent, challenger, name, low, whose)
        f_high = _difference_with(model, incumbent, challenger, name, high, whose)
        if f_low * f_high > 0:
            return at, None, float(np.sign(slope))
        for _ in range(200):
            mid = (low + high) / 2
            f_mid = _difference_with(model, incumbent, challenger, name, mid, whose)
            if f_low * f_mid <= 0:
                high, f_high = mid, f_mid
            else:
                low, f_low = mid, f_mid
        tie = (low + high) / 2
    return at, tie, float(np.sign(slope))


def break_evens(model: Model, incumbent: Scenario, challenger: Scenario) -> list[dict]:
    rows = []
    for name, whose in BREAK_EVENS:
        node = model.nodes[name]
        assert isinstance(node, Input)
        at, tie, direction = _tie_point(model, incumbent, challenger, name, whose)
        low, high = node.slider or (None, None)
        swing = swing_of(model, name) if whose == "shared" else None
        rows.append(
            {
                "input": name,
                "label": node.display,
                "unit": node.unit,
                "whose": whose,
                "at": at,
                "ties_at": tie,
                # Whether the tie lies inside the range the model admits for this input, and,
                # for an input the model is uncertain about, inside the middle eighty per cent
                # of what it could be. A break-even outside both is a comparison this input
                # cannot flip.
                # How far from the quote the tie is, for a line the challenger could move.
                "from_quote": (tie - at) / at if tie is not None and at else None,
                "in_range": tie is not None and low is not None and low <= tie <= high,
                "in_swing": tie is not None and swing is not None and swing[0] <= tie <= swing[1],
                "range_low": low,
                "range_high": high,
                "swing_low": swing[0] if swing else None,
                "swing_high": swing[1] if swing else None,
                "rises_with_input": direction,
            }
        )
    return rows


def tornado_of_difference(model: Model, incumbent: Scenario, challenger: Scenario) -> list[dict]:
    """How far the difference moves when each shared uncertain input is swung on its own."""
    base = point(model, challenger)[TOTAL] - point(model, incumbent)[TOTAL]
    bars = []
    for name in sampled_inputs(model):
        if name in challenger.overrides or name in model.blocked():
            continue
        swing = swing_of(model, name)
        if swing is None:
            continue
        low, high = (
            _difference_with(model, incumbent, challenger, name, value, "shared") for value in swing
        )
        # An input that reaches neither total, or both equally, leaves the difference where it
        # was, and floating-point noise must not turn that into a bar a hundredth of a dollar
        # long. Snapped, so the chart can say how many inputs do not move it at all.
        if abs(high - low) < 1e-6 * max(abs(base), 1.0):
            low = high = base
        bars.append(
            {
                "node": name,
                "label": model.nodes[name].display,
                "kind": model.nodes[name].kind,
                "low": low,
                "high": high,
                "base": base,
                "span": abs(high - low),
            }
        )
    return sorted(bars, key=lambda bar: bar["span"], reverse=True)


def comparison(write: bool = True) -> dict:
    model = load_model(MODEL)
    incumbent, challenger = load_scenario(INCUMBENT), load_scenario(CHALLENGER)
    if (incumbent.seed, incumbent.samples) != (challenger.seed, challenger.samples):
        raise ValueError("the two quotes must share a seed and a sample count to share futures")
    paired = paired_difference(model, incumbent, challenger)
    a, b = paired.pop("evaluations")
    designs = {
        "incumbent": design_summary(model, incumbent, a),
        "challenger": design_summary(model, challenger, b),
    }
    lines = lines_of(model, incumbent, challenger)
    evens = break_evens(model, incumbent, challenger)
    bars = tornado_of_difference(model, incumbent, challenger)

    units: dict[str, str] = {
        "designs.incumbent.hosts": "host",
        "designs.incumbent.tco": "USD",
        "designs.incumbent.ceilings": "dimensionless",
        "designs.challenger.hosts": "host",
        "designs.challenger.tco": "USD",
        "designs.challenger.ceilings": "dimensionless",
        "lines": "USD",
        "nodes.difference.point": "USD",
        "nodes.difference.summary": "USD",
        "nodes.difference.histogram.counts": "dimensionless",
        "nodes.difference.histogram.edges": "USD",
        "tornado.difference": "USD",
        "paired.share_challenger_cheaper": "dimensionless",
        "paired.share_incumbent_cheaper": "dimensionless",
        "paired.width": "USD",
        "paired.independent": "USD",
        "paired.ends": "USD",
        "paired.shared_inputs": "dimensionless",
    }
    for who in ("incumbent", "challenger"):
        for i, row in enumerate(designs[who]["quote"]):
            units[f"designs.{who}.quote[{i}]"] = row["unit"]
    for i, row in enumerate(evens):
        units[f"break_even[{i}]"] = row["unit"]
        if row["from_quote"] is not None:
            units[f"break_even[{i}].from_quote"] = "dimensionless"
        units[f"break_even[{i}].rises_with_input"] = "dimensionless"

    return build_result(
        "comparison",
        target="model",
        kind="measurement",
        produced_by={
            "method": "both quotes evaluated on the same draws and subtracted sample by sample; "
            "lines and break-evens at the point estimate",
            "model": model.name,
            "scenario": f"{incumbent.name} and {challenger.name}",
            "seed": incumbent.seed,
            "samples": incumbent.samples,
            "stack": "sizing.evaluate",
        },
        summary={
            "designs": designs,
            "lines": lines,
            "nodes": {"difference": paired["node"]},
            "tornado": {"difference": bars},
            "paired": paired["paired"],
            "break_even": evens,
        },
        units=units,
        conditions={
            "shared_futures": "both scenarios pin the same inputs and share a seed, so every "
            "input neither quote fixes is drawn once and reaches both designs. The runner "
            "checks the shared columns are identical before subtracting",
            "quotes_held_exactly": "a quote is a number, so every line of both quotes is pinned. "
            "Nothing here is about what either vendor would charge after negotiation, and the "
            "incumbent's quote is the model's own point estimate held exactly",
            "the_move_is_an_estimate": "migration_cost on the challenger's side is the team's "
            "own figure, marked as an assumption; the incumbent's is a declared zero",
            "break_evens_at_the_point": "each break-even is where the two totals tie with "
            "everything else at its point value. It says which input could flip the ordering "
            "and where, not how likely that is",
            "one_model": "a line neither quote has is a line neither total has. The comparison "
            "is as complete as the model, and no more (ch20)",
        },
        code_sources=SOURCES,
        write=write,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-run and diff against the stamp")
    arguments = parser.parse_args(argv)

    fresh = comparison(write=not arguments.check)
    if not arguments.check:
        print("  wrote bench/results/comparison.json")
        print("\nrun_comparison: OK")
        return 0

    if not result_exists("comparison"):
        print("comparison has never been run", file=sys.stderr)
        return 1
    differences = numeric_differences(load_result("comparison")["summary"], fresh["summary"])
    if differences:
        print("comparison moved:", file=sys.stderr)
        for line in differences:
            print(f"  {line}", file=sys.stderr)
        return 1
    print("  ok: comparison")
    print("\nrun_comparison: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
