"""Problem 7.1 - graded against the sweep the book publishes."""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.when_adding_servers_stops_helping.stubs import throughput


@pytest.fixture(scope="module")
def reference():
    values = point(
        load_model("models/service_tier/model.yaml"),
        load_scenario("models/service_tier/scenarios/reference.yaml"),
    )
    return values["single_node_throughput"], values["contention"], values["crosstalk"]


@pytest.mark.problem
def test_it_reproduces_the_published_sweep(reference):
    one_node, contention, crosstalk = reference
    for row in load_result("scaling-curve")["summary"]["curve"]:
        mine = float(np.asarray(throughput(row["nodes"], one_node, contention, crosstalk)))
        assert mine == pytest.approx(row["achievable_throughput"], rel=1e-9), (
            f"at {row['nodes']:.0f} nodes the book's sweep says "
            f"{row['achievable_throughput']:,.0f} and your formula says {mine:,.0f}"
        )


@pytest.mark.problem
def test_one_machine_is_just_one_machine(reference):
    one_node, contention, crosstalk = reference
    assert float(np.asarray(throughput(1, one_node, contention, crosstalk))) == pytest.approx(
        one_node, rel=1e-12
    ), "with one machine there is nobody to contend with and nobody to coordinate with"


@pytest.mark.problem
def test_with_no_costs_it_is_a_straight_line():
    counts = np.array([1.0, 10.0, 100.0])
    assert np.allclose(np.asarray(throughput(counts, 50.0, 0.0, 0.0), dtype=float), counts * 50.0)


@pytest.mark.problem
def test_contention_alone_flattens_but_never_falls():
    """Amdahl's ceiling: without coordination cost the curve approaches a limit and stays."""
    counts = np.array([1.0, 10.0, 100.0, 1000.0, 10000.0])
    values = np.asarray(throughput(counts, 50.0, 0.05, 0.0), dtype=float)
    assert np.all(np.diff(values) > 0), "with no crosstalk the curve must never turn over"
    assert values[-1] == pytest.approx(50.0 / 0.05, rel=0.01), (
        "with only contention the ceiling is one machine's throughput over the serial fraction"
    )


@pytest.mark.problem
def test_crosstalk_makes_it_turn_over():
    counts = np.arange(1, 600, dtype=float)
    values = np.asarray(throughput(counts, 50.0, 0.02, 0.0005), dtype=float)
    assert values.argmax() not in (0, len(counts) - 1), (
        "with coordination cost the peak has to be somewhere in the middle - that is the whole "
        "difference between this law and Amdahl's"
    )


def test_the_published_sweep_really_does_turn_over():
    """Scaffolding: the figure the problem is graded against has the shape the chapter claims."""
    summary = load_result("scaling-curve")["summary"]
    counts = [row["nodes"] for row in summary["curve"]]
    assert summary["peak_at_nodes"] not in (counts[0], counts[-1])
