"""Problem 12.1 - sizing to a risk rather than to a point estimate.

Graded by asking the model, at the reader's answer, whether the risk is what they claimed. The
reader asks the same model through the one call the test hands them, so the oracle is the model
itself: nothing is stored, and changing the model changes the answer.
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


@pytest.fixture(scope="module")
def risk_at(model, scenario):
    """What the reader is handed: the share of futures over the queueing ceiling for a fleet, at
    the scenario's full number of draws unless asked for fewer."""

    def risk(hosts: int, samples: int | None = None) -> float:
        forced = replace(
            scenario,
            samples=scenario.samples if samples is None else int(samples),
            overrides={**scenario.overrides, "hosts": float(hosts)},
        )
        return evaluate(model, forced).ceilings["queueing_headroom"]["p_over_limit"]

    return risk


@pytest.mark.problem
@pytest.mark.parametrize("target", TARGETS)
def test_the_answer_meets_the_target(risk_at, target):
    hosts = hosts_for_risk(risk_at, target)
    assert risk_at(hosts) <= target + 0.01, (
        f"at {hosts} hosts the model still breaches the limit more often than {target:.0%}"
    )


@pytest.mark.problem
@pytest.mark.parametrize("target", TARGETS)
def test_it_is_the_smallest_such_answer(risk_at, target):
    """Buying more than the risk target requires is a different kind of wrong."""
    hosts = hosts_for_risk(risk_at, target)
    assert risk_at(hosts - 1) > target - 0.01, (
        f"{hosts - 1} hosts would also have met the target, so {hosts} is not the smallest"
    )


@pytest.mark.problem
def test_less_risk_costs_more_machines(risk_at):
    counts = [hosts_for_risk(risk_at, target) for target in TARGETS]
    assert counts == sorted(counts), (
        f"a tighter risk target cannot need fewer machines: {dict(zip(TARGETS, counts, strict=True))}"
    )


def test_the_relationship_is_monotonic(risk_at):
    """Scaffolding: a bisection is a legitimate way to answer this."""
    risks = [risk_at(n) for n in (40, 60, 90, 140)]
    assert risks == sorted(risks, reverse=True), risks


def test_fewer_draws_give_the_same_picture_more_cheaply(risk_at):
    """Scaffolding: the shortcut the stub recommends is real. Asked for a few thousand draws, the
    call answers close to what the full number gives, so a search can afford to use it."""
    assert abs(risk_at(60, samples=4000) - risk_at(60)) < 0.05
