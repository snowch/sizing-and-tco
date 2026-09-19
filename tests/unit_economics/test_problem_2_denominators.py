"""Problem 17.2 - four defensible denominators, four different answers.

Every expected value is computed from the samples at test time.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.unit_economics.stubs import denominators

KEYS = ("at_horizon", "at_start", "average_linear", "per_sample")


@pytest.fixture(scope="module")
def evaluated():
    return evaluate(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )


@pytest.fixture(scope="module")
def samples(evaluated):
    return evaluated.samples["stored_data"], evaluated.samples["tco"]


@pytest.mark.problem
def test_all_four_are_returned(samples):
    answer = denominators(*samples)
    assert set(answer) == set(KEYS), f"expected {sorted(KEYS)}, got {sorted(answer)}"
    assert all(np.isfinite(v) and v > 0 for v in answer.values())


@pytest.mark.problem
def test_the_per_sample_one_is_the_median_of_ratios(samples, evaluated):
    capacity, total = samples
    months = evaluated.point["horizon"] * 12.0
    answer = denominators(*samples)
    expected = float(np.median(total / capacity / months))
    assert answer["per_sample"] == pytest.approx(expected, rel=1e-6), (
        "divide each total by its own capacity first, then take the median. Taking the median of "
        "each and then dividing is a different quantity and is one of the other three."
    )


@pytest.mark.problem
def test_the_horizon_one_is_the_ratio_of_medians(samples, evaluated):
    capacity, total = samples
    months = evaluated.point["horizon"] * 12.0
    answer = denominators(*samples)
    expected = float(np.median(total)) / float(np.median(capacity)) / months
    assert answer["at_horizon"] == pytest.approx(expected, rel=1e-6)


@pytest.mark.problem
def test_they_are_not_close_together(samples):
    """The point of the problem."""
    answer = denominators(*samples)
    values = list(answer.values())
    assert max(values) / min(values) > 1.5, (
        f"four defensible denominators giving {min(values):.2f} to {max(values):.2f} is the "
        "finding. If yours are all within a few per cent, check that at_start is using the "
        "day-one figure and not the horizon one."
    )


@pytest.mark.problem
def test_starting_capacity_gives_the_most_expensive_answer(samples):
    """A fleet bought for growth looks dreadful per terabyte on the day it is installed."""
    answer = denominators(*samples)
    assert answer["at_start"] == max(answer.values())


def test_the_two_capacities_really_do_differ(evaluated):
    """Scaffolding: the problem is about something."""
    ratio = float(np.median(evaluated.samples["stored_data"])) / evaluated.point["stored_data_t0"]
    assert ratio > 1.5, f"what is held only grows by {ratio:.2f}x over the horizon"
