"""What a measurement would actually buy, computed rather than argued about.

    python3 -m bench.run_information            # run it and write the result
    python3 -m bench.run_information --check    # re-run and fail if a published figure moved

ch19 ranks the inputs with a tornado, and a tornado answers *which input should I go and measure
first*. It does not answer the question that follows, which is the one somebody has to approve:
**and what would that buy?** A ranking is not a quantity. This is the quantity.

The experiment is the simplest thing that means anything. Take one uncertain input, pin it at its
median — pretend somebody went and measured it, perfectly — and re-sample the whole model. The
interval that comes back is what the model would say if that one thing were known. The difference
between it and the interval you have now is the *most* that measuring that input could be worth,
because no real measurement is perfect.

An upper bound is the right shape of answer here. A real measurement leaves a standard error
behind, and how big that error would be is not knowable before doing the work — so a figure that
claimed to predict it would be inventing the number this book refuses to invent. What can be
computed is the ceiling: measure this thing as well as it can possibly be measured, and the
interval still does not close by more than this. If the ceiling is small, the measurement is not
worth commissioning whatever its standard error turns out to be. That is a decision somebody can
take from this table and cannot take from a tornado.

Two further things fall out of running it, and both are worth more than the headline:

**The reductions do not add up.** Pin every uncertain input one at a time, total what each one
removed, and the total is not a hundred per cent — it is nowhere near it. Uncertainty in a chain
of multiplications is not a pie that can be divided between the inputs, and a sensitivity figure
that invites that reading is inviting a mistake (ch19).

**Knowing everything is not the same as knowing anything.** The last row pins every uncertain
input at once. The interval collapses, because a model with no uncertain inputs is arithmetic —
which is a useful reminder of what the interval was ever a statement about. It was never a
statement about the world. It was a statement about what had been written down.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from bench.stamp import build_result, load_result, numeric_differences, result_exists
from sizing import mc
from sizing.dsl import Input, Measured, Model, Scenario, load_model, load_scenario
from sizing.evaluate import evaluate, point_value_of_input, sampled_inputs

SOURCES = ["bench/run_information.py"]

#: One model, one output, per row of the published table. Three subjects rather than one because
#: the shape of the answer differs, and the difference is the point. The web service's five-year
#: total spreads its uncertainty across what people and licences cost, and no single input is
#: worth much on its own; its recommended host count rests almost entirely on a growth rate; the
#: observability model's retention store is concentrated in two inputs. Which of those a table
#: describes decides whether commissioning one measurement is worth anything at all.
SUBJECTS = (
    ("models/web_service/model.yaml", "models/web_service/scenarios/reference.yaml", "tco"),
    (
        "models/web_service/model.yaml",
        "models/web_service/scenarios/reference.yaml",
        "hosts_recommended",
    ),
    (
        "models/observability/model.yaml",
        "models/observability/scenarios/reference.yaml",
        "known_stored",
    ),
)


def without_uncertainty(model: Model, scenario: Scenario, names: tuple[str, ...]) -> Model:
    """The same model with ``names`` known exactly, at the value a point estimate would use.

    An input loses its distribution and keeps its median. A measured constant keeps its value and
    loses its standard error — which is the same act, since a standard error is the whole of what
    a measured node contributes to the spread.

    Any correlation naming a pinned input goes with it. A correlation is a statement about two
    quantities moving together, and a quantity that is known does not move.
    """
    nodes = dict(model.nodes)
    for name in names:
        node = nodes[name]
        if isinstance(node, Input):
            nodes[name] = replace(
                node, distribution=None, value=point_value_of_input(node, scenario)
            )
        elif isinstance(node, Measured) and node.measurement is not None:
            summary = {**node.measurement["summary"], "sd": 0.0}
            nodes[name] = replace(node, measurement={**node.measurement, "summary": summary})
    correlations = tuple(
        pair for pair in model.correlations if pair["a"] not in names and pair["b"] not in names
    )
    return replace(model, nodes=nodes, correlations=correlations)


def _half_width(model: Model, scenario: Scenario, output: str) -> float:
    """The interval's half-width, or zero when nothing upstream of the output varies any more.

    An evaluation only carries samples for the nodes that move. Pin every uncertain input and the
    output stops being an array and stops appearing there at all, which is the answer rather than
    a missing case: a model with nothing uncertain in it has an interval of zero width.
    """
    drawn = evaluate(model, scenario).samples.get(output)
    return float(mc.half_width(drawn)) if drawn is not None else 0.0


def value_of_information(write: bool = True) -> dict:
    """For every uncertain input of every subject: the interval if it were known exactly."""
    rows: list[dict] = []
    totals: list[dict] = []
    for model_path, scenario_path, output in SUBJECTS:
        model, scenario = load_model(model_path), load_scenario(scenario_path)
        blocked = model.blocked()
        baseline = _half_width(model, scenario, output)
        uncertain = [
            name
            for name in sampled_inputs(model)
            if name not in blocked and name in model.ancestors(output)
        ]
        for name in uncertain:
            known = _half_width(without_uncertainty(model, scenario, (name,)), scenario, output)
            rows.append(
                {
                    "model": model.name,
                    "output": output,
                    "input": name,
                    "label": model.nodes[name].display,
                    "kind": model.nodes[name].kind,
                    "half_width": baseline,
                    "if_known": known,
                    # The most that measuring this one thing could remove, as a fraction of the
                    # interval there is now. Not what a measurement will buy — what the best
                    # imaginable one could.
                    "removed": 1.0 - known / baseline if baseline else 0.0,
                }
            )
        mine = [row for row in rows if row["model"] == model.name and row["output"] == output]
        everything = _half_width(
            without_uncertainty(model, scenario, tuple(uncertain)), scenario, output
        )
        totals.append(
            {
                "model": model.name,
                "output": output,
                "half_width": baseline,
                "inputs": len(uncertain),
                # Each input pinned alone, totalled. If uncertainty were a pie this would come to
                # one; it does not, and the gap is the interaction a one-at-a-time figure cannot
                # show (ch19, problem 18.2).
                "sum_of_removals": sum(row["removed"] for row in mine),
                # Everything pinned at once. A model with nothing uncertain in it is arithmetic.
                "all_known": everything,
                "best_single": max((row["removed"] for row in mine), default=0.0),
            }
        )
    return build_result(
        "value-of-information",
        target="model",
        kind="measurement",
        produced_by={
            "method": "each uncertain input pinned at its median in turn, and the model resampled",
            "model": " and ".join(sorted({row["model"] for row in rows})),
            "scenario": "reference",
            "seed": load_scenario("models/web_service/scenarios/reference.yaml").seed,
            "stack": "sizing.evaluate",
        },
        summary={"rows": rows, "totals": totals},
        units={
            "rows": "dimensionless",
            "rows[0].removed": "dimensionless",
            "totals": "dimensionless",
            "totals[0].sum_of_removals": "dimensionless",
        },
        conditions={
            "this_is_an_upper_bound": "each figure is what knowing the input *exactly* would "
            "remove. A real measurement leaves a standard error behind and removes less, by an "
            "amount nobody can know before doing the work",
            "removals_do_not_add": "the sum of the individual removals is not one. Uncertainty in "
            "a chain of multiplications is not a quantity that divides between the inputs, and a "
            "figure read that way is read wrongly (ch19)",
            "what_it_cannot_say": "whether the input can be measured at all. The web service's "
            "total rests on how many people it takes and what a licence costs, which are decided "
            "and negotiated rather than measured; its host count and the observability model's "
            "store both rest on a growth rate, which belongs to no target. The honest response "
            "to those is to decide them rather than to commission a measurement (ch04)",
        },
        code_sources=SOURCES,
        write=write,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-run and diff against the stamp")
    arguments = parser.parse_args(argv)

    fresh = value_of_information(write=not arguments.check)
    if not arguments.check:
        print("  wrote bench/results/value-of-information.json")
        print("\nrun_information: OK")
        return 0

    if not result_exists("value-of-information"):
        print("value-of-information has never been run", file=sys.stderr)
        return 1
    # Summaries only: the stamp carries a timestamp, and a re-run always has a newer one.
    differences = numeric_differences(
        load_result("value-of-information")["summary"], fresh["summary"]
    )
    if differences:
        print("value-of-information moved:", file=sys.stderr)
        for line in differences:
            print(f"  {line}", file=sys.stderr)
        return 1
    print("  ok: value-of-information")
    print("\nrun_information: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
