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
        load_model("models/storage_cluster/model.yaml"),
        load_scenario("models/storage_cluster/scenarios/reference.yaml"),
    )


@pytest.mark.problem
def test_it_agrees_with_the_model(values):
    mine = unit_cost(
        values["tco"], values["average_usable_capacity"], values["horizon"] * MONTHS_PER_YEAR
    )
    assert mine == pytest.approx(values["cost_per_usable_tb_month"], rel=1e-6), (
        f"the model publishes {values['cost_per_usable_tb_month']:.4f} and you make {mine:.4f}. "
        "If you are out by twelve, one of you is working in years."
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
        "the same total over the same capacity, quoted per year and per month, differs by twelve "
        "and both figures look equally authoritative"
    )


def test_the_model_declares_the_period_in_its_unit(values):
    """Scaffolding: the model cannot make this mistake, because the unit says which."""
    from sizing.dsl import load_model

    node = load_model("models/storage_cluster/model.yaml").nodes["cost_per_usable_tb_month"]
    assert "month" in node.unit, node.unit
