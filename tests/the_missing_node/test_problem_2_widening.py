"""Problem 20.2 - the wrong repair, and what it costs."""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc
from tests.the_missing_node.stubs import widen_until_it_fits


@pytest.fixture(scope="module")
def samples():
    return mc.sample({"lognormal": {"p10": 1.0, "p90": 4.0}}, 100_000, mc.rng(3000))


def widened(samples: np.ndarray, factor: float) -> np.ndarray:
    median = float(np.median(samples))
    return median + (samples - median) * factor


@pytest.mark.problem
def test_an_observation_already_inside_needs_no_widening(samples):
    factor = widen_until_it_fits(samples, float(np.median(samples)))
    assert factor == pytest.approx(1.0, abs=0.05), (
        f"the observation is the model's own median, already inside the interval, and this "
        f"returned a factor of {factor:.2f}. An observation inside needs no widening, and a factor "
        "below one would narrow the interval rather than widen it. The docstring says what the "
        "smallest factor is."
    )


@pytest.mark.problem
def test_the_factor_it_returns_actually_works(samples):
    """Whatever it returns, widening by it has to put the observation inside."""
    observation = float(np.percentile(samples, 99.9))
    factor = widen_until_it_fits(samples, observation)
    low, high = mc.interval(widened(samples, factor))
    slack = 1e-9 * (high - low)  # the natural answer lands the end exactly on the observation
    assert low - slack <= observation <= high + slack, (
        f"widening by {factor:.2f} gives an interval of {low:.2f} to {high:.2f}, which still does "
        f"not contain {observation:.2f}"
    )


@pytest.mark.problem
def test_a_further_observation_needs_more_widening(samples):
    near = widen_until_it_fits(samples, float(np.percentile(samples, 99.0)))
    far = widen_until_it_fits(samples, float(np.percentile(samples, 100.0)) * 3)
    assert far > near


@pytest.mark.problem
def test_the_repair_destroys_the_model(samples):
    """The point. A model that cannot be wrong has stopped being able to be useful."""
    observation = float(np.percentile(samples, 100.0)) * 3
    factor = widen_until_it_fits(samples, observation)
    before = mc.interval(samples)
    after = mc.interval(widened(samples, factor))
    assert (after[1] - after[0]) > 3 * (before[1] - before[0]), (
        f"the interval goes from {before[1] - before[0]:.2f} wide to {after[1] - after[0]:.2f}, "
        "and the observation is three times the largest value the model drew. A factor that fits "
        "it stretches the interval much further than that. If the test that the factor works "
        "also fails, fix that one first: it is the same mistake."
    )


def test_widening_does_not_move_the_median(samples):
    """Scaffolding: the operation the problem describes is a scaling, not a shift.

    Which is what makes it the dishonest repair rather than a different model: the headline number
    stays exactly where it was and only the doubt changes.
    """
    assert float(np.median(widened(samples, 4.0))) == pytest.approx(
        float(np.median(samples)), rel=1e-9
    )
