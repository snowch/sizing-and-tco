"""Problem 7.1 - graded against the sweep the book publishes."""

from __future__ import annotations

import math

import numpy as np
import pytest

from bench.stamp import load_result
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.when_adding_servers_stops_helping.stubs import throughput


@pytest.fixture(scope="module")
def reference():
    values = point(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )
    return values["single_host_throughput"], values["contention"], values["crosstalk"]


@pytest.mark.problem
def test_it_reproduces_the_published_sweep(reference):
    one_host, contention, crosstalk = reference
    for row in load_result("scaling-curve")["summary"]["curve"]:
        hosts, published = row["hosts"], row["achievable_throughput"]
        mine = float(np.asarray(throughput(hosts, one_host, contention, crosstalk)))
        if not math.isfinite(mine):
            pytest.fail(f"at {hosts:.0f} hosts your formula returned {mine}", pytrace=False)
        if math.isclose(mine, published, rel_tol=1e-9):
            continue
        gap = (mine - published) / published
        where = "above" if gap > 0 else "below"
        hint = (
            "A gap this small at a few hosts means one term multiplies the wrong count: compare "
            "each term of yours with the law on the page, one at a time."
            if abs(gap) < 0.01
            else "Compare your formula with the law on the page, term by term."
        )
        pytest.fail(
            f"at {hosts:.0f} hosts your formula gives {mine:,.3f} requests per second, "
            f"{abs(gap):.3%} {where} the book's sweep. {hint}",
            pytrace=False,
        )


@pytest.mark.problem
def test_one_machine_is_just_one_machine(reference):
    one_host, contention, crosstalk = reference
    mine = float(np.asarray(throughput(1, one_host, contention, crosstalk)))
    if not math.isclose(mine, one_host, rel_tol=1e-12):
        pytest.fail(
            "at one host your formula does not give one_host back. With one machine there is "
            "nobody to contend with and nobody to coordinate with, so both terms must vanish.",
            pytrace=False,
        )


@pytest.mark.problem
def test_with_no_costs_it_is_a_straight_line():
    counts = np.array([1.0, 10.0, 100.0])
    if not np.allclose(np.asarray(throughput(counts, 50.0, 0.0, 0.0), dtype=float), counts * 50.0):
        pytest.fail(
            "with contention and crosstalk both zero, the throughput of n hosts must be n times "
            "one host's",
            pytrace=False,
        )


@pytest.mark.problem
def test_contention_alone_flattens_but_never_falls():
    """Amdahl's limit: without coordination cost the curve approaches a limit and stays below it."""
    counts = np.array([1.0, 10.0, 100.0, 1000.0, 10000.0])
    values = np.asarray(throughput(counts, 50.0, 0.05, 0.0), dtype=float)
    if not np.all(np.diff(values) > 0):
        pytest.fail("with no crosstalk the curve must never turn over", pytrace=False)
    if not math.isclose(values[-1], 50.0 / 0.05, rel_tol=0.01):
        pytest.fail(
            "with only contention, the curve must level off at one machine's throughput divided "
            "by the serial fraction, and at ten thousand hosts yours has not",
            pytrace=False,
        )


@pytest.mark.problem
def test_crosstalk_makes_it_turn_over():
    counts = np.arange(1, 600, dtype=float)
    values = np.asarray(throughput(counts, 50.0, 0.02, 0.0005), dtype=float)
    assert values.argmax() not in (0, len(counts) - 1), (
        "with coordination cost the peak has to be somewhere in the middle - that is the "
        "difference between this law and Amdahl's"
    )


def test_the_published_sweep_really_does_turn_over():
    """Scaffolding: the figure the problem is graded against has the shape the chapter claims."""
    summary = load_result("scaling-curve")["summary"]
    counts = [row["hosts"] for row in summary["curve"]]
    assert summary["peak_at_hosts"] not in (counts[0], counts[-1])
