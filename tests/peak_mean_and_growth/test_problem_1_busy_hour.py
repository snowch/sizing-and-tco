"""Problem 4.1 - the busy hour, graded against the shape it is drawn from."""

from __future__ import annotations

import numpy as np
import pytest

from tests.peak_mean_and_growth.stubs import busy_hour_rate

FLAT = np.ones(24)
#: A working day: quiet overnight, a morning ramp, a lunch dip, an afternoon peak.
DIURNAL = np.array(
    [
        0.3,
        0.2,
        0.2,
        0.2,
        0.3,
        0.5,
        1.0,
        2.0,
        3.0,
        3.5,
        3.4,
        3.0,
        2.6,
        3.2,
        3.8,
        3.6,
        3.0,
        2.2,
        1.6,
        1.2,
        0.9,
        0.7,
        0.5,
        0.4,
    ]
)
#: A batch window: almost nothing, then everything at once.
SPIKY = np.array([0.05] * 22 + [4.0, 0.05])


def expected(shape: np.ndarray, total: float) -> float:
    """Derived from the shape at test time: the busiest hour's share of the day."""
    return total * float(shape.max() / shape.sum())


@pytest.mark.problem
@pytest.mark.parametrize(
    ("name", "shape"), [("flat", FLAT), ("diurnal", DIURNAL), ("spiky", SPIKY)]
)
def test_it_finds_the_busiest_hour(name, shape):
    total = 1_000_000.0
    assert busy_hour_rate(shape, total) == pytest.approx(expected(shape, total), rel=1e-9), (
        f"{name}: the busy-hour rate is off. The weights are relative: turn each into its share "
        "of the whole day before you use it. Twenty-four equal weights should give the daily "
        "total spread evenly over the hours."
    )


@pytest.mark.problem
def test_a_flat_day_peaks_at_its_mean():
    """On a flat day the busiest hour is no busier than the average hour, so the two rates agree."""
    total = 24_000.0
    assert busy_hour_rate(FLAT, total) == pytest.approx(total / 24, rel=1e-9), (
        "a flat day: every hour carries the same share, so the busy-hour rate should be the daily "
        "total spread evenly over the hours. If yours is many times larger, check what you "
        "divided the weights by."
    )


@pytest.mark.problem
def test_the_weights_do_not_have_to_sum_to_anything():
    """The same shape at ten times the scale is the same shape."""
    total = 500.0
    assert busy_hour_rate(DIURNAL * 10, total) == pytest.approx(
        busy_hour_rate(DIURNAL, total), rel=1e-9
    )


def test_the_three_days_size_differently():
    """Scaffolding: three shapes, three answers, or the problem is one case repeated."""
    answers = [expected(shape, 1000.0) for shape in (FLAT, DIURNAL, SPIKY)]
    assert len({round(a, 6) for a in answers}) == 3, answers
    assert answers[2] > answers[1] > answers[0], "a spikier day must size you harder"
