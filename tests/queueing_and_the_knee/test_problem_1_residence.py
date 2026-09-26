"""Problem 6.1 - graded against the curve the book publishes, not against a formula in a file."""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from tests.queueing_and_the_knee.stubs import residence_time

#: What a failure at a full system says, in both tests that check it. The model clamps and this
#: function may not, and a reader who copied the model's clamp needs to be told why.
NO_CLAMP = (
    "The model can clamp because its ceiling watches the unclamped utilisation and reports "
    "over. This function has nothing beside it, so a clamped answer reaches whoever calls it "
    "as an ordinary number."
)


@pytest.fixture(scope="module")
def curve():
    return load_result("queueing-curve")["summary"]["curve"]


def over_an_array(busy: np.ndarray) -> np.ndarray:
    """The reader's function over an array of utilisations, or a failure that says why not."""
    try:
        values = np.asarray(residence_time(1.0, busy), dtype=float)
    except ValueError as error:
        raise AssertionError(
            f"given an array of utilisations, residence_time raised: {error}. An `if` on the "
            "utilisation asks one question of the whole array. Handle a full system element by "
            "element, so that each utilisation gets its own answer."
        ) from None
    assert values.shape == busy.shape, (
        f"{busy.size} utilisations went in and an answer of shape {values.shape} came out. "
        "Return one residence time for each utilisation."
    )
    return values


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
def test_it_takes_an_array_of_utilisations():
    """The figure in the chapter is a sweep, and a sweep is an array."""
    busy = np.array([0.0, 0.3, 0.6, 0.9])
    values = over_an_array(busy)
    one_at_a_time = [float(np.asarray(residence_time(1.0, float(u)))) for u in busy]
    assert values == pytest.approx(one_at_a_time, rel=1e-12), (
        "an array of utilisations and the same utilisations one at a time give different "
        "answers. Each element should get the answer it would get on its own."
    )


@pytest.mark.problem
def test_it_is_monotonic_and_convex():
    """Busier is never faster, and each extra per cent of load costs more than the last."""
    values = over_an_array(np.linspace(0.0, 0.95, 200))
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
    assert not np.isfinite(answer), (
        "at a utilisation of one there is nothing left of the system to do your work. Return an "
        "infinity or raise; do not return a finite number, of either sign, that somebody can put "
        f"in a slide. {NO_CLAMP}"
    )


@pytest.mark.problem
def test_a_full_system_is_not_a_finite_number_in_an_array_either():
    """numpy does not raise on a division by zero, so the array route has to say it too."""
    # Below one, an array has to work: a raise here is the `if` fault, not a decision about a
    # full system, and test_it_takes_an_array_of_utilisations says so.
    over_an_array(np.array([0.5, 0.6]))
    try:
        values = np.asarray(residence_time(1.0, np.array([0.5, 1.0, 1.2])), dtype=float)
    except (ZeroDivisionError, ValueError):
        return
    assert np.isfinite(values[0])
    assert not np.any(np.isfinite(values[1:])), (
        "past a utilisation of one the formula describes nothing. An array of utilisations has "
        f"to come back non-finite where it crosses one, not negative and not capped. {NO_CLAMP}"
    )


def test_the_published_curve_actually_bends(curve):
    """Scaffolding: the figure the problem is graded against is the shape the chapter claims."""
    inflations = [row["inflation"] for row in curve]
    assert inflations == sorted(inflations)
    assert inflations[-1] > 10 * inflations[0], "a curve that does not bend teaches nothing"


def test_an_array_can_say_infinity_without_raising():
    """Scaffolding: the array route is answerable without raising, because numpy can put an
    infinity in one element and ordinary numbers in the others."""
    with np.errstate(divide="ignore"):
        values = np.float64(1.0) / (1.0 - np.array([0.5, 1.0]))
    assert np.isfinite(values[0]) and np.isinf(values[1])
