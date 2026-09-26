"""Problem 7.2 - fitting the law's three numbers from three measurements.

Graded by round trip: the test makes measurements from known coefficients, hands them over, and
checks that what comes back reproduces them. Nothing is stored and the coefficients change between
cases, so there is nothing to pattern-match.
"""

from __future__ import annotations

import math

import pytest

from tests.when_adding_servers_stops_helping.stubs import fit

#: One host's throughput, contention and crosstalk. Problem 7.3's test uses the same three fleets.
CASES = {
    "a fleet like the book's": (1220.0, 0.005, 3.7e-5),
    "heavily serialised": (400.0, 0.12, 1e-4),
    "chatty": (80.0, 0.004, 2e-3),
}

#: Host counts you could plausibly have measured at: one machine on a bench, and two fleets.
COUNTS = (1, 8, 40)


def known_throughput(hosts: float, one_host: float, contention: float, crosstalk: float) -> float:
    """The forward direction, used only to make measurements for the reader to fit."""
    return hosts * one_host / (1 + contention * (hosts - 1) + crosstalk * hosts * (hosts - 1))


def measurements(name: str) -> list[tuple[float, float]]:
    return [(float(n), known_throughput(float(n), *CASES[name])) for n in COUNTS]


def close(got: float, want: float, rel: float) -> bool:
    return math.isfinite(got) and math.isclose(got, want, rel_tol=rel)


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
def test_the_fit_recovers_the_coefficients(name):
    one_host_only = (
        "If you divided by hosts - 1, the one-host measurement makes that 0 / 0. Use it for "
        "one_host only, and take contention and crosstalk from the other two."
    )
    try:
        got = [float(value) for value in fit(measurements(name))]
    except ZeroDivisionError:
        pytest.fail(f"{name}: your fit divided by zero. {one_host_only}", pytrace=False)
    if any(math.isnan(value) for value in got):
        pytest.fail(f"{name}: your fit returned nan. {one_host_only}", pytrace=False)
    if not close(got[0], CASES[name][0], 1e-6):
        pytest.fail(
            f"{name}: one_host is wrong. One measurement is at a single host, which has nobody "
            "to contend or coordinate with.",
            pytrace=False,
        )
    for index, coefficient in ((1, "contention"), (2, "crosstalk")):
        if not close(got[index], CASES[name][index], 1e-4):
            pytest.fail(
                f"{name}: one_host is right and {coefficient} is not, so the slip is in the "
                "rearrangement. Check which way up it is: the law's denominator is the straight "
                "line divided by the measured throughput, not the other way round. Then check "
                "that contention goes with hosts - 1 and crosstalk with hosts * (hosts - 1).",
                pytrace=False,
            )


def test_three_different_counts_pin_the_answer_down():
    """Scaffolding: three different counts, one of them a single host, and every measurement
    falls short of the straight line by a different amount, so none of them repeats another."""
    assert len(set(COUNTS)) == 3 and 1 in COUNTS
    for name, (one_host, _, _) in CASES.items():
        shortfalls = {rate / (hosts * one_host) for hosts, rate in measurements(name)}
        assert len(shortfalls) == 3, name


def test_the_cases_are_not_one_case_repeated():
    """Scaffolding: every one of the three numbers differs from case to case."""
    for index in range(3):
        assert len({case[index] for case in CASES.values()}) == len(CASES)
