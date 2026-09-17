"""Problem 12.1 — add a distribution.

Graded against the PERT distribution's own definition. The expected mean is computed from the
parameters at test time by the formula the problem statement gives, so there is no stored answer
and no way to pass this by pattern-matching.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.monte_carlo.stubs import pert_ppf

#: Three shapes with the same bounds and different opinions about the middle, plus one that is
#: nearly symmetric. A percentile function that quietly ignores `likely` passes the last and
#: fails the first two, which is the point of having all four.
CASES = [
    (0.0, 1.0, 10.0),
    (0.0, 9.0, 10.0),
    (0.0, 5.0, 10.0),
    (2.0, 3.0, 40.0),
]


def expected_mean(minimum: float, likely: float, maximum: float) -> float:
    """The PERT mean, straight from the problem statement. Derived, never stored."""
    return (minimum + 4.0 * likely + maximum) / 6.0


@pytest.mark.problem
@pytest.mark.parametrize(("minimum", "likely", "maximum"), CASES)
def test_the_mean_is_what_the_definition_says(minimum, likely, maximum):
    u = (np.arange(200_000) + 0.5) / 200_000
    values = np.asarray(pert_ppf(u, minimum, likely, maximum), dtype=float)
    wanted = expected_mean(minimum, likely, maximum)
    assert abs(values.mean() - wanted) < 0.01 * (maximum - minimum), (
        f"a PERT({minimum}, {likely}, {maximum}) has mean {wanted:.4f} by definition; these "
        f"samples average {values.mean():.4f}. The mode is weighted four times as heavily as the "
        "bounds — if your shape parameters do not encode that, the mean will come out at the "
        "midpoint instead."
    )


@pytest.mark.problem
@pytest.mark.parametrize(("minimum", "likely", "maximum"), CASES)
def test_it_stays_inside_its_bounds(minimum, likely, maximum):
    values = np.asarray(pert_ppf(np.linspace(1e-6, 1 - 1e-6, 5000), minimum, likely, maximum))
    assert values.min() >= minimum - 1e-9 and values.max() <= maximum + 1e-9, (
        "a PERT distribution is defined on a closed interval; nothing it produces may fall "
        f"outside [{minimum}, {maximum}]"
    )


@pytest.mark.problem
@pytest.mark.parametrize(("minimum", "likely", "maximum"), CASES)
def test_it_is_monotonic(minimum, likely, maximum):
    values = np.asarray(pert_ppf(np.linspace(0.001, 0.999, 4000), minimum, likely, maximum))
    assert np.all(np.diff(values) >= -1e-9), (
        "a higher percentile cannot give a lower value. If this fails, the function is not a "
        "percentile function at all, whatever else it is doing right."
    )


def test_the_target_is_real_and_distinguishes_the_cases():
    """Scaffolding: the problem has an answer, and the four cases do not share it.

    Unmarked, so CI keeps checking that this problem is answerable. A problem whose cases all
    have the same target is not a problem.
    """
    means = [expected_mean(*case) for case in CASES]
    assert len({round(m, 6) for m in means}) == len(CASES), (
        f"the four cases must have different means or the problem is trivial: {means}"
    )
    for minimum, likely, maximum in CASES:
        assert minimum <= likely <= maximum
