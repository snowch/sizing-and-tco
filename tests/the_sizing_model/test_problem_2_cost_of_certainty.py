"""Problem 12.2 - what a percentage point of risk costs in hosts, and why the last ones cost most.

Graded against the reader's own answer to 12.1, so that both fleets are sized by the same rule,
and against the model for the range the reference design sits in. Nothing is stored.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.the_sizing_model.stubs import cost_of_certainty, hosts_for_risk


@pytest.fixture(scope="module")
def model():
    return load_model("models/web_service/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/web_service/scenarios/reference.yaml")


@pytest.fixture(scope="module")
def risk_at(model, scenario):
    """The same call problem 12.1 hands the reader, so both fleets are sized by the same rule."""

    def risk(hosts: int, samples: int | None = None) -> float:
        forced = replace(
            scenario,
            samples=scenario.samples if samples is None else int(samples),
            overrides={**scenario.overrides, "hosts": float(hosts)},
        )
        return evaluate(model, forced).ceilings["queueing_headroom"]["p_over_limit"]

    return risk


@pytest.mark.problem
def test_it_is_the_gap_between_the_two_fleets_it_compares(risk_at):
    assert cost_of_certainty(risk_at, 0.30, 0.10) == hosts_for_risk(risk_at, 0.10) - hosts_for_risk(
        risk_at, 0.30
    )


@pytest.mark.problem
def test_removing_risk_costs_hosts(risk_at):
    assert cost_of_certainty(risk_at, 0.30, 0.10) > 0


@pytest.mark.problem
def test_going_the_other_way_gives_them_back(risk_at):
    assert cost_of_certainty(risk_at, 0.10, 0.30) == -cost_of_certainty(risk_at, 0.30, 0.10)


@pytest.mark.problem
def test_the_last_points_cost_more_hosts_than_the_first(risk_at):
    """The shape that makes this a decision rather than an optimisation."""
    early = cost_of_certainty(risk_at, 0.35, 0.25)
    late = cost_of_certainty(risk_at, 0.15, 0.05)
    assert late > early, (
        f"the first ten points of risk cost {early} hosts and the last ten cost {late}. If they "
        "came out the other way round, check that both fleets are being sized by the same rule."
    )


def test_the_reference_design_is_somewhere_in_the_interesting_range(model, scenario):
    """Scaffolding: the problem has room to move in both directions."""
    reference = evaluate(model, scenario).ceilings["queueing_headroom"]["p_over_limit"]
    assert 0.1 < reference < 0.6, (
        f"the reference design breaches in {reference:.0%} of samples; if that were near zero or "
        "near one there would be nothing to trade off"
    )
