"""The post-mortem the model can do on itself, and the one it cannot.

    python3 -m bench.run_postmortem            # run it and write the result
    python3 -m bench.run_postmortem --check    # re-run and fail if a published figure moved

ch12 bought a fleet and ch13 reported how often it goes over the queueing knee at the busy hour,
across the futures the model thinks are plausible. This runner asks the question somebody asks
three years later, when one of those futures has happened:

    **what went wrong, and could the model have told us?**

The answer to the second half is yes, and it is uncomfortable: the model did tell you, as a
percentage, in a column nobody read out loud. So the interesting work is the first half —
attributing the miss — and it can be done without a single new measurement.

## Conditioning, rather than hindsight

The sampled model already contains the futures where the design failed. They are the draws where
the queueing ceiling came out over its limit. So the post-mortem is a filter: take those draws,
look at what each input had been doing in them, and compare that against what it does across all
the futures.

An input that is no different in the failures than it is everywhere else did not cause them. An
input whose typical value in the failures is well away from its typical value overall is the one
that did. That comparison is the whole method, and it needs no observation from outside — which
is exactly why it is also **limited in a way worth being explicit about**, and why the second half
of this runner exists.

## What conditioning cannot find

A cause that is not in the model cannot appear in this table, because the samples never contained
it. Worse than absent: the attribution will hand the blame to whichever declared input happens to
correlate with failure, and it will do so with a straight face.

So the runner also does the experiment on a model that is *known* to be missing a term — the
observability model's ingest total, which excludes traces because nobody has measured spans per
request (ch20) — and records that the attribution confidently blames the inputs that are present.
That is the honest bottom of the technique, and a post-mortem that does not know about it is a
procedure for generating a culprit.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from bench.stamp import build_result, load_result, numeric_differences, result_exists
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate, sampled_inputs

SOURCES = ["bench/run_postmortem.py"]

WEB_SERVICE = "models/web_service/model.yaml"
REFERENCE = "models/web_service/scenarios/reference.yaml"
OBSERVABILITY = "models/observability/model.yaml"
OBSERVABILITY_REFERENCE = "models/observability/scenarios/reference.yaml"

#: The failure a post-mortem is about: the fleet was asked to serve more than it could at the
#: busy hour, and the queue did what queues do.
FAILED = "queueing_headroom"


def attribute(model_path: str, scenario_path: str, ceiling: str) -> dict:
    """Where each uncertain input sat, in the futures where one ceiling was breached.

    The comparison is between medians rather than means, for the reason every other summary in
    this book uses a median: these inputs are skewed, and a mean would report a shift that is
    mostly the tail moving.
    """
    model, scenario = load_model(model_path), load_scenario(scenario_path)
    result = evaluate(model, scenario)
    breached = np.asarray(result.samples[ceiling], dtype=float) > 1.0
    share = float(breached.mean())
    rows = []
    used: dict[str, np.ndarray] = {}
    for name in sampled_inputs(model):
        drawn = result.samples.get(name)
        if drawn is None or name not in model.ancestors(ceiling):
            continue
        drawn = np.asarray(drawn, dtype=float)
        used[name] = drawn
        overall = float(np.median(drawn))
        in_failures = float(np.median(drawn[breached]))
        rows.append(
            {
                "input": name,
                "label": model.nodes[name].display,
                "overall": overall,
                "in_failures": in_failures,
                # How far this input had to be from its usual self for the design to fail. One
                # near zero is an input that was a bystander.
                "shift": in_failures / overall - 1.0 if overall else 0.0,
                # And how often it was extreme rather than merely high: the share of failures in
                # which this input was above its own p90. A cause that is only ever slightly
                # above average is a cause nobody could have acted on.
                "extreme_in_failures": float(
                    (drawn[breached] > np.percentile(drawn, 90)).mean() if share else 0.0
                ),
            }
        )
    rows.sort(key=lambda row: -abs(row["shift"]))
    # The story told afterwards is always about one dramatic thing. This is how often there was
    # one: the share of failures in which *some* input was beyond its own p90. Its complement is
    # the share for which the honest account is "nothing unusual happened, and the design could
    # not absorb that" — which is a statement about the margin rather than about the world.
    extreme = np.zeros_like(breached)
    for drawn in used.values():
        extreme |= drawn > np.percentile(drawn, 90)
    return {
        "model": model.name,
        "ceiling": ceiling,
        "share_of_futures": share,
        "rows": rows,
        "something_extreme_share": float(extreme[breached].mean()) if share else 0.0,
        "nothing_extreme_share": float((~extreme[breached]).mean()) if share else 0.0,
        # And the figure that stops the one above being read as a finding. With enough inputs,
        # *something* is beyond its own p90 in most futures whether or not anything failed. A
        # post-mortem statistic that is not compared against its own base rate is a statistic
        # about how many inputs the model has.
        "something_extreme_everywhere": float(extreme.mean()),
        "inputs": len(used),
    }


def postmortem(write: bool = True) -> dict:
    """The attribution on a model that is complete, and on one that is known to be missing a term."""
    complete = attribute(WEB_SERVICE, REFERENCE, FAILED)
    # The same method on a model with a hole in it. `known_ingest` excludes traces entirely,
    # because spans per request has never been measured — so every figure this attribution
    # produces is about the two chains that are present, and it will never mention the third.
    incomplete = attribute(OBSERVABILITY, OBSERVABILITY_REFERENCE, "quoted_pipeline_utilisation")
    model = load_model(OBSERVABILITY)
    missing = sorted(model.blocked())
    return build_result(
        "postmortem",
        target="model",
        kind="measurement",
        produced_by={
            "method": "the sampled futures filtered to the ones where a ceiling was breached, "
            "and each input's median in them compared against its median overall",
            "model": "web_service and observability",
            "scenario": "reference",
            "seed": load_scenario(REFERENCE).seed,
            "stack": "sizing.evaluate",
        },
        summary={
            "complete": complete,
            "incomplete": incomplete,
            # What the attribution on the second model cannot see, named here so that the figure
            # and its limitation are stamped in the same file.
            "not_in_the_model": missing,
            "blocked_nodes": len(missing),
        },
        units={
            "complete": "dimensionless",
            "complete.share_of_futures": "dimensionless",
            "complete.nothing_extreme_share": "dimensionless",
            "complete.something_extreme_everywhere": "dimensionless",
            "complete.inputs": "dimensionless",
            "incomplete": "dimensionless",
            "blocked_nodes": "dimensionless",
        },
        conditions={
            "no_observation_was_used": "nothing here is a measurement of a real outcome. It is "
            "the model's own futures, filtered to the ones in which the design failed — which is "
            "what makes it reproducible and also what bounds what it can say",
            "it_cannot_find_a_missing_cause": "the second attribution is run on a model known to "
            "exclude an entire chain, and it blames the inputs that are present without "
            "hesitating. A post-mortem inside a model is a post-mortem of that model (ch20)",
            "medians_not_means": "these inputs are skewed, and a shift in means would mostly be "
            "the tail moving rather than the typical case",
            "read_the_base_rate": "`something_extreme_share` must be read against "
            "`something_extreme_everywhere`. Even with three uncertain inputs feeding a ceiling, "
            "one of them is beyond its own p90 in a fair share of all futures, failure or not, "
            "and the share rises with every input added. A post-mortem that does not say so has "
            "discovered the number of inputs",
        },
        code_sources=SOURCES,
        write=write,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-run and diff against the stamp")
    arguments = parser.parse_args(argv)

    fresh = postmortem(write=not arguments.check)
    if not arguments.check:
        print("  wrote bench/results/postmortem.json")
        print("\nrun_postmortem: OK")
        return 0

    if not result_exists("postmortem"):
        print("postmortem has never been run", file=sys.stderr)
        return 1
    differences = numeric_differences(load_result("postmortem")["summary"], fresh["summary"])
    if differences:
        print("postmortem moved:", file=sys.stderr)
        for line in differences:
            print(f"  {line}", file=sys.stderr)
        return 1
    print("  ok: postmortem")
    print("\nrun_postmortem: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
