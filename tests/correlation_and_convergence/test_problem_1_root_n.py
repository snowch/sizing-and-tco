"""Problem 14.1 — show the square-root law.

The target is the law itself, not a stored number: the test asks whether the reader's measured
spread falls by a factor of root ten per decade, with a tolerance derived from how many
replicates they were told to run. The test supplies the run, one evaluation of the web service
model at a count and a seed; the reader supplies the seeds, the percentile of each run and the
spread between them.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.correlation_and_convergence.stubs import spread_at

COUNTS = (1_000, 10_000, 100_000)
OUTPUT = "tco"
#: Thirty-two runs at each count, as the book's own experiment uses (bench/run_uncertainty.py):
#: a spread estimated from a dozen runs carries about twenty per cent noise of its own, enough to
#: fail a correct answer one time in ten.
REPLICATES = 32

#: The standard deviation of a sample standard deviation is itself about 1/sqrt(2(k-1)) of it, so
#: each measured spread carries roughly this much relative noise, and a *ratio* of two of them
#: carries root-two times as much. The tolerance is derived from that rather than guessed, and a
#: reader who wants a tighter one has to run more replicates — which is the chapter's own
#: argument, applied to the chapter's own experiment.
RELATIVE_NOISE = 1.0 / math.sqrt(2 * (REPLICATES - 1))
TOLERANCE = 3.0 * RELATIVE_NOISE * math.sqrt(2.0) * math.sqrt(10.0)


@pytest.fixture(scope="module")
def run():
    """One run of the web service model: ``run(samples, seed)`` is that many draws of the
    five-year total from that seed, the reference scenario otherwise as declared."""
    model = load_model("models/web_service/model.yaml")
    scenario = load_scenario("models/web_service/scenarios/reference.yaml")

    def one_run(samples: int, seed: int) -> np.ndarray:
        rerun = dataclasses.replace(scenario, samples=samples, seed=seed)
        return evaluate(model, rerun).samples[OUTPUT]

    return one_run


@pytest.mark.problem
def test_the_spread_falls_as_one_over_root_n(run):
    spreads = [spread_at(run, samples=count, replicates=REPLICATES) for count in COUNTS]
    assert all(s > 0 for s in spreads), (
        "a spread of zero means every replicate gave the same answer, which means the seeds were "
        "not different. Re-read what `replicates` is for."
    )
    for i in range(len(COUNTS) - 1):
        ratio = spreads[i] / spreads[i + 1]
        assert abs(ratio - math.sqrt(10.0)) < TOLERANCE, (
            f"going from {COUNTS[i]:,} to {COUNTS[i + 1]:,} samples changed the run-to-run spread "
            f"by {ratio:.2f}x; the law says about {math.sqrt(10.0):.2f}x. If your ratio is near "
            "1.0 you are probably measuring the interval width, which does not shrink — that is "
            "the whole point of the section."
        )


def test_the_tolerance_is_derived_and_not_absurd():
    """Scaffolding: the problem is passable and is not trivially passable."""
    assert 0.1 < TOLERANCE < math.sqrt(10.0), (
        f"a tolerance of {TOLERANCE:.3f} either cannot be met or cannot be failed"
    )


def test_the_run_is_one_run_and_the_seed_is_what_makes_two_differ(run):
    """Scaffolding: what the test hands the reader does what the stub says it does. The count
    sets how many draws come back, the same seed gives the same run, and a different seed is what
    makes a run different — so a loop over seeds is enough to answer the problem."""
    first = run(COUNTS[0], 1)
    assert len(first) == COUNTS[0], "the count is how many draws a run returns"
    assert np.array_equal(run(COUNTS[0], 1), first), "the same seed has to give the same run"
    assert not np.array_equal(run(COUNTS[0], 2), first), (
        "a different seed has to give a different run, or replicates would have nothing to spread"
    )
