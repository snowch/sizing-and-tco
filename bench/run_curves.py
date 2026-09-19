"""Sweeps: the figures that are a shape rather than a number.

    python3 -m bench.run_curves            # run them and write the results
    python3 -m bench.run_curves --check    # re-run and fail if a published figure moved

Three chapters in Part II and Part III argue about shapes — where a curve turns, which of three
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

WEB_SERVICE = "models/web_service/model.yaml"
REFERENCE = "models/web_service/scenarios/reference.yaml"

#: Utilisations to sweep. Bunched towards the top on purpose: the interesting half of this curve
#: is the last tenth of it, and an evenly spaced sweep spends most of its points on the flat part
#: where nothing happens.
UTILISATIONS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.93, 0.95, 0.97)

#: Host counts for the scaling sweep, well past the peak so that the turn is visible rather than
#: inferred. A curve cut off before it turns over is a curve that looks like it never does.
#:
#: From two, not one. A fleet of one host has no failure headroom - nothing is left when it
#: dies - and the model says so by dividing by zero rather than by pretending otherwise.
HOST_COUNTS = (2, 4, 8, 16, 32, 64, 96, 128, 160, 200, 256, 320, 400)


def queueing_curve(write: bool = True) -> dict:
    """Residence time against utilisation, swept out of the web service model.

    The request rate is what moves; everything else is held at the reference point. So each row
    is the same fleet, the same software and the same machines, serving more requests — which is
    the only honest way to draw this curve, because changing the service demand instead would
    move the vertical axis as well as the horizontal one.
    """
    model = load_model(WEB_SERVICE)
    scenario = load_scenario(REFERENCE)
    factors = conversion_factors(model)
    base = point(model, scenario, factors)

    # The busy-hour rate that produces a given utilisation, from the reference fleet's own
    # numbers. What a scenario can pin is the rate at the start of the horizon and the model
    # grows it from there, so the growth already in the reference point is divided out first.
    per_request = base["service_demand"]
    cores = base["cores"]
    growth = base["peak_request_rate"] / base["peak_request_rate_t0"]
    rows = []
    for target in UTILISATIONS:
        arrivals = target * cores / per_request
        forced = replace(
            scenario, overrides={**scenario.overrides, "peak_request_rate_t0": arrivals / growth}
        )
        values = point(model, forced, factors)
        rows.append(
            {
                "utilisation": values["utilisation"],
                "arrival_rate": values["peak_request_rate"],
                "residence_time": values["residence_time"],
                "waiting_time": values["waiting_time"],
                "concurrency": values["concurrency"],
                # How much longer a request takes than it would on an idle fleet. The number
                # people think they are quoting when they quote a utilisation.
                "inflation": values["residence_time"] / values["service_seconds"],
            }
        )
    return build_result(
        "queueing-curve",
        target="model",
        produced_by={
            "model": "web_service",
            "scenario": "reference",
            "seed": load_scenario(REFERENCE).seed,
            "method": "the busy-hour request rate swept to hit each utilisation, everything "
            "else held still",
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
            "one_slice": "the request rate moves and nothing else does. A service whose demand "
            "per request also rises with load - which is most of them - is on a steeper curve "
            "than this one",
            "the_cap": "the model clamps utilisation before it divides by zero; past that point "
            "the formula has stopped describing a queue",
        },
        code_sources=SOURCES,
        write=write,
    )


def scaling_curve(write: bool = True) -> dict:
    """Throughput against host count, and the straight line nobody gets."""
    model = load_model(WEB_SERVICE)
    scenario = load_scenario(REFERENCE)
    factors = conversion_factors(model)
    rows = []
    for count in HOST_COUNTS:
        forced = replace(scenario, overrides={**scenario.overrides, "hosts": float(count)})
        values = point(model, forced, factors)
        rows.append(
            {
                "hosts": float(count),
                "achievable_throughput": values["achievable_throughput"],
                "linear_throughput": values["linear_throughput"],
                "scaling_efficiency": values["scaling_efficiency"],
                # What the last batch of machines actually bought, per machine.
                "throughput_per_host": values["achievable_throughput"] / count,
            }
        )
    best = max(rows, key=lambda row: row["achievable_throughput"])
    return build_result(
        "scaling-curve",
        target="model",
        produced_by={
            "model": "web_service",
            "scenario": "reference",
            "seed": load_scenario(REFERENCE).seed,
            "method": "the host count swept from two to four hundred",
            "stack": "sizing.evaluate",
        },
        summary={
            "curve": rows,
            "peak_at_hosts": best["hosts"],
            "peak_throughput": best["achievable_throughput"],
            "predicted_peak": point(model, scenario, factors)["peak_hosts"],
        },
        units={
            "curve": "request/second",
            "curve[0].hosts": "host",
            "curve[0].scaling_efficiency": "dimensionless",
            "curve[0].throughput_per_host": "request/second",
            "peak_at_hosts": "host",
            "peak_throughput": "request/second",
            "predicted_peak": "host",
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
    """How often each of the web service's three chains decides the answer.

    ch10's whole subject, as a count rather than a claim. Three independent chains each produce
    a host count and you buy the largest, so across the model's uncertainty the answer is
    sometimes set by the request rate, sometimes by the working set and sometimes by the data on
    disk - and an average of the three would satisfy none of them.
    """
    model = load_model(WEB_SERVICE)
    evaluation = evaluate(model, load_scenario(REFERENCE))
    chains = {
        name: np.asarray(evaluation.samples[f"hosts_for_{name}"], dtype=float)
        for name in ("requests", "memory", "storage")
    }
    stacked = np.stack(list(chains.values()))
    # Decided outright: this chain alone asked for the most. Two chains asking for the same
    # count is its own row rather than a coincidence to split between them, because it is the
    # case where relieving one of them changes nothing.
    decides = {
        name: float(np.mean(drawn > np.delete(stacked, index, axis=0).max(axis=0)))
        for index, (name, drawn) in enumerate(chains.items())
    }
    # And the other way round: size on one chain alone, and how often is the fleet too small.
    short = {
        name: float(np.mean(np.delete(stacked, index, axis=0).max(axis=0) > drawn))
        for index, (name, drawn) in enumerate(chains.items())
    }
    ordered = np.sort(stacked, axis=0)
    gap = ordered[-1] - ordered[-2]
    return build_result(
        "binding-constraint",
        target="model",
        produced_by={
            "model": "web_service",
            "scenario": "reference",
            "seed": load_scenario(REFERENCE).seed,
            "method": "sampled, and the three host-count chains compared draw by draw",
            "stack": "sizing.evaluate",
        },
        summary={
            "requests_binds": decides["requests"],
            "memory_binds": decides["memory"],
            "storage_binds": decides["storage"],
            "tied": 1.0 - sum(decides.values()),
            "short_if_requests": short["requests"],
            "short_if_memory": short["memory"],
            "short_if_storage": short["storage"],
            "median_gap": float(np.median(gap)),
            "p95_gap": float(np.percentile(gap, 95)),
            # How wrong you would be to size on any one chain and forget the others - and how
            # much bigger the largest of three uncertain counts is than any one of them usually
            # is, which is the part of ch10 that surprises people.
            "median_requests_hosts": float(np.median(chains["requests"])),
            "median_memory_hosts": float(np.median(chains["memory"])),
            "median_storage_hosts": float(np.median(chains["storage"])),
            "median_largest": float(np.median(ordered[-1])),
        },
        units={
            "requests_binds": "dimensionless",
            "memory_binds": "dimensionless",
            "storage_binds": "dimensionless",
            "tied": "dimensionless",
            "short_if_requests": "dimensionless",
            "short_if_memory": "dimensionless",
            "short_if_storage": "dimensionless",
            "median_gap": "host",
            "p95_gap": "host",
            "median_requests_hosts": "host",
            "median_memory_hosts": "host",
            "median_storage_hosts": "host",
            "median_largest": "host",
        },
        conditions={
            "three_chains_only": "this model has three. A real service has more - a database's "
            "connection limit, a cache's eviction rate, the network between them - and each one "
            "is another chance for the answer to be set by something nobody was watching",
            "the_largest_of_three": "the recommended count is the largest of three uncertain "
            "numbers, and the largest of three sits above where any one of them usually does. "
            "Sizing on the chain that wins most often is still sizing on one chain, and the "
            "other two are larger whenever it loses",
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
