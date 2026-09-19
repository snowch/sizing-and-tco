"""Problem 11.1 - what a host loss costs, and why fleet size changes the answer."""

from __future__ import annotations

import pytest

from tests.headroom_and_failure_domains.stubs import failure_reserve

CASES = [(5, 1), (12, 1), (50, 1), (121, 1), (12, 2), (50, 3), (500, 2)]


def expected(hosts: int, losses: int) -> float:
    """The lost fraction, from the definition. Derived, never stored."""
    return losses / hosts


@pytest.mark.problem
@pytest.mark.parametrize(("hosts", "losses"), CASES)
def test_it_is_the_share_that_goes_away(hosts, losses):
    assert failure_reserve(hosts, losses) == pytest.approx(expected(hosts, losses), rel=1e-9)


@pytest.mark.problem
def test_a_small_cluster_pays_a_large_margin():
    """The argument for large failure domains that nobody makes."""
    small = failure_reserve(5, 1)
    large = failure_reserve(500, 1)
    assert small > 20 * large, (
        f"one machine in five costs {small:.0%} of the fleet and one in five hundred costs "
        f"{large:.1%}. Per machine, a small fleet is enormously more expensive to make "
        "survivable - which is a capacity argument for consolidation and is not the argument "
        "people usually give."
    )


@pytest.mark.problem
def test_tolerating_more_losses_costs_proportionally_more():
    assert failure_reserve(50, 3) == pytest.approx(3 * failure_reserve(50, 1))


@pytest.mark.problem
def test_losing_everything_leaves_nothing():
    assert failure_reserve(4, 4) == pytest.approx(1.0)


def test_the_models_own_margin_is_in_the_plausible_range():
    """Scaffolding: the book's declared headroom is not absurd against this arithmetic.

    The web service keeps one margin for the queue *and* audits the one-host-down case against
    the same margin, so it should be comfortably above what one host's share of the fleet comes
    to — and nowhere near a whole fleet.
    """
    from sizing.dsl import load_model, load_scenario
    from sizing.evaluate import point

    values = point(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )
    hosts = int(values["hosts"])
    declared = values["queueing_margin"]
    assert expected(hosts, 1) < declared < 0.6, (
        f"the model declares {declared:.0%} and one host of {hosts} is {expected(hosts, 1):.1%}"
    )
