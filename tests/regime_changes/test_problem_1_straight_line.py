"""Problem 8.1 - a straight line fitted to a healthy system, extrapolated into a busy one.

Graded against the queueing curve the book publishes. The line is fitted on the low end, which is
the only data a system that has never been in trouble can give you.
"""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from tests.regime_changes.stubs import straight_line_forecast

#: Evenly spaced loads on the busy side, where the test asks whether the forecast bends. A
#: straight line's steps between them are all the same size; anything that curves has steps that
#: differ.
EVENLY_SPACED = (0.6, 0.7, 0.8, 0.9)


@pytest.fixture(scope="module")
def curve():
    return load_result("queueing-curve")["summary"]["curve"]


@pytest.fixture(scope="module")
def known(curve):
    """What a comfortable system knows about itself: nothing above half load."""
    return [
        (row["utilisation"], row["residence_time"]) for row in curve if row["utilisation"] <= 0.5
    ]


def bends(values: np.ndarray) -> bool:
    """Whether a run of values at evenly spaced loads curves, rather than climbing in equal steps.

    Written without fitting anything, so that the method the problem asks for is not in the file
    it ships with.
    """
    steps = np.diff(values)
    return bool(np.ptp(steps) > 1e-6 * max(float(np.abs(steps).max()), 1e-12))


@pytest.mark.problem
def test_the_line_fits_where_it_was_fitted(known):
    """It has to be a good line, or the problem is about a bad fit rather than about regimes."""
    at = np.array([u for u, _ in known])
    predicted = np.asarray(straight_line_forecast(known, at), dtype=float)
    actual = np.array([r for _, r in known])
    fits = bool(np.allclose(predicted, actual, rtol=0.12))
    assert fits, (
        "the fit is poor even on its own data; this problem is about extrapolation, not about "
        "fitting"
    )


@pytest.mark.problem
def test_it_is_a_straight_line(known):
    """The problem asks what a chain of multiplications predicts, and that is a straight line."""
    predicted = np.asarray(straight_line_forecast(known, np.array(EVENLY_SPACED)), dtype=float)
    bent = bends(predicted)
    assert not bent, (
        "your forecast bends: at evenly spaced loads it does not climb in equal steps, so it is "
        "not a straight line. If you fitted ch06's division, you have the right model, and it "
        "follows the curve; that is ch06's lesson, not a mistake. This problem asks what a "
        "straight line, the shape a chain of multiplications gives, predicts out there."
    )


@pytest.mark.problem
def test_it_is_wrong_by_a_multiple_further_out(curve, known):
    far = [row for row in curve if row["utilisation"] >= 0.9]
    at = np.array([row["utilisation"] for row in far])
    predicted = np.asarray(straight_line_forecast(known, at), dtype=float)
    actual = np.array([row["residence_time"] for row in far])
    wrong_by_a_multiple = bool((actual / predicted).min() > 2.0)
    assert wrong_by_a_multiple, (
        "a straight line through the points in `known` falls short of the busy end by a "
        "multiple, and this forecast does not. If the straight-line test above fails too, start "
        "there. If it passes, check that your line is fitted to `known` and to nothing else."
    )


@pytest.mark.problem
def test_the_error_grows_with_load(curve, known):
    at = np.array([row["utilisation"] for row in curve if row["utilisation"] >= 0.6])
    actual = np.array([row["residence_time"] for row in curve if row["utilisation"] >= 0.6])
    ratios = actual / np.asarray(straight_line_forecast(known, at), dtype=float)
    widening = bool(np.all(np.diff(ratios) > 0))
    assert widening, (
        "the curve pulls further ahead of a straight line with every step of load. Here the gap "
        "stops widening somewhere, which only a forecast that bends with the curve can do: see "
        "the straight-line test above."
    )


def test_the_low_end_really_does_look_linear(known):
    """Scaffolding: the problem's premise holds — a healthy system looks well behaved.

    This is what makes the failure interesting. If the low end were visibly curved, nobody would
    fit a line to it and there would be nothing to warn anybody about. Stated without fitting a
    line, so that the method the problem asks for is not written in the file it ships with: no
    step steepens much on the step before it, and the whole low end rises by less than a factor
    of two.
    """
    utilisations = np.array([u for u, _ in known])
    residences = np.array([r for _, r in known])
    slopes = np.diff(residences) / np.diff(utilisations)
    assert np.all(slopes[1:] / slopes[:-1] < 1.5), "the low end should look nearly straight"
    assert residences[-1] < 2.0 * residences[0], "the low end should rise gently"


def test_the_straight_line_check_tells_a_line_from_the_curve(curve):
    """Scaffolding: the bend check can fail. The published curve, read at the same evenly spaced
    loads, bends; the same loads drawn as a straight line do not. Without this, the straight-line
    test could pass a forecast that follows the curve."""
    at_the_loads = {round(row["utilisation"], 6): row["residence_time"] for row in curve}
    missing = [u for u in EVENLY_SPACED if u not in at_the_loads]
    assert not missing, f"the published curve has no row at {missing}; the check reads it there"
    assert bends(np.array([at_the_loads[u] for u in EVENLY_SPACED])), (
        "the curve should bend at these loads"
    )
    assert not bends(np.array(EVENLY_SPACED)), "a straight run of values should not count as bent"
