"""Problem 16.1 - graded against the model's own power chain, run backwards."""

from __future__ import annotations

import math

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.power_first.stubs import hosts_that_fit

#: An allocation in kilowatts, a draw per machine in watts, a facility multiplier. Each divides
#: out to a fraction of a machine: one just over a half, one well over, and one under, so that
#: neither rounding to the nearest whole number nor rounding up passes all three.
ROUNDING = [(1.05, 100.0, 1.0), (1.09, 100.0, 1.0), (4.0, 300.0, 1.2)]

UNITS = (
    "The allocation is in kilowatts and the draw per machine is in watts: convert one of them "
    "before you divide."
)
ROUND_DOWN = (
    "A supply that cannot be exceeded rounds down. Every other constraint in this book is a "
    "demand to be satisfied, and rounds up."
)


def most_that_fit(budget_kw: float, watts_per_host: float, pue: float) -> int:
    """The oracle, from the problem's own terms: add machines until the next would go over."""
    count = 0
    while (count + 1) * watts_per_host * pue <= budget_kw * 1000:
        count += 1
    return count


@pytest.fixture(scope="module")
def values():
    return point(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/power_first.yaml"),
    )


@pytest.mark.problem
def test_it_inverts_the_models_power_chain(values):
    """The scenario's fleet draws what it draws; that draw must buy back the same fleet.

    With a rounding hair on the budget: the scenario's draw is exactly the fleet's, so a floor at
    that boundary would be decided by the last bit of a product, which is no test of anything.
    """
    budget = values["facility_power"] * (1 + 1e-9)
    mine = hosts_that_fit(budget, values["host_power"], values["pue"])
    if mine == int(values["hosts"]):
        return
    hint = (
        UNITS if mine == 0 else "Check which way up the multiplier goes, and which way you round."
    )
    pytest.fail(
        f"the power-first scenario's fleet draws {values['facility_power']:.1f} kW at the wall, "
        f"and your function fits {mine} machines in that allocation. It should give back the "
        f"scenario's own fleet, the 'hosts in the fleet' row of the chapter's first table. {hint}",
        pytrace=False,
    )


@pytest.mark.problem
def test_the_facility_multiplier_reduces_what_fits():
    """An inefficient building buys you fewer machines, not more."""
    efficient = hosts_that_fit(50.0, 450.0, 1.1)
    wasteful = hosts_that_fit(50.0, 450.0, 1.8)
    if efficient == 0:
        pytest.fail(f"your function fits no 450 W machines in 50 kW. {UNITS}", pytrace=False)
    if not wasteful < efficient:
        pytest.fail(
            "the multiplier applies to the machines' draw. If yours is the other way up, an "
            "inefficient datacentre appears to fit more machines, which would be a remarkable "
            "property of inefficiency.",
            pytrace=False,
        )


@pytest.mark.problem
@pytest.mark.parametrize(("budget_kw", "watts_per_host", "pue"), ROUNDING)
def test_it_rounds_down(budget_kw, watts_per_host, pue):
    """The one rounding in this book that goes the other way."""
    mine = hosts_that_fit(budget_kw, watts_per_host, pue)
    fits = most_that_fit(budget_kw, watts_per_host, pue)
    if mine == fits:
        return
    case = f"{budget_kw} kW, {watts_per_host:.0f} W a machine, a multiplier of {pue}"
    if mine == 0:
        pytest.fail(f"{case}: your function fits no machines. {UNITS}", pytrace=False)
    if abs(mine - fits) > 1:
        pytest.fail(
            f"{case}: your function fits {mine}, which is further out than rounding could put it. "
            "Check which way up the multiplier goes.",
            pytrace=False,
        )
    if mine > fits:
        pytest.fail(
            f"{case}: your function fits {mine}, and that many machines draw more than the "
            f"allocation. {ROUND_DOWN}",
            pytrace=False,
        )
    pytest.fail(
        f"{case}: your function fits {mine}, and there is room under the allocation for another.",
        pytrace=False,
    )


@pytest.mark.problem
def test_no_power_fits_nothing():
    mine = hosts_that_fit(0.0, 450.0, 1.3)
    if mine != 0:
        pytest.fail(f"an allocation of nothing fits {mine} machines", pytrace=False)


def test_the_scenario_is_the_one_the_problem_describes(values):
    """Scaffolding: the power-first scenario still exists and is power-bound."""
    assert values["facility_power"] == pytest.approx(16.0, abs=1.0), (
        f"the scenario draws {values['facility_power']:.1f} kW; problem 16.1 describes it as a "
        "sixteen-kilowatt allocation"
    )
    assert math.isclose(values["hosts"], int(values["hosts"]))


def test_the_oracle_gives_back_the_scenario_fleet(values):
    """Scaffolding: the oracle and the model agree, so the first problem test is answerable."""
    budget = values["facility_power"] * (1 + 1e-9)
    assert most_that_fit(budget, values["host_power"], values["pue"]) == int(values["hosts"])
    assert most_that_fit(50.0, 450.0, 1.8) < most_that_fit(50.0, 450.0, 1.1)


def test_the_rounding_cases_catch_the_wrong_roundings():
    """Scaffolding: rounding to the nearest and rounding up each fail at least one case.

    Python rounds a half to the even number, so a case at exactly a half passed `round()`. That
    is why one case is above a half.
    """
    exact = [budget * 1000 / (watts * pue) for budget, watts, pue in ROUNDING]
    fits = [most_that_fit(*case) for case in ROUNDING]
    assert all(not math.isclose(q, round(q)) for q in exact), "a case divides out whole"
    assert any(round(q) != want for q, want in zip(exact, fits, strict=True))
    assert all(math.ceil(q) != want for q, want in zip(exact, fits, strict=True))
