"""The two experiments ch12 and ch13 are built on.

    python3 -m bench.run_uncertainty            # run them and write the results
    python3 -m bench.run_uncertainty --check    # re-run and fail if a published figure moved

Neither chapter asserts what Monte Carlo does; both show it. So the claims that would otherwise
be the reader's to take on trust are arranged here as measurements with stamps on them, exactly
like every other number in this book:

**Convergence.** This one caught an error in its own first draft, which is why it is written the
way it is. The obvious experiment — measure the interval at rising sample counts and watch it
narrow — does not work, because *the interval does not narrow*. A 90% interval is a property of
the distribution the model describes, and more samples do not make that distribution smaller;
they converge on it. Running it settles at about the same width from ten thousand draws upwards.

What falls as one over the square root of n is how precisely you know **where** that interval is.
So the model is run many times over at each sample count, with a different seed each time, and
what is recorded is the *spread between those runs*. That is the quantity the square-root law
governs, and it is also the one that answers the question people actually have: how many samples
is enough? Enough is when the answer stops moving between runs at the precision you are going to
report it to.

**Correlation.** The same model sampled twice, once with its declared correlations and once with
them removed. The difference is what assuming independence was worth — and the direction of the
difference is the part worth seeing rather than being told.
"""

from __future__ import annotations

import argparse
import math
import sys

import numpy as np

from bench.stamp import build_result, load_result, numeric_differences, result_exists
from sizing import mc
from sizing.dsl import Model, Scenario, load_model, load_scenario, scenarios_for
from sizing.evaluate import evaluate

SOURCES = ["bench/run_uncertainty.py"]

#: Sample counts for the convergence run.
COUNTS = (100, 1_000, 10_000, 100_000)

#: Independent runs at each count. The whole experiment is about how far apart two runs land, so
#: this is the sample size that matters — and it is the one people cut first.
#:
#: Thirty-two, not a dozen, and the reason is the chapter's own argument applied to the chapter's
#: own figure. A standard deviation estimated from twelve numbers carries about twenty per cent
#: noise of its own, which is enough to move a ratio of two of them from three to five and make
#: the square-root law look like it does not hold. Measuring how uncertain something is, is
#: itself an uncertain measurement, and the figure that demonstrates a law had better not be the
#: one place in the book that forgets it.
REPLICATES = 32

#: The law is measured from this sample count upwards. See :func:`convergence`.
LAW_FROM = 1_000

STORAGE = "models/storage_cluster/model.yaml"
REFERENCE = "models/storage_cluster/scenarios/reference.yaml"


def _sample_output(model: Model, scenario: Scenario, output: str, samples: int, seed: int):
    from dataclasses import replace

    return evaluate(model, replace(scenario, samples=samples, seed=seed)).samples[output]


def convergence(write: bool = True) -> dict:
    """How precisely the interval is known, as the sample count rises.

    Replicates rather than a single run per count: the thing being measured is run-to-run
    variation, and one run cannot show it. Each replicate is an independent draw with its own
    seed, so the spread between them is exactly the sampling noise a reader would meet by running
    the model twice and getting two different answers.
    """
    model, scenario = load_model(STORAGE), load_scenario(REFERENCE)
    points = []
    for count in COUNTS:
        estimates = []
        for replicate in range(REPLICATES):
            drawn = _sample_output(
                model, scenario, "tco", count, scenario.seed + count * 977 + replicate
            )
            estimates.append(
                {
                    "p5": float(np.percentile(drawn, 5)),
                    "p50": float(np.percentile(drawn, 50)),
                    "p95": float(np.percentile(drawn, 95)),
                    "half_width": mc.half_width(drawn),
                }
            )
        points.append(
            {
                "samples": count,
                "replicates": REPLICATES,
                # The interval itself: settles, and does not shrink. This is the row that stops a
                # reader believing more samples make a model more certain.
                "half_width": float(np.mean([e["half_width"] for e in estimates])),
                # How far apart two runs land. This is what one over the square root of n governs.
                "p95_spread": float(np.std([e["p95"] for e in estimates], ddof=1)),
                "p50_spread": float(np.std([e["p50"] for e in estimates], ddof=1)),
                "p95_mean": float(np.mean([e["p95"] for e in estimates])),
            }
        )

    # The law, checked rather than assumed: each ten-fold increase in samples should shrink the
    # run-to-run spread by about the square root of ten.
    #
    # Measured from LAW_FROM upwards, and the exclusion is not a convenience. The square-root law
    # is exact for a mean and only asymptotic for a tail percentile, and a p95 estimated from a
    # hundred draws is the fifth largest of them — bounded by the sample itself, and nowhere near
    # the regime where the law applies. The smallest row stays in the table because it is the
    # clearest demonstration of the *other* half of this figure, that the interval settles; it is
    # simply not evidence about the law and is not used as if it were.
    usable = [point for point in points if point["samples"] >= LAW_FROM]
    ratios = [usable[i]["p95_spread"] / usable[i + 1]["p95_spread"] for i in range(len(usable) - 1)]
    decades = math.log10(usable[-1]["samples"] / usable[0]["samples"])
    overall = (usable[0]["p95_spread"] / usable[-1]["p95_spread"]) ** (1.0 / decades)
    return build_result(
        "convergence-storage-tco",
        target="model",
        kind="measurement",
        produced_by={
            "model": "storage_cluster",
            "scenario": "reference",
            "seed": load_scenario(REFERENCE).seed,
            "method": f"resampled {REPLICATES} times at each sample count, each replicate's seed "
            f"derived from the scenario's as seed + count * 977 + replicate",
            "stack": "sizing.mc",
            "output": "tco",
        },
        summary={
            "convergence": points,
            "ratios_per_decade": ratios,
            "mean_ratio": float(np.mean(ratios)),
            # The headline. Far steadier than any single ratio, because the noise in a spread
            # estimated from a finite number of replicates partly cancels across the range.
            "overall_ratio_per_decade": overall,
            "law_measured_from": LAW_FROM,
            "root_ten": math.sqrt(10.0),
        },
        units={
            "convergence": "USD",
            "convergence[0].samples": "dimensionless",
            "convergence[0].replicates": "dimensionless",
            "ratios_per_decade": "dimensionless",
            "mean_ratio": "dimensionless",
            "overall_ratio_per_decade": "dimensionless",
            "law_measured_from": "dimensionless",
            "root_ten": "dimensionless",
        },
        conditions={
            "what_this_measures": "sampling noise, and nothing else. An interval that has stopped "
            "moving is an interval whose *arithmetic* has settled; whether the model is right is "
            "a different question and Monte Carlo cannot answer it (ch13, ch18)",
            "the_interval_does_not_shrink": "the half_width column settles rather than falling. "
            "More samples locate the interval more precisely; they do not narrow the uncertainty "
            "the model describes",
            "individual_ratios_are_noisy": "each spread is estimated from a finite number of "
            "replicates and carries noise of its own, so read the overall rate rather than any "
            "single row. Estimating how uncertain something is, is itself an uncertain "
            "measurement",
        },
        code_sources=SOURCES,
        write=write,
    )


def correlation_effect(write: bool = True) -> dict:
    """What declaring that two inputs move together is worth, per model and per output."""
    from dataclasses import replace

    rows = []
    for path, outputs in (
        (STORAGE, ("tco", "nodes_recommended")),
        ("models/observability/model.yaml", ("known_ingest", "query_utilisation")),
    ):
        model = load_model(path)
        scenario = scenarios_for(model)[0]
        for name in scenarios_for(model):
            if name.name == "reference":
                scenario = name
        independent = replace(model, correlations=())
        with_correlations = evaluate(model, scenario)
        without = evaluate(independent, scenario)
        for output in outputs:
            declared = mc.half_width(with_correlations.samples[output])
            assumed = mc.half_width(without.samples[output])
            rows.append(
                {
                    "model": model.name,
                    "output": output,
                    "declared": declared,
                    "independent": assumed,
                    "change": declared / assumed - 1.0,
                }
            )
    return build_result(
        "correlation-effect",
        target="model",
        kind="measurement",
        produced_by={
            "model": "storage_cluster and observability",
            "scenario": "reference",
            "seed": load_scenario(REFERENCE).seed,
            "method": "sampled with and without each model's declared correlations",
            "stack": "sizing.mc — Iman-Conover rank correlation",
        },
        summary={"rows": rows},
        units={"rows": "dimensionless"},
        conditions={
            "what_widening_means": "assuming independence is not neutral. It is a claim, and "
            "where it is wrong it makes the interval narrower than the evidence supports — "
            "which is the direction that gets a plan approved",
        },
        code_sources=SOURCES,
        write=write,
    )


RUNNERS = {"convergence-storage-tco": convergence, "correlation-effect": correlation_effect}


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
            print(f"  MOVED: {name} no longer matches what the sampler produces")
            for line in moved[:6]:
                print(f"    {line}")
            failures.append(name)
        else:
            print(f"  ok: {name}")
    if failures:
        print("\nrun_uncertainty: FAILED — re-run and read what moved before committing.")
        return 1
    print(f"\nrun_uncertainty: OK ({len(RUNNERS)} experiment(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
