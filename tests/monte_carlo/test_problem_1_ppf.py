"""Problem 13.1 — add a distribution.

Graded against the shape's own density, integrated numerically at test time: the area under it
from the minimum up to each value the reader returns has to be the percentile they were given. No
formula for the answer appears here, and a percentile function of the wrong shape fails however
well behaved it is.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.monte_carlo.stubs import log_uniform_ppf

#: Four ranges: a decade, a wider one, one below one, and one spanning four decades.
CASES = [(1.0, 10.0), (2.0, 40.0), (0.5, 8.0), (100.0, 1_000_000.0)]


def density(x: np.ndarray, minimum: float, maximum: float) -> np.ndarray:
    """The shape's definition, straight from the problem statement."""
    return 1.0 / (x * np.log(maximum / minimum))


def area_up_to(values: np.ndarray, minimum: float, maximum: float) -> np.ndarray:
    """The area under the density from the minimum to each value, by numerical integration."""
    out = np.empty(len(values))
    for i, value in enumerate(values):
        grid = np.geomspace(minimum, value, 4000)
        out[i] = np.trapezoid(density(grid, minimum, maximum), grid)
    return out


@pytest.mark.problem
@pytest.mark.parametrize(("minimum", "maximum"), CASES)
def test_the_area_under_the_density_is_the_percentile(minimum, maximum):
    u = np.linspace(0.01, 0.99, 99)
    values = np.asarray(log_uniform_ppf(u, minimum, maximum), dtype=float)
    assert np.all(values > 0), "the shape lives on positive values only"
    areas = area_up_to(values, minimum, maximum)
    worst = float(np.max(np.abs(areas - u)))
    assert worst < 2e-3, (
        f"the area under the density up to your values misses the percentile by up to {worst:.3f}. "
        "The shape is right when the area from the minimum to the value you return is the "
        "percentile you were asked for, and this one's area is a logarithm."
    )


@pytest.mark.problem
@pytest.mark.parametrize(("minimum", "maximum"), CASES)
def test_it_stays_inside_its_bounds(minimum, maximum):
    values = np.asarray(log_uniform_ppf(np.linspace(1e-6, 1 - 1e-6, 5000), minimum, maximum))
    assert values.min() >= minimum * (1 - 1e-9) and values.max() <= maximum * (1 + 1e-9), (
        f"the shape is defined on a closed interval; nothing it produces may fall outside "
        f"[{minimum}, {maximum}]"
    )


@pytest.mark.problem
@pytest.mark.parametrize(("minimum", "maximum"), CASES)
def test_it_is_monotonic(minimum, maximum):
    values = np.asarray(log_uniform_ppf(np.linspace(0.001, 0.999, 4000), minimum, maximum))
    assert np.all(np.diff(values) >= -1e-9), (
        "a higher percentile cannot give a lower value. If this fails, the function is not a "
        "percentile function at all, whatever else it is doing right."
    )


def test_the_density_integrates_to_one():
    """Scaffolding: the definition the reader is handed is a density, so the grader is sane."""
    for minimum, maximum in CASES:
        whole = area_up_to(np.array([maximum]), minimum, maximum)[0]
        assert abs(whole - 1.0) < 1e-6, (minimum, maximum, whole)


def test_the_cases_are_not_one_case():
    """Scaffolding: the four ranges have different middles, so a constant cannot pass them all."""
    middles = {round(np.sqrt(lo * hi), 6) for lo, hi in CASES}
    assert len(middles) == len(CASES)
