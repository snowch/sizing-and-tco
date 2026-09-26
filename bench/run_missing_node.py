"""The model file problem 20.3 hands the reader, run once, beside the invoice it cannot reach.

    python3 -m bench.run_missing_node            # run it and write the result
    python3 -m bench.run_missing_node --check    # re-run and fail if a published figure moved

ch20 argues that a model missing a cost line reports a confident interval and gives no sign of
what it lacks. The argument needs a case the reader can see, and the book has one: the exercise
fixture under `tests/the_missing_node/`, which is missing exactly one line and has no node to mark
the gap. This stamps what that file says, so the page can show it rather than assert it.

The invoice average is invented for the exercise, and it lives in the problem's test, which is
the file that grades against it. It is read from there rather than restated here, so the page and
the test cannot disagree, and it is copied into the stamp with a condition that says what it is.

The test file is not in the fingerprint. Its docstrings and failure messages are edited for
reasons that change no figure, and each edit would otherwise stale the stamp. The invoice is a
figure in the summary instead, and ``--check``, which CI runs on every push, compares it.
"""

from __future__ import annotations

import argparse
import ast
import sys

import numpy as np

from bench.stamp import (
    KIND_SOURCES,
    ROOT,
    build_result,
    load_result,
    numeric_differences,
    result_exists,
)
from sizing import mc
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate

NAME = "the-missing-node-fixture"
FIXTURE = "tests/the_missing_node/fixtures/model.yaml"
SCENARIO = "tests/the_missing_node/fixtures/scenarios/reference.yaml"
TEST = "tests/the_missing_node/test_problem_3_missing_node.py"
OUTPUT = "monthly_cost"
#: This runner, the fixture and its scenario, and the DSL core, so the stamp moves when the
#: method does. `kind` is "measurement", which does not bring the core in on its own, so it is
#: named here. The test the invoice is read from is left out: see the module docstring.
SOURCES = ["bench/run_missing_node.py", FIXTURE, SCENARIO, *KIND_SOURCES["model"]]


def invoice_average() -> float:
    """``OBSERVED_MONTHLY`` from the problem's test, read as source rather than imported.

    Importing the test would import pytest, and the build has no business needing it.
    """
    tree = ast.parse((ROOT / TEST).read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "OBSERVED_MONTHLY" for t in node.targets
        ):
            return float(ast.literal_eval(node.value))
    raise KeyError(f"{TEST} has no module-level OBSERVED_MONTHLY")


def run(write: bool = True) -> dict:
    model, scenario = load_model(ROOT / FIXTURE), load_scenario(ROOT / SCENARIO)
    result = evaluate(model, scenario)
    drawn = np.asarray(result.samples[OUTPUT], dtype=float)
    low, high = mc.interval(drawn)
    invoice = invoice_average()
    return build_result(
        NAME,
        target="model",
        kind="measurement",
        produced_by={
            "model": model.name,
            "model_file": FIXTURE,
            "scenario": scenario.name,
            "seed": scenario.seed,
            "samples": scenario.samples,
            "classification": model.classification,
            "invoice_from": f"{TEST}::OBSERVED_MONTHLY",
        },
        summary={
            "classification": model.classification,
            "output": OUTPUT,
            "point": float(result.point[OUTPUT]),
            "p5": low,
            "p50": float(np.median(drawn)),
            "p95": high,
            "invoice_average": invoice,
            "share_at_or_above_invoice": float(np.mean(drawn >= invoice)),
        },
        units={
            "point": "USD/month",
            "p5": "USD/month",
            "p50": "USD/month",
            "p95": "USD/month",
            "invoice_average": "USD/month",
            "share_at_or_above_invoice": "dimensionless",
        },
        conditions={
            "everything_here_is_invented": "the fixture is an exercise, not one of the book's models, and "
            "every input in it is an assumption made up for problem 20.3",
            "the_invoice_is_invented_too": "the average of twelve invoices that do not exist, kept in the "
            "problem's test so it is never mistaken for an observation of anything",
            "what_an_interval_here_is": "a statement about this file's declared inputs, and nothing about "
            "whether the file has every cost line (ch20)",
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
        print("\nrun_missing_node: OK")
        return 0
    if not result_exists(NAME):
        print(f"{NAME} has never been run: `python3 -m bench.run_missing_node`", file=sys.stderr)
        return 1
    # Summaries only: the stamp carries a timestamp, and a re-run always has a newer one.
    differences = numeric_differences(load_result(NAME)["summary"], fresh["summary"])
    if differences:
        print(f"{NAME} moved:", file=sys.stderr)
        for line in differences:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(f"  ok: {NAME}")
    print("\nrun_missing_node: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
