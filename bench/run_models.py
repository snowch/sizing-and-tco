"""Evaluate every model and stamp what it said.

    python3 -m bench.run_models            # evaluate, sample, and write bench/results/*.json
    python3 -m bench.run_models --check    # re-run and fail if any published figure moved

This is where the book's third kind of number comes from. A ``corpus`` result is what a codec did;
a ``rig`` result is what a machine did; a ``model`` result is what a model file *says*, worked out
by the code in :mod:`sizing`. All three are held to the same bargain: stamped, fingerprinted, and
re-derived by CI, so that a figure in a chapter cannot go on saying something the repository no
longer computes.

The fingerprint of a model result covers the whole DSL core — the sampler, the evaluator, the unit
registry — so editing how this book draws random numbers invalidates every interval it has
published. That is intended. An interval is a claim about a method as much as about a model, and
changing the method without re-stamping the claim is the failure the whole scheme exists to stop.

One stamped file per model and scenario, and both the chapter's figures and the interactive page
are built from it. That is deliberate: a book and a web page that computed their numbers
separately would eventually disagree, and the reader would have no way to tell which was wrong.
"""

from __future__ import annotations

import argparse
import sys

from bench.stages import stages as storage_stages
from bench.stamp import RERUN_TOLERANCE, build_result, load_result, result_exists
from sizing import export
from sizing.dsl import ROOT, discover, load_model, scenarios_for

#: Everything in a model result's fingerprint beyond the DSL core that KIND_SOURCES already
#: covers. The model file and its scenario are added per result, below.
SOURCES = ["bench/run_models.py", "sizing/export.py", "sizing/graph.py", "sizing/expr.py"]

#: Figures the ``--check`` pass compares, per output node. Not everything in the payload: a
#: histogram bin count can move by one draw between numpy versions without the book being wrong
#: about anything, and a check that fails on that is a check people learn to re-stamp past.
CHECKED = ("point", "p5", "p50", "p95")


def run_one(model, scenario, write: bool = True) -> dict:
    payload = export.export_payload(model, scenario)
    relative = str(model.path.relative_to(ROOT))  # type: ignore[union-attr]
    return build_result(
        f"{model.name}-{scenario.name}",
        target="model",
        kind="model",
        produced_by={
            "model": model.name,
            "model_file": relative,
            "scenario": scenario.name,
            "seed": scenario.seed,
            "samples": scenario.samples,
            "classification": model.classification,
            "sampler": "sizing.mc — inverse transform, Iman-Conover rank correlation",
            "unmeasured": list(model.unmeasured),
        },
        summary=payload,
        units={name: node["unit"] for name, node in payload["nodes"].items()},
        conditions={
            "what_an_interval_here_is": "a statement about this model's declared inputs, and "
            "nothing about whether the model has the right structure (ch13, ch18)",
            "unmeasured": "figures downstream of a constant nobody has measured are absent "
            "rather than estimated",
        },
        code_sources=[
            *SOURCES,
            relative,
            str(scenario.path.relative_to(ROOT)),
        ],  # type: ignore[union-attr]
        write=write,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-run and fail if a figure moved")
    parser.add_argument("--model", help="just this one")
    args = parser.parse_args()

    failures: list[str] = []
    count = 0
    for model in everything():
        if args.model and model.name != args.model:
            continue
        for scenario in scenarios_for(model):
            name = f"{model.name}-{scenario.name}"
            count += 1
            if not args.check:
                run_one(model, scenario)
                continue
            if not result_exists(name):
                print(f"  MISSING: bench/results/{name}.json — run `make models`")
                failures.append(name)
                continue
            committed = load_result(name)["summary"]
            fresh = run_one(model, scenario, write=False)["summary"]
            moved = compare(committed, fresh, model.outputs)
            if moved:
                failures += [f"{name}: {line}" for line in moved]
                for line in moved:
                    print(f"  MOVED: {name}: {line}")
            else:
                print(f"  ok: {name} ({len(fresh['nodes'])} nodes)")

    if failures:
        print(
            "\nrun_models: FAILED — a published figure no longer matches what the model computes.\n"
            "Either a model file, a measured constant or the DSL core changed. Read what moved, "
            "then `python3 -m bench.run_models` and commit the new stamps."
        )
        return 1
    print(f"\nrun_models: OK ({count} model run(s))")
    return 0


def everything():
    """Every model the book publishes a figure from, the staged ones included.

    ``discover()`` globs ``models/*/model.yaml`` and so cannot see the staged storage models,
    which are built under ``models/_out``. They are models all the same: the book quotes what
    each one computes in the chapter that finishes building it, and a figure with no stamped
    result behind it is the thing invariant 1 exists to refuse.
    """
    yield from discover()
    for stage in storage_stages():
        # The last stage is the finished model, which discover() has already yielded.
        if not stage.is_the_finished_model and stage.path.exists():
            yield load_model(stage.path)


def compare(committed: dict, fresh: dict, outputs) -> list[str]:
    """Which published figures moved, to the precision the book reports them at."""
    moved = []
    for name in outputs:
        was, now = committed["nodes"].get(name, {}), fresh["nodes"].get(name, {})
        for figure in CHECKED:
            old = was.get(figure, (was.get("summary") or {}).get(figure))
            new = now.get(figure, (now.get("summary") or {}).get(figure))
            if old is None and new is None:
                continue
            if old is None or new is None or abs(old - new) > RERUN_TOLERANCE * max(1.0, abs(old)):
                moved.append(f"{name}.{figure}: {old!r} -> {new!r}")
    return moved


if __name__ == "__main__":
    sys.exit(main())
