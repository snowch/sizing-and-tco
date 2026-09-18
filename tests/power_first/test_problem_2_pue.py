"""Problem 16.2 - a ratio quoted, a fraction paid."""

from __future__ import annotations

import pytest

from tests.power_first.stubs import pue_premium

CASES = [1.0, 1.1, 1.2, 1.35, 1.5, 1.8, 2.0]


def expected(pue: float) -> float:
    """The share that is not the machines. Derived from the definition."""
    return (pue - 1.0) / pue


@pytest.mark.problem
@pytest.mark.parametrize("pue", CASES)
def test_it_is_the_share_of_the_bill(pue):
    assert pue_premium(pue) == pytest.approx(expected(pue), rel=1e-9)


@pytest.mark.problem
def test_a_perfect_building_costs_nothing_extra():
    assert pue_premium(1.0) == pytest.approx(0.0)


@pytest.mark.problem
def test_the_fraction_is_larger_than_the_ratio_suggests():
    """The point of the problem.

    A multiplier that sounds like a small surcharge is a substantial share of the bill, and the
    two framings land very differently in a conversation about money.
    """
    assert pue_premium(1.5) == pytest.approx(1 / 3, rel=1e-9)
    assert pue_premium(2.0) == pytest.approx(0.5)


@pytest.mark.problem
def test_it_never_reaches_one():
    assert pue_premium(100.0) < 1.0, "the machines always get some of the power"


def test_the_models_own_multiplier_is_in_range():
    """Scaffolding: the book's assumption is inside the range this problem explores."""
    from sizing.dsl import load_model, load_scenario
    from sizing.evaluate import point

    pue = point(
        load_model("models/storage_cluster/model.yaml"),
        load_scenario("models/storage_cluster/scenarios/reference.yaml"),
    )["pue"]
    assert CASES[0] <= pue <= CASES[-1]
