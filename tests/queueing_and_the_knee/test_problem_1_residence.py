"""Problem 6.1 - graded against the curve the book publishes, not against a formula in a file."""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from tests.queueing_and_the_knee.stubs import residence_time


@pytest.fixture(scope="module")
def curve():
    return load_result("queueing-curve")["summary"]["curve"]


@pytest.mark.problem
def test_it_reproduces_the_published_curve(curve):
    """Every row of the figure in the chapter, from the reader's own function."""
    for row in curve:
        # The service time is whatever the model's own row implies: residence at this utilisation
        # divided by the inflation it reports. Derived at test time, so nothing is stored here.
        service = row["residence_time"] / row["inflation"]
        mine = float(np.asarray(residence_time(service, row["utilisation"])))
        assert mine == pytest.approx(row["residence_time"], rel=1e-9), (
            f"at {row['utilisation']:.0%} busy the book's curve says {row['residence_time']:.4f}s "
            f"and your formula says {mine:.4f}s"
        )


@pytest.mark.problem
def test_an_idle_system_costs_only_the_work():
    assert float(np.asarray(residence_time(0.01, 0.0))) == pytest.approx(0.01)


@pytest.mark.problem
def test_it_is_monotonic_and_convex():
    """Busier is never faster, and each extra per cent of load costs more than the last."""
    values = np.asarray(residence_time(1.0, np.linspace(0.0, 0.95, 200)), dtype=float)
    steps = np.diff(values)
    assert np.all(steps >= 0), "a busier system is never faster"
    assert np.all(np.diff(steps) >= -1e-12), (
        "each extra per cent of utilisation must cost more than the last - if it does not, the "
        "formula is not the one this chapter is about"
    )


@pytest.mark.problem
@pytest.mark.parametrize("busy", [1.0, 1.2])
def test_a_full_system_is_not_a_finite_number(busy):
    try:
        answer = float(np.asarray(residence_time(1.0, busy)))
    except (ZeroDivisionError, ValueError):
        return
    assert not np.isfinite(answer) or answer < 0, (
        "at a utilisation of one there is nothing left of the system to do your work. Return an "
        "infinity or raise; do not return a large finite number that somebody can put in a slide."
    )


def test_the_published_curve_actually_bends(curve):
    """Scaffolding: the figure the problem is graded against is the shape the chapter claims."""
    inflations = [row["inflation"] for row in curve]
    assert inflations == sorted(inflations)
    assert inflations[-1] > 10 * inflations[0], "a curve that does not bend teaches nothing"
