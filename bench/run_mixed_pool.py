"""Two generations in one pool: what the old hosts change, and what keeping them costs.

    python3 -m bench.run_mixed_pool            # run it and write the result
    python3 -m bench.run_mixed_pool --check    # re-run and fail if a published figure moved

``models/mixed_pool/`` sizes a purchase when last generation's hosts are still in service. This
runner gathers what ch10, ch11 and ch22 print from it:

- **New hosts, chain by chain**, three ways at the point estimate: an all-new fleet (the
  ``replace`` scenario), the mixed pool with requests routed by capacity, and the mixed pool with
  requests routed equally. The chain that binds is different in each.
- **The ceilings** of the pool as bought, with the old hosts kept (``reference``) and after they
  retire before the horizon (``old_retired``): how often each is crossed.
- **Keep versus replace**, subtracted future by future. Both scenarios pin only decisions, so
  every input either samples is drawn once and reaches both, and the difference can be taken
  sample by sample (ch22). The runner checks the shared draws are identical first.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from bench.stamp import build_result, load_result, numeric_differences, result_exists
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate, point, sampled_inputs

SOURCES = ["bench/run_mixed_pool.py"]

NAME = "mixed-pool"
MODEL = "models/mixed_pool/model.yaml"
SCENARIOS = "models/mixed_pool/scenarios"

#: The chains, as the model names what each asks of the new hosts. The equal-routing column
#: differs from the capacity-weighted one only for requests: data is placed by capacity either way.
CHAINS = (
    ("Requests", "new_for_requests", "new_for_requests_equal"),
    ("Memory", "new_for_memory", "new_for_memory"),
    ("Disk", "new_for_storage", "new_for_storage"),
    ("New hosts to buy", "new_hosts_weighted", "new_hosts_equal"),
)

CEILINGS = (
    "queueing_headroom_weighted",
    "queueing_headroom_equal",
    "failure_headroom",
    "cache_fill",
    "disk_fill",
    "shard_fit",
)

TOTAL = "total_cost"

#: The lines of each total, as the model adds them: the purchase, then each running cost for the
#: length of the horizon.
LINES = (
    ("New hosts bought", "new_capex", False),
    ("Energy over the horizon", "annual_energy_cost", True),
    ("Licences over the horizon", "annual_licences", True),
    ("Support over the horizon", "annual_support", True),
)


def run(write: bool = True) -> dict:
    model = load_model(MODEL)
    keep = load_scenario(f"{SCENARIOS}/reference.yaml")
    replace = load_scenario(f"{SCENARIOS}/replace.yaml")
    retired = load_scenario(f"{SCENARIOS}/old_retired.yaml")
    equal = load_scenario(f"{SCENARIOS}/keep_routed_equally.yaml")

    at_keep, at_replace = point(model, keep), point(model, replace)
    chains = [
        {
            "label": label,
            "all_new": at_replace[weighted],
            "by_capacity": at_keep[weighted],
            "equally": at_keep[equal],
        }
        for label, weighted, equal in CHAINS
    ]

    # The equal-routing purchase is a scenario with a number in it, so it can go stale when the
    # model changes. It is checked against the node that decides it rather than trusted.
    at_equal = point(model, equal)
    if at_equal["new_hosts"] != at_keep["new_hosts_equal"]:
        raise ValueError(
            f"keep_routed_equally buys {at_equal['new_hosts']} new hosts; new_hosts_equal says "
            f"{at_keep['new_hosts_equal']}. Update the scenario."
        )

    kept, replaced, gone, kept_equal = (evaluate(model, s) for s in (keep, replace, retired, equal))
    ceilings = [
        {
            "node": name,
            "label": model.nodes[name].display,
            "kept": kept.ceilings[name]["p_over_allowed"],
            "retired": gone.ceilings[name]["p_over_allowed"],
            "all_new": replaced.ceilings[name]["p_over_allowed"],
            # What the plan itself says, before any future is drawn: ok, inside headroom, or over.
            "verdict_kept": kept.ceilings[name]["verdict"],
            "verdict_retired": gone.ceilings[name]["verdict"],
            "verdict_all_new": replaced.ceilings[name]["verdict"],
        }
        for name in CEILINGS
    ]

    shared = [n for n in sampled_inputs(model) if n in kept.samples and n in replaced.samples]
    for name in shared:
        if not np.array_equal(kept.samples[name], replaced.samples[name]):
            raise ValueError(f"{name} was drawn differently for keep and replace")
    difference = kept.samples[TOTAL] - replaced.samples[TOTAL]
    for name in shared:
        if not np.array_equal(kept_equal.samples[name], replaced.samples[name]):
            raise ValueError(f"{name} was drawn differently for keep_routed_equally and replace")
    difference_equal = kept_equal.samples[TOTAL] - replaced.samples[TOTAL]
    e5, e95 = np.percentile(difference_equal, [5, 95])
    p5, p50, p95 = np.percentile(difference, [5, 50, 95])
    keep_vs_replace = {
        "keep": {
            "point": at_keep[TOTAL],
            "p5": kept.summaries[TOTAL]["p5"],
            "p95": kept.summaries[TOTAL]["p95"],
        },
        "replace": {
            "point": at_replace[TOTAL],
            "p5": replaced.summaries[TOTAL]["p5"],
            "p95": replaced.summaries[TOTAL]["p95"],
        },
        "difference": {
            "point": at_keep[TOTAL] - at_replace[TOTAL],
            "p5": float(p5),
            "p50": float(p50),
            "p95": float(p95),
        },
        "share_keep_cheaper": float(np.mean(difference < 0)),
        # The same comparison with the router sending every host the same share, which is the
        # condition the verdict above rests on.
        "routed_equally": {
            "new_hosts": at_equal["new_hosts"],
            "point": at_equal[TOTAL] - at_replace[TOTAL],
            "p5": float(e5),
            "p95": float(e95),
            "share_keep_cheaper": float(np.mean(difference_equal < 0)),
        },
        # Which lines the difference is made of, at the point estimate: the purchase, and each
        # running cost over the horizon.
        "lines": [
            {
                "label": label,
                "keep": at_keep[node] * (at_keep["horizon"] if running else 1.0),
                "replace": at_replace[node] * (at_replace["horizon"] if running else 1.0),
            }
            for label, node, running in LINES
        ],
        "new_hosts": {"keep": at_keep["new_hosts"], "replace": at_replace["new_hosts"]},
        "shared_inputs": len(shared),
    }

    units = {
        "chains": "host",
        "ceilings": "dimensionless",
        "keep_vs_replace.keep": "USD",
        "keep_vs_replace.replace": "USD",
        "keep_vs_replace.difference": "USD",
        "keep_vs_replace.share_keep_cheaper": "dimensionless",
        "keep_vs_replace.new_hosts": "host",
        "keep_vs_replace.routed_equally.new_hosts": "host",
        "keep_vs_replace.routed_equally.point": "USD",
        "keep_vs_replace.routed_equally.p5": "USD",
        "keep_vs_replace.routed_equally.p95": "USD",
        "keep_vs_replace.routed_equally.share_keep_cheaper": "dimensionless",
        "keep_vs_replace.lines": "USD",
        "keep_vs_replace.shared_inputs": "dimensionless",
    }
    return build_result(
        NAME,
        target="model",
        kind="measurement",
        produced_by={
            "method": "new hosts per chain at the point estimate for three scenarios; ceilings "
            "from each scenario's own run; keep and replace evaluated on the same draws and "
            "subtracted sample by sample",
            "model": model.name,
            "scenario": f"{keep.name}, {replace.name}, {retired.name} and {equal.name}",
            "seed": keep.seed,
            "samples": keep.samples,
            "stack": "sizing.evaluate",
        },
        summary={"chains": chains, "ceilings": ceilings, "keep_vs_replace": keep_vs_replace},
        units=units,
        conditions={
            "demand_is_the_web_service's": "the mixed pool's demand is the web service's own "
            "chain, node for node, with its shapes, sources and correlation",
            "data_placed_by_capacity": "only the routing of requests differs between the two "
            "policies; data is placed by capacity in both",
            "shared_futures": "keep and replace pin only decisions, so every sampled input is "
            "drawn once and reaches both. The runner checks the shared columns are identical "
            "before subtracting",
            "old_purchase_is_sunk": "the old hosts' purchase is spent and appears in neither "
            "total; their energy, licences and support appear in keep's",
        },
        code_sources=SOURCES,
        write=write,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-run and diff against the stamp")
    arguments = parser.parse_args(argv)

    fresh = run(write=not arguments.check)
    if not arguments.check:
        print(f"  wrote bench/results/{NAME}.json")
        print("\nrun_mixed_pool: OK")
        return 0

    if not result_exists(NAME):
        print(f"{NAME} has never been run", file=sys.stderr)
        return 1
    differences = numeric_differences(load_result(NAME)["summary"], fresh["summary"])
    if differences:
        print(f"{NAME} moved:", file=sys.stderr)
        for line in differences:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(f"  ok: {NAME}")
    print("\nrun_mixed_pool: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
