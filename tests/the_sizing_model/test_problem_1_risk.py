"""Problem 12.1 - sizing to a risk rather than to a point estimate.

Graded by asking the model, at the reader's answer, whether the risk is what they claimed. The
reader asks the same model through the one call the test hands them, so the oracle is the model
itself: nothing is stored, and changing the model changes the answer.

The seed is fixed, so a fleet asked about at the full number of draws gets the same share every
time. That is why the answer is held to the target exactly and not to within a tolerance: a
tolerance wider than one host's step accepts a count that misses the target.
"""

from __future__ import annotations

from dataclasses import replace
from functools import cache

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


def share_over_limit(model, scenario, hosts: float, samples: int) -> float:
    """The share of futures in which utilisation at the busy hour is past its limit."""
    forced = replace(
        scenario,
        samples=samples,
        overrides={**scenario.overrides, "hosts": float(hosts)},
    )
    return evaluate(model, forced).ceilings["queueing_headroom"]["p_over_limit"]


@pytest.fixture(scope="module")
def risk_at(model, scenario):
    """What the reader is handed: the share of futures over the queueing ceiling for a fleet, at
    the scenario's full number of draws unless asked for fewer. Each fleet and number of draws is
    worked out once, because the answer cannot change and the page runs this in a browser."""

    @cache
    def at(hosts: float, samples: int) -> float:
        return share_over_limit(model, scenario, hosts, samples)

    def risk(hosts: int, samples: int | None = None) -> float:
        return at(float(hosts), scenario.samples if samples is None else int(samples))

    return risk


@pytest.fixture(scope="module")
def answer(risk_at):
    """The reader's answer for each target, asked for once: each asking runs their search."""
    answers: dict[float, int] = {}

    def of(target: float) -> int:
        if target not in answers:
            answers[target] = hosts_for_risk(risk_at, target)
        return answers[target]

    return of


@pytest.mark.problem
@pytest.mark.parametrize("target", TARGETS)
def test_the_answer_meets_the_target(risk_at, answer, target):
    hosts = answer(target)
    assert risk_at(hosts) <= target, (
        f"at {hosts} hosts the busy hour is past its limit in more than {target:.0%} of futures, "
        "asked at the full number of draws. If you searched with fewer, ask again at the full "
        "number before you return. If your search ends on a pair of counts, return the one that "
        "meets the target."
    )


@pytest.mark.problem
@pytest.mark.parametrize("target", TARGETS)
def test_it_is_the_smallest_such_answer(risk_at, answer, target):
    """Buying more than the risk target requires is a different kind of wrong."""
    hosts = answer(target)
    assert risk_at(hosts - 1) > target, (
        f"{hosts - 1} hosts also meet the target at the full number of draws, so {hosts} is not "
        "the smallest. A search at fewer draws can stop short of the answer or beyond it: check "
        "the counts next to yours at the full number."
    )


@pytest.mark.problem
def test_less_risk_costs_more_machines(answer):
    counts = [answer(target) for target in TARGETS]
    assert counts == sorted(counts), (
        f"a tighter risk target cannot need fewer machines: {dict(zip(TARGETS, counts, strict=True))}"
    )


def test_the_relationship_is_monotonic(risk_at):
    """Scaffolding: a bisection is a legitimate way to answer this."""
    risks = [risk_at(n) for n in (40, 60, 90, 140)]
    assert risks == sorted(risks, reverse=True), risks


def test_one_more_host_never_raises_the_share(risk_at):
    """Scaffolding: at a fixed seed and a fixed number of draws, adding a host never raises the
    share, one host at a time. So "the smallest fleet that meets the target" has one answer."""
    risks = [risk_at(n, samples=4000) for n in range(40, 61)]
    assert risks == sorted(risks, reverse=True), risks


def test_one_fleet_gives_one_answer(model, scenario):
    """Scaffolding: asked twice at the full number of draws, a fleet gets the same share. That is
    what lets the problem tests hold the reader to the target exactly."""
    first = share_over_limit(model, scenario, 60, scenario.samples)
    second = share_over_limit(model, scenario, 60, scenario.samples)
    assert first == second


def test_fewer_draws_give_the_same_picture_more_cheaply(risk_at):
    """Scaffolding: the shortcut the stub recommends is real. Asked for a few thousand draws, the
    call answers close to what the full number gives, so a search can afford to use it."""
    assert abs(risk_at(60, samples=4000) - risk_at(60)) < 0.05
