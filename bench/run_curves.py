"""Sweeps: the figures that are a shape rather than a number.

    python3 -m bench.run_curves            # run them and write the results
    python3 -m bench.run_curves --check    # re-run and fail if a published figure moved

Three chapters in Part II and Part III argue about shapes — where a curve turns, which of two
chains wins, how far a number moves when one input does. A shape asserted in prose is a claim; a
shape swept out of the model the chapter is about is evidence, and it moves when the model does.

Every sweep here holds the model at its reference point and moves exactly one thing, which is
also the limitation each chapter has to state: a curve drawn by moving one input is a slice
through a surface, and the surface is not flat.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace

import numpy as np

from bench.stamp import build_result, load_result, numeric_differences, result_exists
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import conversion_factors, evaluate, point

SOURCES = ["bench/run_curves.py"]

SERVICE_TIER = "models/service_tier/model.yaml"
SERVICE_REFERENCE = "models/service_tier/scenarios/reference.yaml"
STORAGE = "models/storage_cluster/model.yaml"
STORAGE_REFERENCE = "models/storage_cluster/scenarios/reference.yaml"

#: Utilisations to sweep. Bunched towards the top on purpose: the interesting half of this curve
#: is the last tenth of it, and an evenly spaced sweep spends most of its points on the flat part
#: where nothing happens.
UTILISATIONS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.93, 0.95, 0.97)

#: Node counts for the scaling sweep, well past the peak so that the turn is visible rather than
#: inferred. A curve cut off before it turns over is a curve that looks like it never does.
NODE_COUNTS = (1, 2, 4, 8, 16, 32, 64, 96, 128, 160, 200, 256, 320, 400)


def queueing_curve(write: bool = True) -> dict:
    """Residence time against utilisation, swept out of the service tier model.

    The arrival rate is what moves; everything else is held at the reference point. So each row is
    the same tier, the same software and the same machines, serving more requests — which is the
    only honest way to draw this curve, because changing the service demand instead would move the
    vertical axis as well as the horizontal one.
    """
    model = load_model(SERVICE_TIER)
    scenario = load_scenario(SERVICE_REFERENCE)
    factors = conversion_factors(model)
    base = point(model, scenario, factors)

    # The arrival rate that produces a given utilisation, from the reference tier's own numbers.
    per_request = base["service_demand"]
    nodes = base["nodes"]
    rows = []
    for target in UTILISATIONS:
        arrivals = target * nodes / per_request
        forced = replace(scenario, overrides={**scenario.overrides, "arrival_rate": arrivals})
        values = point(model, forced, factors)
        rows.append(
            {
                "utilisation": values["utilisation"],
                "arrival_rate": arrivals,
                "residence_time": values["residence_time"],
                "waiting_time": values["waiting_time"],
                "concurrency": values["concurrency"],
                # How much longer a request takes than it would on an idle tier. The number people
                # think they are quoting when they quote a utilisation.
                "inflation": values["residence_time"] / values["service_seconds"],
            }
        )
    return build_result(
        "queueing-curve",
        target="model",
        produced_by={
            "model": "service_tier",
            "scenario": "reference",
            "method": "arrival_rate swept to hit each utilisation, everything else held still",
            "stack": "sizing.evaluate",
        },
        summary={"curve": rows, "utilisations": list(UTILISATIONS)},
        units={
            "curve": "second",
            "curve[0].utilisation": "dimensionless",
            "curve[0].arrival_rate": "request/second",
            "curve[0].concurrency": "request",
            "curve[0].inflation": "dimensionless",
            "utilisations": "dimensionless",
        },
        conditions={
            "one_slice": "the arrival rate moves and nothing else does. A tier whose service "
            "demand also rises with load - which is most of them - is on a steeper curve than "
            "this one",
            "the_cap": "the model clamps utilisation before it divides by zero; past that point "
            "the formula has stopped describing a queue",
        },
        code_sources=SOURCES,
        write=write,
    )


def scaling_curve(write: bool = True) -> dict:
    """Throughput against node count, and the straight line nobody gets."""
    model = load_model(SERVICE_TIER)
    scenario = load_scenario(SERVICE_REFERENCE)
    factors = conversion_factors(model)
    rows = []
    for count in NODE_COUNTS:
        forced = replace(scenario, overrides={**scenario.overrides, "nodes": float(count)})
        values = point(model, forced, factors)
        rows.append(
            {
                "nodes": float(count),
                "achievable_throughput": values["achievable_throughput"],
                "linear_throughput": values["linear_throughput"],
                "scaling_efficiency": values["scaling_efficiency"],
                # What the last batch of machines actually bought, per machine.
                "throughput_per_node": values["achievable_throughput"] / count,
            }
        )
    best = max(rows, key=lambda row: row["achievable_throughput"])
    return build_result(
        "scaling-curve",
        target="model",
        produced_by={
            "model": "service_tier",
            "scenario": "reference",
            "method": "the node count swept from one to four hundred",
            "stack": "sizing.evaluate",
        },
        summary={
            "curve": rows,
            "peak_at_nodes": best["nodes"],
            "peak_throughput": best["achievable_throughput"],
            "predicted_peak": point(model, scenario, factors)["peak_nodes"],
        },
        units={
            "curve": "request/second",
            "curve[0].nodes": "node",
            "curve[0].scaling_efficiency": "dimensionless",
            "curve[0].throughput_per_node": "request/second",
            "peak_at_nodes": "node",
            "peak_throughput": "request/second",
            "predicted_peak": "node",
        },
        conditions={
            "swept_and_predicted": "the peak found by sweeping and the peak the two coefficients "
            "predict are computed independently and must agree; if they ever stop agreeing, one "
            "of them is wrong",
            "coefficients_are_assumptions": "contention and crosstalk are fitted in practice, and "
            "in this model they are assumptions. The shape is the claim, not the position",
        },
        code_sources=SOURCES,
        write=write,
    )


def binding_constraint(write: bool = True) -> dict:
    """How often each of the storage model's two chains decides the answer.

    ch10's whole subject, as a count rather than a claim. Two independent chains produce two node
    counts and you buy the larger, so across the model's uncertainty the answer is sometimes set
    by capacity and sometimes by bandwidth - and an average of the two would satisfy neither.
    """
    model = load_model(STORAGE)
    evaluation = evaluate(model, load_scenario(STORAGE_REFERENCE))
    capacity = evaluation.samples["nodes_for_capacity"]
    throughput = evaluation.samples["nodes_for_throughput"]
    binds_on_capacity = float(np.mean(capacity >= throughput))
    gap = np.abs(capacity - throughput)
    return build_result(
        "binding-constraint",
        target="model",
        produced_by={
            "model": "storage_cluster",
            "scenario": "reference",
            "method": "sampled, and the two node-count chains compared draw by draw",
            "stack": "sizing.evaluate",
        },
        summary={
            "capacity_binds": binds_on_capacity,
            "throughput_binds": 1.0 - binds_on_capacity,
            "median_gap": float(np.median(gap)),
            "p95_gap": float(np.percentile(gap, 95)),
            # How wrong you would be to size on the capacity chain alone and forget the other.
            "median_capacity_nodes": float(np.median(capacity)),
            "median_throughput_nodes": float(np.median(throughput)),
        },
        units={
            "capacity_binds": "dimensionless",
            "throughput_binds": "dimensionless",
            "median_gap": "node",
            "p95_gap": "node",
            "median_capacity_nodes": "node",
            "median_throughput_nodes": "node",
        },
        conditions={
            "two_chains_only": "this model has two. A real estate has more - rebuild bandwidth, "
            "metadata operations, a control plane - and each one is another chance for the answer "
            "to be set by something nobody was watching",
        },
        code_sources=SOURCES,
        write=write,
    )


RUNNERS = {
    "queueing-curve": queueing_curve,
    "scaling-curve": scaling_curve,
    "binding-constraint": binding_constraint,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    failures = []
    for name, runner in RUNNERS.items():
        if not args.check:
            runner()
            continue
        if not result_exists(name):
            print(f"  MISSING: bench/results/{name}.json")
            failures.append(name)
            continue
        moved = numeric_differences(load_result(name)["summary"], runner(write=False)["summary"])
        if moved:
            print(f"  MOVED: {name} no longer matches what the model produces")
            for line in moved[:6]:
                print(f"    {line}")
            failures.append(name)
        else:
            print(f"  ok: {name}")
    if failures:
        print("\nrun_curves: FAILED - re-run and read what moved before committing.")
        return 1
    print(f"\nrun_curves: OK ({len(RUNNERS)} sweep(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
