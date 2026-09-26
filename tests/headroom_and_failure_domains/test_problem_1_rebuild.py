"""Problem 11.1 - what a host loss costs, and why fleet size changes the answer."""

from __future__ import annotations

import math

import pytest

from sizing.dsl import load_model
from sizing.evaluate import point
from tests.headroom_and_failure_domains.stubs import failure_reserve

MODEL = "models/web_service/model.yaml"

CASES = [(5, 1), (12, 1), (50, 1), (121, 1), (12, 2), (50, 3), (500, 2)]


def expected(hosts: int, losses: int) -> float:
    """The lost fraction, from the definition. Derived, never stored."""
    return losses / hosts


def agrees(got: float, want: float) -> bool:
    """Compared outside the assertion, so a failure never prints the value the test wanted."""
    return math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-12)


@pytest.mark.problem
@pytest.mark.parametrize(("hosts", "losses"), CASES)
def test_it_is_the_share_that_goes_away(hosts, losses):
    got = failure_reserve(hosts, losses)
    right = agrees(got, expected(hosts, losses))
    assert right, (
        f"failure_reserve({hosts}, {losses}) returned {got:.3g}. It should be the share of the "
        "fleet's capacity that goes away with the lost hosts."
    )


@pytest.mark.problem
def test_it_agrees_with_the_models_own_two_utilisations():
    """The model carries utilisation before and after a host loss; what one loss costs the fleet
    is the share of the survivors' utilisation that the loss added. Derived from the model."""
    values = point(load_model(MODEL))
    lost = values["hosts"] - values["hosts_after_failure"]
    from_the_model = 1.0 - values["utilisation"] / values["utilisation_after_failure"]
    right = agrees(failure_reserve(int(values["hosts"]), int(lost)), from_the_model)
    assert right, (
        "the web service model's utilisation before and after losing a host implies a different "
        "share from the one your function returns. The load a loss adds to the survivors is the "
        "capacity it took away."
    )


@pytest.mark.problem
def test_a_small_cluster_pays_a_large_margin():
    """The capacity argument for larger pools: as a share, a small fleet pays far more."""
    small = failure_reserve(5, 1)
    large = failure_reserve(500, 1)
    assert small > 20 * large, (
        f"your function says one machine in five costs {small:.0%} of the fleet and one in five "
        f"hundred costs {large:.1%}. Each fleet keeps one machine free, but as a share of the "
        "fleet the small one pays far more. Check which share your function returns."
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
