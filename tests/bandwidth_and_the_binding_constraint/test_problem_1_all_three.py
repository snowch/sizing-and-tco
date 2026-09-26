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


def one_count_per_future(chains) -> np.ndarray:
    """The reader's answer, refused with its own message if it is not one count per future.

    One number for the whole array fails the other tests too, and their messages describe a
    different mistake: the largest count any future asked for is "more than any chain asked" in
    nearly every future.
    """
    mine = np.asarray(size_for_all(*chains), dtype=float)
    assert mine.shape == np.shape(chains[0]), (
        "size_for_all has to return one host count for every future: an array as long as each "
        f"chain, and yours has shape {mine.shape}. If you took the largest, take it across the "
        "three chains within each future, not across every count in all three arrays."
    )
    return mine


@pytest.mark.problem
def test_it_agrees_with_the_model_everywhere(evaluated, chains):
    mine = one_count_per_future(chains)
    assert np.allclose(mine, evaluated.samples["hosts_recommended"]), (
        "the model reaches this through its own node, and the two must agree in every future"
    )


@pytest.mark.problem
def test_it_satisfies_every_chain_in_every_future(chains):
    mine = one_count_per_future(chains)
    for chain in chains:
        assert np.all(mine >= chain), (
            "in some futures your fleet is smaller than one of the chains asks for, and a fleet "
            "that satisfies two chains and not the third is too small for the third. An average "
            "of the three does this whenever the three differ: it falls short of the largest."
        )


@pytest.mark.problem
def test_it_buys_nothing_more_than_it_has_to(chains):
    mine = one_count_per_future(chains)
    assert np.all(mine <= np.max(np.stack(chains), axis=0)), (
        "in some futures you have bought more than any chain asked for"
    )


def test_the_chains_are_one_count_per_future(chains):
    """Scaffolding: the shape check in the problem tests means something.

    Three arrays of the same length, one host count per future, with more than one future in
    them. A single number for the whole set can then be told apart from an answer.
    """
    shapes = {np.shape(chain) for chain in chains}
    assert len(shapes) == 1, f"the three chains have different shapes: {shapes}"
    (shape,) = shapes
    assert len(shape) == 1 and shape[0] > 1, (
        f"each chain should be one count per future, not an array of shape {shape}"
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
