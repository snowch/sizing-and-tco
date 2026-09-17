"""Problem 20.1 - what would count as evidence.

Graded at the two ends where there is a right answer, and for self-consistency in between, because
in between there is no right answer and a test claiming otherwise would be the error the chapter
is about.
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


@pytest.mark.problem
def test_one_miss_is_never_a_refutation(samples):
    """A 90% interval is supposed to be missed one time in ten."""
    just_outside = percentile(samples, 96)
    assert not is_refuted(samples, just_outside, observations=1), (
        "a single observation just outside a 90% interval is the expected behaviour of an "
        "interval that is working. A rule that rejects on one miss will reject a correct model "
        "sooner or later, because a correct model is supposed to miss."
    )


@pytest.mark.problem
def test_an_observation_inside_is_never_a_refutation(samples):
    assert not is_refuted(samples, percentile(samples, 50), observations=1)
    assert not is_refuted(samples, percentile(samples, 50), observations=100)


@pytest.mark.problem
def test_something_no_plausible_model_produces_always_is(samples):
    far = percentile(samples, 100) * 50
    for count in (1, 5, 50):
        assert is_refuted(samples, far, observations=count), (
            "an observation fifty times the largest value the model ever produced is not bad luck"
        )


@pytest.mark.problem
def test_more_observations_make_the_same_miss_more_damning(samples):
    """If a rule is not monotonic in the evidence, it is not a rule."""
    value = percentile(samples, 99.5)
    verdicts = [is_refuted(samples, value, observations=n) for n in (1, 10, 100, 1000)]
    assert verdicts == sorted(verdicts), (
        f"the same observation becomes more damning as you collect more of them, never less: "
        f"{dict(zip((1, 10, 100, 1000), verdicts, strict=True))}"
    )


@pytest.mark.problem
def test_further_out_is_more_damning(samples):
    at = [percentile(samples, q) for q in (95.0, 99.0, 99.9)]
    verdicts = [is_refuted(samples, v, observations=20) for v in at]
    assert verdicts == sorted(verdicts)


def test_the_interval_really_does_miss_one_in_ten(samples):
    """Scaffolding: the premise the problem rests on."""
    low, high = mc.interval(samples)
    outside = float(np.mean((samples < low) | (samples > high)))
    assert outside == pytest.approx(0.10, abs=0.005), outside
