"""Problem 12.1 - sizing to a risk rather than to a point estimate.

Graded by asking the model, at the reader's answer, whether the risk is what they claimed. The
oracle is the model itself, so nothing is stored and changing the model changes the answer.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.the_sizing_model.stubs import hosts_for_risk

TARGETS = [0.30, 0.15, 0.05]


@pytest.fixture(scope="module")
def model():
    return load_model("models/web_service/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/web_service/scenarios/reference.yaml")


def risk_at(model, scenario, hosts: int) -> float:
    forced = replace(scenario, overrides={**scenario.overrides, "hosts": float(hosts)})
    return evaluate(model, forced).ceilings["queueing_headroom"]["p_over_limit"]


@pytest.mark.problem
@pytest.mark.parametrize("target", TARGETS)
def test_the_answer_meets_the_target(model, scenario, target):
    hosts = hosts_for_risk(target)
    assert risk_at(model, scenario, hosts) <= target + 0.01, (
        f"at {hosts} hosts the model still breaches the limit more often than {target:.0%}"
    )


@pytest.mark.problem
@pytest.mark.parametrize("target", TARGETS)
def test_it_is_the_smallest_such_answer(model, scenario, target):
    """Buying more than the risk target requires is a different kind of wrong."""
    hosts = hosts_for_risk(target)
    assert risk_at(model, scenario, hosts - 1) > target - 0.01, (
        f"{hosts - 1} hosts would also have met the target, so {hosts} is not the smallest"
    )


@pytest.mark.problem
def test_less_risk_costs_more_machines():
    counts = [hosts_for_risk(target) for target in TARGETS]
    assert counts == sorted(counts), (
        f"a tighter risk target cannot need fewer machines: {dict(zip(TARGETS, counts, strict=True))}"
    )


def test_the_relationship_is_monotonic(model, scenario):
    """Scaffolding: a bisection is a legitimate way to answer this."""
    risks = [risk_at(model, scenario, n) for n in (40, 60, 90, 140)]
    assert risks == sorted(risks, reverse=True), risks
