"""Problem 11.2 - what a percentage point of risk costs, and why the last ones cost most."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.the_sizing_model.stubs import cost_of_certainty, nodes_for_risk


@pytest.fixture(scope="module")
def model():
    return load_model("models/storage_cluster/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/storage_cluster/scenarios/reference.yaml")


def median_tco(model, scenario, nodes: int) -> float:
    forced = replace(scenario, overrides={**scenario.overrides, "nodes_purchased": float(nodes)})
    return evaluate(model, forced).summaries["tco"]["p50"]


@pytest.mark.problem
def test_it_matches_the_two_designs_it_compares(model, scenario):
    mine = cost_of_certainty(0.30, 0.10)
    expected = median_tco(model, scenario, nodes_for_risk(0.10)) - median_tco(
        model, scenario, nodes_for_risk(0.30)
    )
    assert mine == pytest.approx(expected, rel=0.02)


@pytest.mark.problem
def test_removing_risk_costs_money():
    assert cost_of_certainty(0.30, 0.10) > 0


@pytest.mark.problem
def test_going_the_other_way_gives_it_back():
    there = cost_of_certainty(0.30, 0.10)
    back = cost_of_certainty(0.10, 0.30)
    assert back == pytest.approx(-there, rel=0.02)


@pytest.mark.problem
def test_the_last_points_cost_more_than_the_first():
    """The shape that makes this a decision rather than an optimisation."""
    early = cost_of_certainty(0.35, 0.25)
    late = cost_of_certainty(0.15, 0.05)
    assert late > early, (
        f"the first ten points of risk cost {early:,.0f} and the last ten cost {late:,.0f}. If "
        "they came out the other way round, check that both designs are being sized by the same "
        "rule."
    )


def test_the_reference_design_is_somewhere_in_the_interesting_range(model, scenario):
    """Scaffolding: the problem has room to move in both directions."""
    reference = evaluate(model, scenario).ceilings["fill_level"]["p_over_limit"]
    assert 0.1 < reference < 0.6, (
        f"the reference design breaches in {reference:.0%} of samples; if that were near zero or "
        "near one there would be nothing to trade off"
    )
