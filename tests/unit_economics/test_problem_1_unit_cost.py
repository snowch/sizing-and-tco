"""Problem 17.1 - graded against the model's own unit-economics node."""

from __future__ import annotations

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.unit_economics.stubs import unit_cost

MONTHS_PER_YEAR = 12.0


@pytest.fixture(scope="module")
def values():
    return point(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )


def _hint(mine: float, published: float, months: float) -> str:
    """Where to look, from how far out the reader is. Never what the answer is."""
    ratio = mine / published
    if ratio == pytest.approx(MONTHS_PER_YEAR, rel=1e-3) or ratio == pytest.approx(
        1 / MONTHS_PER_YEAR, rel=1e-3
    ):
        return "You are out by twelve, so one of you is working in years."
    if ratio == pytest.approx(months, rel=1e-3):
        return (
            "You are out by the number of months in the horizon: you have a cost per terabyte "
            "over the whole period. Divide by the months as well."
        )
    return (
        "Get the three cases you can check in your head right first: they are a test of their own."
    )


@pytest.mark.problem
def test_it_agrees_with_the_model(values):
    months = values["horizon"] * MONTHS_PER_YEAR
    mine = unit_cost(values["tco"], values["average_stored"], months)
    published = values["cost_per_stored_tb_month"]
    assert mine == pytest.approx(published, rel=1e-6), (
        "your cost per terabyte per month is not the model's. " + _hint(mine, published, months)
    )


@pytest.mark.problem
def test_the_cases_you_can_check_in_your_head():
    assert unit_cost(1200.0, 1.0, 12.0) == pytest.approx(100.0)
    assert unit_cost(1200.0, 10.0, 12.0) == pytest.approx(10.0)
    assert unit_cost(1200.0, 1.0, 1.0) == pytest.approx(1200.0)


@pytest.mark.problem
def test_a_year_and_a_month_differ_by_twelve():
    """The confusion this problem exists for."""
    per_month = unit_cost(6000.0, 100.0, 60.0)
    per_year = unit_cost(6000.0, 100.0, 5.0)
    assert per_year == pytest.approx(12 * per_month), (
        "the same total over the same holding, quoted per year and per month, differs by twelve, "
        "and both figures look equally authoritative"
    )


def test_the_model_declares_the_period_in_its_unit(values):
    """Scaffolding: the model cannot make this mistake, because the unit says which."""
    from sizing.dsl import load_model

    node = load_model("models/web_service/model.yaml").nodes["cost_per_stored_tb_month"]
    assert "month" in node.unit, node.unit


def test_the_hints_cannot_both_fire(values):
    """Scaffolding: out by twelve and out by the horizon's months are different mistakes here."""
    months = values["horizon"] * MONTHS_PER_YEAR
    assert months != pytest.approx(MONTHS_PER_YEAR, rel=1e-2), (
        "a one-year horizon makes the two hints in _hint the same; the problem needs another"
    )
