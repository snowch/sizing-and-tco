"""Problem 10.2 - the shortfall from sizing on the chain that usually wins.

Graded against the published sweep and against the model's futures, both computed at test time.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from bench.stamp import load_result
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.bandwidth_and_the_binding_constraint.stubs import cost_of_sizing_on_one

#: Each chain, by the name the published sweep uses for it. Which one wins most often comes from
#: the sweep rather than from this file, so the problem follows the model if the model changes.
CHAINS = {
    "requests": "hosts_for_requests",
    "memory": "hosts_for_memory",
    "storage": "hosts_for_storage",
}


@pytest.fixture(scope="module")
def published():
    return load_result("binding-constraint")["summary"]


@pytest.fixture(scope="module")
def usual_winner(published):
    return max(CHAINS, key=lambda name: published[f"{name}_binds"])


@pytest.fixture(scope="module")
def chains(usual_winner):
    samples = evaluate(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    ).samples
    chosen = samples[CHAINS[usual_winner]]
    others = tuple(samples[node] for name, node in CHAINS.items() if name != usual_winner)
    return chosen, others


@pytest.mark.problem
def test_the_share_matches_the_published_sweep(chains, published, usual_winner):
    share, _ = cost_of_sizing_on_one(*chains)
    # Compared outside the assert, so that a failure shows the reader's figure and not the book's.
    right = math.isclose(float(share), published[f"short_if_{usual_winner}"], abs_tol=0.005)
    assert right, (
        f"you make the share of futures in which a fleet sized on the {usual_winner} chain alone "
        f"is too small {float(share):.1%}, and the book's sweep disagrees. Check two things. The "
        "share is a fraction between 0 and 1, not a percentage. And a future where another chain "
        "asks for the same count as the chosen one is a tie, not a shortfall: count only the "
        "futures where some other chain asks for strictly more."
    )


@pytest.mark.problem
def test_the_shortfall_is_conditional(chains):
    chosen, others = chains
    _, shortfall = cost_of_sizing_on_one(chosen, others)
    largest_other = np.max(np.stack(others), axis=0)
    short = largest_other > chosen
    # Compared outside the assert, so that a failure shows the reader's figure and not the book's.
    right = math.isclose(
        float(shortfall), float(np.median((largest_other - chosen)[short])), rel_tol=1e-9
    )
    assert right, (
        f"a median shortfall of {float(shortfall):g} hosts is not the one asked for. Take the "
        "median over the futures where the fleet comes up short, and only those: the futures "
        "where some other chain asks for strictly more than the chosen one. A tie is not short, "
        "and nor is a future the chosen chain won. Each of those adds a zero, and zeros pull the "
        "median down. If your figure matches the chapter's median shortfall across all futures, "
        "you counted every future."
    )


@pytest.mark.problem
def test_the_usual_winner_still_loses_more_often_than_not(chains):
    """The point of the problem."""
    share, _ = cost_of_sizing_on_one(*chains)
    assert share > 0.5, (
        f"sized on the chain that wins most often, the fleet is too small in {share:.0%} of "
        "futures. Winning a three-way race most often is not the same as winning it usually."
    )


@pytest.mark.problem
def test_the_conditional_shortfall_is_not_small(chains):
    chosen, others = chains
    _, shortfall = cost_of_sizing_on_one(chosen, others)
    assert shortfall > 0.05 * float(np.median(chosen)), (
        f"a shortfall of {shortfall:.0f} hosts is not a rounding error against a fleet of "
        f"{np.median(chosen):.0f}. Where a neglected chain wins, it wins by a lot."
    )


def test_no_chain_is_safe_to_size_on(published):
    """Scaffolding: the distinction the problem turns on is a real one in this model.

    Every chain wins sometimes, and sizing on any one of them alone leaves the fleet short in
    more futures than not. If a chain ever came to win nearly always, the chapter would be about
    that chain and this problem would need rewriting.
    """
    for name in CHAINS:
        assert published[f"short_if_{name}"] > 0.5, f"sizing on {name} alone is nearly safe"
