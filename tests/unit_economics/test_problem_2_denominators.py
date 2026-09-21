"""Problem 17.2 - four defensible denominators, four different answers.

Every expected value is computed from the samples at test time. The test hands the stub the two
things the four need beyond the samples, the model's day-one holding and the months in the
horizon, as plain numbers.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.unit_economics.stubs import denominators

KEYS = ("at_horizon", "at_start", "average_linear", "per_sample")
MONTHS_PER_YEAR = 12.0


@pytest.fixture(scope="module")
def evaluated():
    return evaluate(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )


@pytest.fixture(scope="module")
def given(evaluated):
    """What the stub is handed: the two bags, day one's holding and the months in the horizon."""
    return (
        evaluated.samples["stored_data"],
        evaluated.samples["tco"],
        evaluated.point["stored_data_t0"],
        evaluated.point["horizon"] * MONTHS_PER_YEAR,
    )


@pytest.mark.problem
def test_all_four_are_returned(given):
    answer = denominators(*given)
    assert set(answer) == set(KEYS), f"expected {sorted(KEYS)}, got {sorted(answer)}"
    assert all(np.isfinite(v) and v > 0 for v in answer.values())


@pytest.mark.problem
def test_the_per_sample_one_is_the_median_of_ratios(given):
    capacity, total, _, months = given
    answer = denominators(*given)
    expected = float(np.median(total / capacity / months))
    assert answer["per_sample"] == pytest.approx(expected, rel=1e-6), (
        "divide each total by its own capacity first, then take the median. Taking the median of "
        "each and then dividing is a different quantity and is one of the other three."
    )


@pytest.mark.problem
def test_the_horizon_one_is_the_ratio_of_medians(given):
    capacity, total, _, months = given
    answer = denominators(*given)
    expected = float(np.median(total)) / float(np.median(capacity)) / months
    assert answer["at_horizon"] == pytest.approx(expected, rel=1e-6)


@pytest.mark.problem
def test_the_start_one_divides_by_day_one(given):
    _, total, at_start, months = given
    expected = float(np.median(total)) / at_start / months
    assert denominators(*given)["at_start"] == pytest.approx(expected, rel=1e-6), (
        "the day-one figure is the stored_at_start you were handed, and the months are the "
        "horizon's"
    )


@pytest.mark.problem
def test_the_linear_one_divides_by_the_mean_of_the_two(given):
    capacity, total, at_start, months = given
    held = (at_start + float(np.median(capacity))) / 2.0
    expected = float(np.median(total)) / held / months
    assert denominators(*given)["average_linear"] == pytest.approx(expected, rel=1e-6), (
        "a straight line under the curve: the mean of day one and the median horizon holding"
    )


@pytest.mark.problem
def test_they_are_not_close_together(given):
    """The point of the problem."""
    answer = denominators(*given)
    values = list(answer.values())
    assert max(values) / min(values) > 1.5, (
        f"four defensible denominators giving {min(values):.2f} to {max(values):.2f} is the "
        "finding, and most of it is day one against the rest: a fleet bought for growth looks "
        "dear per terabyte on the day it is installed. If yours are all within a few per cent, "
        "check that at_start is using the day-one figure and not the horizon one."
    )


@pytest.mark.problem
def test_starting_capacity_gives_the_most_expensive_answer(given):
    """A fleet bought for growth looks dreadful per terabyte on the day it is installed."""
    answer = denominators(*given)
    assert answer["at_start"] == max(answer.values())


def test_the_two_capacities_really_do_differ(given):
    """Scaffolding: the problem is about something."""
    capacity, _, at_start, _ = given
    ratio = float(np.median(capacity)) / at_start
    assert ratio > 1.5, f"what is held only grows by {ratio:.2f}x over the horizon"
