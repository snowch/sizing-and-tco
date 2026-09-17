"""Problem 9.2 - the shortfall conditional on the neglected chain binding.

Graded against the published sweep and against the samples, both computed at test time.
"""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.bandwidth_and_the_binding_constraint.stubs import cost_of_ignoring_a_chain


@pytest.fixture(scope="module")
def chains():
    evaluation = evaluate(
        load_model("models/storage_cluster/model.yaml"),
        load_scenario("models/storage_cluster/scenarios/reference.yaml"),
    )
    return evaluation.samples["nodes_for_capacity"], evaluation.samples["nodes_for_throughput"]


@pytest.mark.problem
def test_the_share_matches_the_published_sweep(chains):
    share, _ = cost_of_ignoring_a_chain(*chains)
    published = load_result("binding-constraint")["summary"]["throughput_binds"]
    assert share == pytest.approx(published, abs=0.005), (
        f"the book publishes {published:.1%} of samples in which bandwidth decides, and you make "
        f"it {share:.1%}"
    )


@pytest.mark.problem
def test_the_shortfall_is_conditional(chains):
    capacity, throughput = chains
    _, shortfall = cost_of_ignoring_a_chain(capacity, throughput)
    binding = throughput > capacity
    expected = float(np.median((throughput - capacity)[binding]))
    assert shortfall == pytest.approx(expected, rel=1e-9), (
        "the median shortfall is over the samples where the neglected chain actually binds, not "
        "over all of them. Averaging in the zeroes is how a constraint that binds rarely comes to "
        "look harmless."
    )


@pytest.mark.problem
def test_the_conditional_shortfall_is_not_small(chains):
    """The point of the problem."""
    _, shortfall = cost_of_ignoring_a_chain(*chains)
    capacity, _ = chains
    assert shortfall > 0.05 * float(np.median(capacity)), (
        f"a shortfall of {shortfall:.0f} machines is not a rounding error against a cluster of "
        f"{np.median(capacity):.0f}. Where the neglected chain wins, it wins by a lot."
    )


def test_averaging_in_the_zeroes_would_look_harmless(chains):
    """Scaffolding: the distinction the problem turns on is a real one in this model."""
    capacity, throughput = chains
    gap = np.maximum(throughput - capacity, 0)
    unconditional = float(np.mean(gap))
    conditional = float(np.median(gap[gap > 0]))
    assert conditional > 3 * unconditional, (
        f"unconditional {unconditional:.1f} against conditional {conditional:.1f} - if these were "
        "close, the problem would not be teaching anything"
    )
