"""Problem 15.2 - a refresh cycle, and the refresh at the end of the horizon.

The test checks consistency rather than a particular convention, because which one is right is a
modelling choice and the chapter says so.
"""

from __future__ import annotations

import pytest

from tests.capex_opex_and_lifecycle.stubs import lifecycle_total

CAPEX, OPEX = 1_000_000.0, 300_000.0

#: What tests 1 to 3 check, said without the answer: the purchases are whole, and the first one
#: is at the start. The boundary is left to the two tests below.
WHOLE_PURCHASES = (
    "count whole purchases: one at the start, and one more at each refresh partway through the "
    "horizon. Each purchase is the whole capital cost, not a share of it spread over the years "
    "the fleet is used."
)


@pytest.mark.problem
def test_no_refresh_inside_the_horizon_is_one_purchase():
    assert lifecycle_total(CAPEX, OPEX, 3.0, 5.0) == pytest.approx(CAPEX + 3 * OPEX), (
        WHOLE_PURCHASES
    )


@pytest.mark.problem
def test_a_refresh_partway_through_is_two():
    assert lifecycle_total(CAPEX, OPEX, 7.0, 4.0) == pytest.approx(2 * CAPEX + 7 * OPEX), (
        WHOLE_PURCHASES
    )


@pytest.mark.problem
def test_two_refreshes_are_three_purchases():
    assert lifecycle_total(CAPEX, OPEX, 11.0, 4.0) == pytest.approx(3 * CAPEX + 11 * OPEX), (
        WHOLE_PURCHASES
    )


@pytest.mark.problem
def test_the_boundary_is_whatever_you_decided_but_it_is_one_of_the_two():
    """A refresh landing exactly on the horizon: either convention, consistently applied."""
    at_boundary = lifecycle_total(CAPEX, OPEX, 5.0, 5.0)
    assert at_boundary == pytest.approx(CAPEX + 5 * OPEX) or at_boundary == pytest.approx(
        2 * CAPEX + 5 * OPEX
    ), (
        f"a five-year horizon with a five-year refresh is either one purchase or two, and you "
        f"returned {at_boundary:,.0f}. Pick one and say why in a comment."
    )


@pytest.mark.problem
def test_the_convention_is_applied_consistently():
    """Whatever you chose at five and five, you have to mean at ten and five."""
    one_cycle = lifecycle_total(CAPEX, OPEX, 5.0, 5.0) - 5 * OPEX
    two_cycles = lifecycle_total(CAPEX, OPEX, 10.0, 5.0) - 10 * OPEX
    assert two_cycles == pytest.approx(one_cycle + CAPEX), (
        "a horizon twice as long with the same cycle buys exactly one more cluster under either "
        "convention. If it does not, the boundary is being handled differently in the two cases."
    )


def test_the_boundary_case_is_worth_a_whole_purchase():
    """Scaffolding: the ambiguity the problem is about is material, not a rounding error."""
    total = CAPEX + 5 * OPEX
    assert CAPEX / total > 0.2, (
        f"a whole extra purchase is {CAPEX / total:.0%} of the total. If that were small, the "
        "convention would not matter and the problem would be teaching nothing."
    )
