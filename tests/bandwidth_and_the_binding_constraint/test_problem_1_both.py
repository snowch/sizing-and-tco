"""Problem 9.1 - graded against the model, which reaches the same answer through its own node."""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.bandwidth_and_the_binding_constraint.stubs import size_for_both


@pytest.fixture(scope="module")
def evaluated():
    return evaluate(
        load_model("models/storage_cluster/model.yaml"),
        load_scenario("models/storage_cluster/scenarios/reference.yaml"),
    )


@pytest.mark.problem
def test_it_agrees_with_the_model_everywhere(evaluated):
    mine = size_for_both(
        evaluated.samples["nodes_for_capacity"], evaluated.samples["nodes_for_throughput"]
    )
    assert np.allclose(mine, evaluated.samples["nodes_recommended"]), (
        "the model reaches this through its own node and the two must agree on every sample"
    )


@pytest.mark.problem
def test_it_satisfies_both_chains_in_every_sample(evaluated):
    capacity = evaluated.samples["nodes_for_capacity"]
    throughput = evaluated.samples["nodes_for_throughput"]
    mine = np.asarray(size_for_both(capacity, throughput), dtype=float)
    assert np.all(mine >= capacity) and np.all(mine >= throughput), (
        "a cluster that satisfies one chain and not the other satisfies nothing. An average of "
        "the two is the commonest wrong answer here and it fails this test in both directions."
    )


@pytest.mark.problem
def test_it_buys_nothing_more_than_it_has_to(evaluated):
    capacity = evaluated.samples["nodes_for_capacity"]
    throughput = evaluated.samples["nodes_for_throughput"]
    mine = np.asarray(size_for_both(capacity, throughput), dtype=float)
    assert np.all(mine <= np.maximum(capacity, throughput)), (
        "you have bought more than either asked"
    )


def test_both_chains_win_sometimes(evaluated):
    """Scaffolding: the problem has two sides.

    If one chain always won, this chapter would be about one chain and the problem would be
    trivial. CI keeps checking that the model still puts both in play.
    """
    capacity = evaluated.samples["nodes_for_capacity"]
    throughput = evaluated.samples["nodes_for_throughput"]
    share = float(np.mean(throughput > capacity))
    assert 0.02 < share < 0.98, f"bandwidth decides only {share:.1%} of the time"
