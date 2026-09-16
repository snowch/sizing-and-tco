"""Problem 8.1 - a straight line fitted to a healthy system, extrapolated into a busy one.

Graded against the queueing curve the book publishes. The line is fitted on the low end, which is
the only data a system that has never been in trouble can give you.
"""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from tests.regime_changes.stubs import straight_line_forecast


@pytest.fixture(scope="module")
def curve():
    return load_result("queueing-curve")["summary"]["curve"]


@pytest.fixture(scope="module")
def known(curve):
    """What a comfortable system knows about itself: nothing above half load."""
    return [
        (row["utilisation"], row["residence_time"]) for row in curve if row["utilisation"] <= 0.5
    ]


@pytest.mark.problem
def test_the_line_fits_where_it_was_fitted(known):
    """It has to be a good line, or the problem is about a bad fit rather than about regimes."""
    at = np.array([u for u, _ in known])
    predicted = np.asarray(straight_line_forecast(known, at), dtype=float)
    actual = np.array([r for _, r in known])
    assert np.allclose(predicted, actual, rtol=0.12), (
        "the fit is poor even on its own data; this problem is about extrapolation, not about "
        "fitting"
    )


@pytest.mark.problem
def test_it_is_wrong_by_a_multiple_further_out(curve, known):
    far = [row for row in curve if row["utilisation"] >= 0.9]
    at = np.array([row["utilisation"] for row in far])
    predicted = np.asarray(straight_line_forecast(known, at), dtype=float)
    actual = np.array([row["residence_time"] for row in far])
    ratios = actual / predicted
    assert ratios.min() > 2.0, (
        f"the straight line should understate the busy end by a multiple, and it is only off by "
        f"{ratios.min():.2f}x. Check that you fitted on `known` and did not peek at the far end."
    )


@pytest.mark.problem
def test_the_error_grows_with_load(curve, known):
    at = np.array([row["utilisation"] for row in curve if row["utilisation"] >= 0.6])
    actual = np.array([row["residence_time"] for row in curve if row["utilisation"] >= 0.6])
    ratios = actual / np.asarray(straight_line_forecast(known, at), dtype=float)
    assert np.all(np.diff(ratios) > 0), (
        "a linear extrapolation into a non-linear regime gets steadily worse, never better. If "
        "yours improves somewhere, the fit is picking up curvature it should not have seen."
    )


def test_the_low_end_really_does_look_linear(known):
    """Scaffolding: the problem's premise holds — a healthy system looks well behaved.

    This is what makes the failure interesting. If the low end were visibly curved, nobody would
    fit a line to it and there would be nothing to warn anybody about.
    """
    utilisations = np.array([u for u, _ in known])
    residences = np.array([r for _, r in known])
    slope, intercept = np.polyfit(utilisations, residences, 1)
    fitted = slope * utilisations + intercept
    assert np.allclose(fitted, residences, rtol=0.12), "the low end should look nearly straight"
