"""Problem 10.1 - what a node loss costs, and why cluster size changes the answer."""

from __future__ import annotations

import pytest

from tests.headroom_and_failure_domains.stubs import rebuild_reserve

CASES = [(5, 1), (12, 1), (50, 1), (121, 1), (12, 2), (50, 3), (500, 2)]


def expected(nodes: int, losses: int) -> float:
    """The lost fraction, from the definition. Derived, never stored."""
    return losses / nodes


@pytest.mark.problem
@pytest.mark.parametrize(("nodes", "losses"), CASES)
def test_it_is_the_share_that_goes_away(nodes, losses):
    assert rebuild_reserve(nodes, losses) == pytest.approx(expected(nodes, losses), rel=1e-9)


@pytest.mark.problem
def test_a_small_cluster_pays_a_large_margin():
    """The argument for large failure domains that nobody makes."""
    small = rebuild_reserve(5, 1)
    large = rebuild_reserve(500, 1)
    assert small > 20 * large, (
        f"one machine in five costs {small:.0%} of the cluster and one in five hundred costs "
        f"{large:.1%}. Per machine, a small cluster is enormously more expensive to make "
        "survivable - which is a capacity argument for consolidation and is not the argument "
        "people usually give."
    )


@pytest.mark.problem
def test_tolerating_more_losses_costs_proportionally_more():
    assert rebuild_reserve(50, 3) == pytest.approx(3 * rebuild_reserve(50, 1))


@pytest.mark.problem
def test_losing_everything_leaves_nothing():
    assert rebuild_reserve(4, 4) == pytest.approx(1.0)


def test_the_models_own_margin_is_in_the_plausible_range():
    """Scaffolding: the book's declared headroom is not absurd against this arithmetic.

    The storage model keeps a margin for rebuild *and* for allocator behaviour near full, so it
    should be comfortably above what rebuild alone demands at that cluster size — and nowhere near
    a whole cluster.
    """
    from sizing.dsl import load_model, load_scenario
    from sizing.evaluate import point

    values = point(
        load_model("models/storage_cluster/model.yaml"),
        load_scenario("models/storage_cluster/scenarios/reference.yaml"),
    )
    nodes = int(values["nodes_purchased"])
    declared = values["capacity_headroom"]
    assert expected(nodes, 1) < declared < 0.6, (
        f"the model declares {declared:.0%} and one node of {nodes} is {expected(nodes, 1):.1%}"
    )
