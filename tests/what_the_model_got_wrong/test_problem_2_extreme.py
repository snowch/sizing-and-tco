"""Problem 22.2 - how often a failure has a culprit at all.

Every case here has an answer that comes out of arithmetic rather than out of a stored figure: a
uniform input above its own 80th percentile has a known chance of also being above its 90th, and
that is the whole of the oracle.
"""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from tests.what_the_model_got_wrong.stubs import was_anything_extreme

N = 40_000


def one_input(threshold: float, above: bool = True) -> tuple[dict, np.ndarray]:
    generator = np.random.Generator(np.random.PCG64(20260916))
    drawn = generator.random(N)
    failed = drawn > threshold if above else drawn < threshold
    return {"only": drawn}, failed


@pytest.mark.problem
def test_half_of_those_failures_had_nothing_extreme_in_them():
    """Failures are the top fifth; the top tenth is half of it. No stored answer required."""
    draws, failed = one_input(0.8)
    assert was_anything_extreme(draws, failed) == pytest.approx(0.5, abs=0.02)


@pytest.mark.problem
def test_when_every_failure_is_extreme_the_answer_is_none():
    draws, failed = one_input(0.95)
    assert was_anything_extreme(draws, failed) == pytest.approx(0.0, abs=0.01)


@pytest.mark.problem
def test_a_failure_at_the_low_end_has_no_culprit_at_the_high_end():
    """Extreme means beyond the stated percentile, which is the upper one. This is the check."""
    draws, failed = one_input(0.5, above=False)
    assert was_anything_extreme(draws, failed) == pytest.approx(1.0, abs=0.01)


@pytest.mark.problem
def test_raising_the_bar_finds_fewer_culprits():
    draws, failed = one_input(0.8)
    lenient = was_anything_extreme(draws, failed, percentile=80.0)
    strict = was_anything_extreme(draws, failed, percentile=99.0)
    assert strict > lenient, (
        "the harder it is to count as extreme, the more failures have nobody to blame"
    )


@pytest.mark.problem
def test_more_inputs_make_a_culprit_easier_to_find_even_when_innocent():
    """The trap the chapter is about, as a test.

    Eight independent inputs, none of which has anything to do with the failure, and one of them
    is beyond its own p90 in most futures. A post-mortem that reports *something was extreme*
    without its base rate has reported how many inputs the model has.
    """
    generator = np.random.Generator(np.random.PCG64(1))
    draws = {f"input_{i}": generator.random(N) for i in range(8)}
    failed = generator.random(N) < 0.2
    assert was_anything_extreme(draws, failed) < 0.5, (
        "with eight inputs, most futures contain something beyond its own p90 — including the "
        "ones where nothing went wrong"
    )


# -- scaffolding: the cases are different cases, and the oracle is arithmetic -------------------


def test_the_uniform_cases_are_what_the_problem_claims():
    draws, failed = one_input(0.8)
    assert failed.mean() == pytest.approx(0.2, abs=0.01)
    extreme = draws["only"] > np.percentile(draws["only"], 90)
    assert float((~extreme[failed]).mean()) == pytest.approx(0.5, abs=0.02)


def test_the_published_post_mortem_has_a_base_rate_to_compare_against():
    """The figure the chapter leans on: the two models differ, and both report both numbers."""
    summary = load_result("postmortem")["summary"]
    for which in ("complete", "incomplete"):
        payload = summary[which]
        assert payload["something_extreme_share"] > payload["something_extreme_everywhere"], (
            "conditioning on failure should find more extremes than there are generally, or the "
            "statistic is measuring the number of inputs and nothing else"
        )
