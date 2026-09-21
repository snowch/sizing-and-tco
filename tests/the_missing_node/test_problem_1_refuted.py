"""Problem 20.1 - what would count as evidence.

Graded at the two ends where there is a right answer, and for self-consistency in between, because
in between there is no right answer and a test claiming otherwise would be the error the chapter
is about. The observations arrive as an array, one entry each, because a rule about how many you
have cannot be stated over a single number.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc
from tests.the_missing_node.stubs import is_refuted


@pytest.fixture(scope="module")
def samples():
    return mc.sample({"lognormal": {"p10": 1.0, "p90": 4.0}}, 100_000, mc.rng(2000))


def percentile(samples, q):
    return float(np.percentile(samples, q))


def repeated(value: float, count: int) -> np.ndarray:
    """The same figure observed ``count`` times."""
    return np.full(count, value, dtype=float)


@pytest.mark.problem
def test_one_miss_is_never_a_refutation(samples):
    """A 90% interval is supposed to be missed one time in ten."""
    just_outside = repeated(percentile(samples, 96), 1)
    assert not is_refuted(samples, just_outside), (
        "a single observation just outside a 90% interval is the expected behaviour of an "
        "interval that is working. A rule that rejects on one miss will reject a correct model "
        "sooner or later, because a correct model is supposed to miss."
    )


@pytest.mark.problem
def test_observations_inside_are_never_a_refutation(samples):
    """The model's own median, seen once and seen a hundred times."""
    median = percentile(samples, 50)
    assert not is_refuted(samples, repeated(median, 1))
    assert not is_refuted(samples, repeated(median, 100)), (
        "a hundred observations at the model's median agree with it a hundred times. A rule that "
        "grows more suspicious of every observation, inside or out, is not weighing where they "
        "landed."
    )


@pytest.mark.problem
def test_something_no_plausible_model_produces_always_is(samples):
    far = percentile(samples, 100) * 50
    for count in (1, 5, 50):
        assert is_refuted(samples, repeated(far, count)), (
            "an observation fifty times the largest value the model ever produced is not bad "
            f"luck, and it is not less damning for having been seen only {count} time(s)"
        )


@pytest.mark.problem
def test_more_copies_of_the_same_miss_are_more_damning(samples):
    """If a rule is not monotonic in the evidence, it is not a rule."""
    value = percentile(samples, 99.5)
    counts = (1, 10, 100, 1000)
    verdicts = [is_refuted(samples, repeated(value, n)) for n in counts]
    assert verdicts == sorted(verdicts), (
        f"the same observation becomes more damning as you collect more of them, never less: "
        f"{dict(zip(counts, verdicts, strict=True))}"
    )


@pytest.mark.problem
def test_further_out_is_more_damning(samples):
    """Twenty observations each, at three distances from the model's belief."""
    at = [percentile(samples, q) for q in (95.0, 99.0, 99.9)]
    verdicts = [is_refuted(samples, repeated(v, 20)) for v in at]
    assert verdicts == sorted(verdicts), (
        f"twenty observations further into the tail are never less damning than twenty nearer "
        f"the interval: {verdicts}"
    )


def test_the_interval_really_does_miss_one_in_ten(samples):
    """Scaffolding: the premise the problem rests on."""
    low, high = mc.interval(samples)
    outside = float(np.mean((samples < low) | (samples > high)))
    assert outside == pytest.approx(0.10, abs=0.005), outside


def test_the_cases_are_where_the_docstring_says(samples):
    """Scaffolding: the ends are ends.

    The single miss is outside the 90% interval but inside the model's belief, and the far value
    is beyond every draw the model made. If either stopped being true the problem's two fixed
    verdicts would be arguable, which is what the middle of the problem is for.
    """
    low, high = mc.interval(samples)
    just_outside = percentile(samples, 96)
    assert high < just_outside < percentile(samples, 100)
    assert percentile(samples, 100) * 50 > percentile(samples, 100)
    assert low < percentile(samples, 50) < high
