"""Problem 16.2 - a ratio quoted, a fraction paid."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.power_first.stubs import pue_premium

CASES = [1.0, 1.1, 1.2, 1.35, 1.5, 1.8, 2.0]

WHERE_TO_LOOK = (
    "Check two things. The share is of the whole bill, the machines' own draw included, not of "
    "what the machines draw. And it is the building's part of the bill, not the machines'."
)


@pytest.fixture(scope="module")
def building_share():
    """The oracle, from the model's own energy bill rather than from a formula.

    The reference fleet's bill in each building, and the same fleet's bill in a building that
    spends nothing on itself: what the building takes is the difference, as a share of its bill.
    """
    model = load_model("models/web_service/model.yaml")
    scenario = load_scenario("models/web_service/scenarios/reference.yaml")

    def bill(pue: float) -> float:
        moved = replace(scenario, overrides={**scenario.overrides, "pue": pue})
        return point(model, moved)["annual_energy_cost"]

    perfect = bill(1.0)
    return {pue: (bill(pue) - perfect) / bill(pue) for pue in CASES}


@pytest.mark.problem
@pytest.mark.parametrize("pue", CASES)
def test_it_is_the_share_of_the_bill(pue, building_share):
    mine = pue_premium(pue)
    if not math.isclose(mine, building_share[pue], rel_tol=1e-9, abs_tol=1e-12):
        pytest.fail(
            f"for a multiplier of {pue}, {mine:.4f} is not the building's share of the bill. "
            f"{WHERE_TO_LOOK}",
            pytrace=False,
        )


@pytest.mark.problem
def test_a_perfect_building_costs_nothing_extra():
    mine = pue_premium(1.0)
    if not math.isclose(mine, 0.0, abs_tol=1e-12):
        pytest.fail(
            f"a building with a multiplier of 1.0 spends nothing on itself, and yours takes {mine:.4f} "
            "of the bill",
            pytrace=False,
        )


@pytest.mark.problem
def test_the_share_is_not_the_surcharge():
    """The point of the problem: the ratio quoted and the share paid are different numbers."""
    for pue in (1.5, 2.0):
        if math.isclose(pue_premium(pue), pue - 1.0, rel_tol=1e-9):
            pytest.fail(
                f"for a multiplier of {pue} you returned what the building draws for each watt "
                "the machines draw. The problem asks for the building's share of the whole bill, "
                "and the whole bill includes the machines' own draw.",
                pytrace=False,
            )


@pytest.mark.problem
def test_it_never_reaches_one():
    if not pue_premium(100.0) < 1.0:
        pytest.fail("the machines always get some of the power", pytrace=False)


def test_the_models_own_multiplier_is_in_range():
    """Scaffolding: the book's assumption is inside the range this problem explores."""
    pue = point(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )["pue"]
    assert CASES[0] <= pue <= CASES[-1]


def test_the_oracle_is_a_share(building_share):
    """Scaffolding: the oracle starts at nothing, grows with the multiplier and stays under one.

    And it is not the surcharge, so the test that says so can be passed.
    """
    shares = [building_share[pue] for pue in CASES]
    assert shares[0] == pytest.approx(0.0, abs=1e-12)
    assert all(a < b for a, b in zip(shares[:-1], shares[1:], strict=True))
    assert shares[-1] < 1.0
    assert not math.isclose(building_share[1.5], 1.5 - 1.0)
