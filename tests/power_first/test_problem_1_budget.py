"""Problem 15.1 - graded against the model's own power chain, run backwards."""

from __future__ import annotations

import math

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.power_first.stubs import nodes_that_fit


@pytest.fixture(scope="module")
def values():
    return point(
        load_model("models/storage_cluster/model.yaml"),
        load_scenario("models/storage_cluster/scenarios/power_first.yaml"),
    )


@pytest.mark.problem
def test_it_inverts_the_models_power_chain(values):
    """The scenario's cluster draws what it draws; that draw must buy back the same cluster."""
    mine = nodes_that_fit(values["facility_power"], values["node_power"], values["pue"])
    assert mine == int(values["nodes_purchased"]), (
        f"the power-first scenario buys {values['nodes_purchased']:.0f} machines and draws "
        f"{values['facility_power']:.1f} kW; that allocation should buy back {mine}"
    )


@pytest.mark.problem
def test_the_facility_multiplier_reduces_what_fits():
    """An inefficient building buys you fewer machines, not more."""
    efficient = nodes_that_fit(50.0, 450.0, 1.1)
    wasteful = nodes_that_fit(50.0, 450.0, 1.8)
    assert wasteful < efficient, (
        "the multiplier applies to the machines' draw. If yours is the other way up, an "
        "inefficient datacentre appears to fit more machines, which would be a remarkable "
        "property of inefficiency."
    )


@pytest.mark.problem
def test_it_rounds_down():
    """The one rounding in this book that goes the other way."""
    exact = nodes_that_fit(1.0, 100.0, 1.0)
    assert exact == 10
    assert nodes_that_fit(1.05, 100.0, 1.0) == 10, (
        "a supply that cannot be exceeded rounds down. Every other constraint in this book is a "
        "demand to be satisfied and rounds up."
    )


@pytest.mark.problem
def test_no_power_fits_nothing():
    assert nodes_that_fit(0.0, 450.0, 1.3) == 0


def test_the_scenario_is_the_one_the_problem_describes(values):
    """Scaffolding: the power-first scenario still exists and is power-bound."""
    assert values["facility_power"] == pytest.approx(50.0, abs=2.0), (
        f"the scenario draws {values['facility_power']:.1f} kW; problem 15.1 describes it as a "
        "fifty-kilowatt allocation"
    )
    assert math.isclose(values["nodes_purchased"], int(values["nodes_purchased"]))
