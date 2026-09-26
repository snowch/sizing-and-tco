"""Problem 23.2 - how often a failure has a culprit at all.

Every case here has an answer that comes out of arithmetic rather than out of a stored figure: a
uniform input above its own 80th percentile has a known chance of also being above its 90th, and
eight inputs drawn with no connection to the failure are each above their own 90th percentile in
one future in ten, independently. The last case is the web service, against the figure the build
publishes for it.
"""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate, sampled_inputs
from tests.what_the_model_got_wrong.stubs import share_with_nothing_extreme

N = 40_000
WEB_SERVICE = "models/web_service/model.yaml"
REFERENCE = "models/web_service/scenarios/reference.yaml"

#: What most wrong answers here have in common, said once so every case can say it.
WHERE_TO_LOOK = (
    "Return the share of failures in which *no* input is above its own percentile, not the share "
    "in which one is; and take each percentile across all the draws, not the failing ones alone."
)


def one_input(threshold: float, above: bool = True) -> tuple[dict, np.ndarray]:
    generator = np.random.Generator(np.random.PCG64(20260916))
    drawn = generator.random(N)
    failed = drawn > threshold if above else drawn < threshold
    return {"only": drawn}, failed


def innocent_inputs(count: int = 8) -> tuple[dict, np.ndarray]:
    """Inputs drawn with no connection at all to which futures failed."""
    generator = np.random.Generator(np.random.PCG64(1))
    draws = {f"input_{i}": generator.random(N) for i in range(count)}
    return draws, generator.random(N) < 0.2


def near(value: float, expected: float, tolerance: float) -> bool:
    """A comparison whose failure prints neither number: the message says where to look."""
    return abs(value - expected) <= tolerance


@pytest.mark.problem
def test_half_of_those_failures_had_nothing_extreme_in_them():
    """Failures are the top fifth; the top tenth is half of it. No stored answer required."""
    draws, failed = one_input(0.8)
    result = share_with_nothing_extreme(draws, failed)
    assert near(result, 0.5, 0.02), (
        "one input, and the failures are its top fifth. " + WHERE_TO_LOOK
    )


@pytest.mark.problem
def test_when_every_failure_is_extreme_the_answer_is_none():
    draws, failed = one_input(0.95)
    result = share_with_nothing_extreme(draws, failed)
    assert near(result, 0.0, 0.01), (
        "every failure here has its one input in its top twentieth. " + WHERE_TO_LOOK
    )


@pytest.mark.problem
def test_a_failure_at_the_low_end_has_no_culprit_at_the_high_end():
    """Extreme means beyond the stated percentile, which is the upper one. This is the check."""
    draws, failed = one_input(0.5, above=False)
    result = share_with_nothing_extreme(draws, failed)
    assert near(result, 1.0, 0.01), (
        "these failures are all in the input's bottom half. Extreme means above the stated "
        "percentile: the upper tail only, however unusual a low value is"
    )


@pytest.mark.problem
def test_raising_the_bar_finds_fewer_culprits():
    draws, failed = one_input(0.8)
    lenient = share_with_nothing_extreme(draws, failed, percentile=80.0)
    strict = share_with_nothing_extreme(draws, failed, percentile=99.0)
    assert strict > lenient, (
        "the harder it is to count as extreme, the more failures have nobody to blame"
    )


@pytest.mark.problem
def test_eight_innocent_inputs_give_the_share_arithmetic_says():
    """The trap the chapter is about, as a test.

    Eight independent inputs, none of which has anything to do with the failure. Each is above its
    own p90 in one future in ten, independently of the others and of the failure, and that is the
    whole of the oracle. A post-mortem that reports *something was extreme* without its base rate
    has reported how many inputs the model has.
    """
    draws, failed = innocent_inputs()
    arithmetic = 0.9 ** len(draws)
    assert near(share_with_nothing_extreme(draws, failed), arithmetic, 0.02), (
        "eight inputs with no connection to the failure, each above its own 90th percentile in "
        "one future in ten, independently of the others. Work out on paper what share of "
        "failures has none of them above it, and compare. " + WHERE_TO_LOOK
    )


@pytest.mark.problem
def test_it_agrees_with_the_post_mortem_the_build_publishes():
    model, scenario = load_model(WEB_SERVICE), load_scenario(REFERENCE)
    result = evaluate(model, scenario)
    failed = np.asarray(result.samples["queueing_headroom"], dtype=float) > 1.0
    draws = {
        name: np.asarray(result.samples[name], dtype=float)
        for name in sampled_inputs(model)
        if name in result.samples and name in model.ancestors("queueing_headroom")
    }
    published = load_result("postmortem")["summary"]["complete"]["nothing_extreme_share"]
    assert near(share_with_nothing_extreme(draws, failed), published, 1e-9), (
        "this is the web service, against the figure the build publishes. The chapter's "
        "attribution table prints its complement, the share of failures in which something was "
        "above its own 90th percentile. If a case above fails as well, fix that one first"
    )


# -- scaffolding: the cases are different cases, and the oracle is arithmetic -------------------


def test_the_uniform_cases_are_what_the_problem_claims():
    draws, failed = one_input(0.8)
    assert failed.mean() == pytest.approx(0.2, abs=0.01)
    extreme = draws["only"] > np.percentile(draws["only"], 90)
    assert float((~extreme[failed]).mean()) == pytest.approx(0.5, abs=0.02)


def test_the_innocent_inputs_are_innocent_and_the_arithmetic_holds():
    draws, failed = innocent_inputs()
    assert failed.mean() == pytest.approx(0.2, abs=0.01)
    extreme = np.zeros(N, dtype=bool)
    for drawn in draws.values():
        extreme |= drawn > np.percentile(drawn, 90)
    # The same share in the failures as everywhere: the inputs are innocent.
    assert float((~extreme[failed]).mean()) == pytest.approx(float((~extreme).mean()), abs=0.02)
    assert float((~extreme[failed]).mean()) == pytest.approx(0.9 ** len(draws), abs=0.02)
    assert 0.9 ** len(draws) < 0.5, "the case exists to show a culprit in most innocent failures"


def test_the_published_post_mortem_has_a_base_rate_to_compare_against():
    """The figure the chapter leans on: the two models differ, and both report both numbers."""
    summary = load_result("postmortem")["summary"]
    for which in ("complete", "incomplete"):
        payload = summary[which]
        assert payload["something_extreme_share"] > payload["something_extreme_everywhere"], (
            "conditioning on failure should find more extremes than there are generally, or the "
            "statistic is measuring the number of inputs and nothing else"
        )
        assert payload["nothing_extreme_share"] == pytest.approx(
            1.0 - payload["something_extreme_share"]
        ), "the page gives the web service's figure as the complement of this one"
