"""Problem 11.1 - sizing to a risk rather than to a point estimate.

Graded by asking the model, at the reader's answer, whether the risk is what they claimed. The
oracle is the model itself, so nothing is stored and changing the model changes the answer.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.the_sizing_model.stubs import nodes_for_risk

TARGETS = [0.30, 0.15, 0.05]


@pytest.fixture(scope="module")
def model():
    return load_model("models/storage_cluster/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/storage_cluster/scenarios/reference.yaml")


def risk_at(model, scenario, nodes: int) -> float:
    forced = replace(scenario, overrides={**scenario.overrides, "nodes_purchased": float(nodes)})
    return evaluate(model, forced).ceilings["fill_level"]["p_over_limit"]


@pytest.mark.problem
@pytest.mark.parametrize("target", TARGETS)
def test_the_answer_meets_the_target(model, scenario, target):
    nodes = nodes_for_risk(target)
    assert risk_at(model, scenario, nodes) <= target + 0.01, (
        f"at {nodes} nodes the model still breaches the limit more often than {target:.0%}"
    )


@pytest.mark.problem
@pytest.mark.parametrize("target", TARGETS)
def test_it_is_the_smallest_such_answer(model, scenario, target):
    """Buying more than the risk target requires is a different kind of wrong."""
    nodes = nodes_for_risk(target)
    assert risk_at(model, scenario, nodes - 1) > target - 0.01, (
        f"{nodes - 1} nodes would also have met the target, so {nodes} is not the smallest"
    )


@pytest.mark.problem
def test_less_risk_costs_more_machines():
    counts = [nodes_for_risk(target) for target in TARGETS]
    assert counts == sorted(counts), (
        f"a tighter risk target cannot need fewer machines: {dict(zip(TARGETS, counts, strict=True))}"
    )


def test_the_relationship_is_monotonic(model, scenario):
    """Scaffolding: a bisection is a legitimate way to answer this."""
    risks = [risk_at(model, scenario, n) for n in (80, 120, 180, 260)]
    assert risks == sorted(risks, reverse=True), risks
