"""Problems 7.2 and 7.3 - fitting the coefficients, and finding the peak they imply.

Graded by round trip: the test generates measurements from known coefficients, hands them over,
and checks what comes back reproduces them. Nothing is stored and the coefficients change between
cases, so there is nothing to pattern-match.
"""

from __future__ import annotations

import math

import pytest

from bench.stamp import load_result
from tests.when_adding_servers_stops_helping.stubs import fit, peak_hosts

CASES = {
    "the book's fleet": (1220.0, 0.005, 3.7e-5),
    "heavily serialised": (400.0, 0.12, 1e-4),
    "chatty": (80.0, 0.004, 2e-3),
}


def known_throughput(hosts: float, one_host: float, contention: float, crosstalk: float) -> float:
    """The forward direction, used only to make measurements for the reader to fit."""
    return hosts * one_host / (1 + contention * (hosts - 1) + crosstalk * hosts * (hosts - 1))


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
def test_the_fit_recovers_the_coefficients(name):
    one_host, contention, crosstalk = CASES[name]
    # Three measurements, at counts somebody could plausibly have run.
    measurements = [
        (float(n), known_throughput(float(n), one_host, contention, crosstalk)) for n in (1, 8, 40)
    ]
    got = fit(measurements)
    assert got[0] == pytest.approx(one_host, rel=1e-6), f"{name}: one_host"
    assert got[1] == pytest.approx(contention, rel=1e-4), f"{name}: contention"
    assert got[2] == pytest.approx(crosstalk, rel=1e-4), f"{name}: crosstalk"


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
def test_the_peak_matches_where_the_curve_actually_turns(name):
    _, contention, crosstalk = CASES[name]
    predicted = peak_hosts(contention, crosstalk)
    # Search for the real peak, so the closed form is checked against the thing it describes.
    counts = range(1, 4000)
    swept = max(counts, key=lambda n: known_throughput(float(n), 1.0, contention, crosstalk))
    assert abs(predicted - swept) <= 1.0, (
        f"{name}: the closed form says {predicted:.1f} and sweeping finds {swept}"
    )


@pytest.mark.problem
def test_without_coordination_there_is_no_peak():
    answer = peak_hosts(0.05, 0.0)
    assert not math.isfinite(answer) or answer > 1e9, (
        "with no coordination cost the curve never turns over. The honest answer is that there is "
        "no peak, not a large number that looks like one."
    )


@pytest.mark.problem
def test_the_books_own_fleet_agrees_with_its_published_peak():
    summary = load_result("scaling-curve")["summary"]
    predicted = summary["predicted_peak"]
    assert abs(predicted - summary["peak_at_hosts"]) / summary["peak_at_hosts"] < 0.2, (
        "the peak the book sweeps for and the peak its coefficients predict are computed "
        "independently and have to agree"
    )


def test_the_three_cases_have_three_different_peaks():
    """Scaffolding: the problem is not one case repeated."""
    peaks = [
        max(range(1, 4000), key=lambda n: known_throughput(float(n), 1.0, c, x))
        for _, c, x in CASES.values()
    ]
    assert len(set(peaks)) == 3, peaks
