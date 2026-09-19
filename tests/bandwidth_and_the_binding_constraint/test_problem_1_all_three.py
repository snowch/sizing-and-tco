"""Problem 10.1 - graded against the model, which reaches the same answer through its own node."""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.bandwidth_and_the_binding_constraint.stubs import size_for_all

CHAINS = ("hosts_for_requests", "hosts_for_memory", "hosts_for_storage")


@pytest.fixture(scope="module")
def evaluated():
    return evaluate(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )


@pytest.fixture(scope="module")
def chains(evaluated):
    return tuple(evaluated.samples[name] for name in CHAINS)


@pytest.mark.problem
def test_it_agrees_with_the_model_everywhere(evaluated, chains):
    mine = size_for_all(*chains)
    assert np.allclose(mine, evaluated.samples["hosts_recommended"]), (
        "the model reaches this through its own node and the two must agree on every sample"
    )


@pytest.mark.problem
def test_it_satisfies_every_chain_in_every_sample(chains):
    mine = np.asarray(size_for_all(*chains), dtype=float)
    for chain in chains:
        assert np.all(mine >= chain), (
            "a fleet that satisfies two chains and not the third satisfies nothing. An average "
            "of the three is the commonest wrong answer here and it fails this test in every "
            "direction at once."
        )


@pytest.mark.problem
def test_it_buys_nothing_more_than_it_has_to(chains):
    mine = np.asarray(size_for_all(*chains), dtype=float)
    assert np.all(mine <= np.max(np.stack(chains), axis=0)), (
        "you have bought more than any chain asked"
    )


def test_every_chain_wins_sometimes(chains):
    """Scaffolding: the problem has three sides.

    If one chain always won, this chapter would be about one chain and the problem would be
    trivial. CI keeps checking that the model still puts all three in play.
    """
    stacked = np.stack(chains)
    for index, name in enumerate(CHAINS):
        others = np.delete(stacked, index, axis=0).max(axis=0)
        share = float(np.mean(stacked[index] > others))
        assert 0.02 < share < 0.98, f"{name} decides only {share:.1%} of the time"
