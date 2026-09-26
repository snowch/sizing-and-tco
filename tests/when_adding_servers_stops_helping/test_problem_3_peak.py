"""Problem 7.3 - where adding machines stops helping, from the two coefficients alone.

Checked against the curve it describes: the test works out the throughput at every host count up
to a few thousand and finds where it is greatest. Nothing is stored.
"""

from __future__ import annotations

import math

import pytest

from bench.stamp import load_result
from tests.when_adding_servers_stops_helping.stubs import peak_hosts

#: Contention and crosstalk for the same three fleets as problem 7.2. One host's throughput
#: scales the whole curve and so cannot move its peak, which is why it is not here.
CASES = {
    "a fleet like the book's": (0.005, 3.7e-5),
    "heavily serialised": (0.12, 1e-4),
    "chatty": (0.004, 2e-3),
}

COUNTS = range(1, 4000)


def relative_throughput(hosts: float, contention: float, crosstalk: float) -> float:
    """The law with one host's throughput set to one, used only to find the peak by sweeping."""
    return hosts / (1 + contention * (hosts - 1) + crosstalk * hosts * (hosts - 1))


def swept_peak(contention: float, crosstalk: float) -> int:
    return max(COUNTS, key=lambda n: relative_throughput(float(n), contention, crosstalk))


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
def test_the_peak_matches_where_the_curve_turns(name):
    contention, crosstalk = CASES[name]
    predicted = float(peak_hosts(contention, crosstalk))
    if not math.isfinite(predicted):
        pytest.fail(
            f"{name}: crosstalk is above zero here, so the curve does turn over and there is a "
            "peak to find.",
            pytrace=False,
        )
    if abs(predicted - swept_peak(contention, crosstalk)) <= 1.0:
        return
    rising = relative_throughput(predicted + 1, contention, crosstalk) > relative_throughput(
        predicted, contention, crosstalk
    )
    hint = (
        " Contention is largest in this case, so if only this case fails, look for contention "
        "in your answer."
        if name == "heavily serialised"
        else ""
    )
    pytest.fail(
        f"{name}: your closed form puts the peak at {predicted:.1f} hosts, and the curve is "
        f"{'still rising' if rising else 'already falling'} there.{hint}",
        pytrace=False,
    )


@pytest.mark.problem
def test_without_coordination_there_is_no_peak():
    try:
        answer = peak_hosts(0.05, 0.0)
    except ValueError:
        return
    except NotImplementedError:
        raise
    except ZeroDivisionError:
        pytest.fail(
            "with crosstalk at zero your function divided by zero. That is the arithmetic "
            "failing, not your function saying there is no peak: check for zero crosstalk "
            "first, then raise ValueError or return an infinity.",
            pytrace=False,
        )
    except Exception as error:  # noqa: BLE001 - any other exception is the reader's to change
        pytest.fail(
            f"with crosstalk at zero your function raised {type(error).__name__}. Raise "
            "ValueError, the exception the problem names, or return an infinity.",
            pytrace=False,
        )
    if math.isfinite(answer):
        pytest.fail(
            "with no coordination cost the curve never turns over, so there is no peak. Raise "
            "ValueError or return an infinity, not a large number that looks like a peak.",
            pytrace=False,
        )


def test_the_books_own_fleet_agrees_with_its_published_peak():
    """Scaffolding: the chapter says the swept peak and the predicted one agree, and this holds
    the two stamped figures to that. Nothing of the reader's is in it."""
    summary = load_result("scaling-curve")["summary"]
    predicted = summary["predicted_peak"]
    assert abs(predicted - summary["peak_at_hosts"]) / summary["peak_at_hosts"] < 0.05, (
        "the peak the book sweeps for and the peak its coefficients predict are computed "
        "independently and have to agree"
    )


def test_the_three_cases_have_three_different_peaks():
    """Scaffolding: the problem is not one case repeated."""
    assert len({swept_peak(c, x) for c, x in CASES.values()}) == len(CASES)


def test_every_peak_is_inside_the_sweep():
    """Scaffolding: each case turns over well before the sweep ends, so a right answer is never
    graded against the end of the range; and with no crosstalk the sweep never turns over."""
    for contention, crosstalk in CASES.values():
        assert swept_peak(contention, crosstalk) < COUNTS[-1] // 2
    assert swept_peak(0.05, 0.0) == COUNTS[-1]
