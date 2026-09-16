"""Problem 14.3 — find the missing node.

The oracle is an observation the model does not contain. It is a fixture for this exercise, not a
measurement the book publishes: it lives here rather than under ``bench/results/`` precisely so
that it can never be mistaken for one.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc
from sizing.dsl import Input, load_model, load_scenario
from sizing.evaluate import evaluate
from tests.correlation_and_convergence.stubs import repair_the_model

FIXTURE = "tests/correlation_and_convergence/fixtures/model.yaml"
SCENARIO = "tests/correlation_and_convergence/fixtures/scenarios/reference.yaml"

#: What the service actually cost, per month, averaged over twelve invoices. Invented for this
#: exercise. The model as shipped cannot reach it, and widening its inputs is not allowed to be
#: the way you get there.
OBSERVED_MONTHLY = 38_200.0


@pytest.fixture(scope="module")
def original():
    return load_model(FIXTURE)


@pytest.fixture(scope="module")
def scenario():
    return load_scenario(SCENARIO)


def _interval(model, scenario):
    return mc.interval(evaluate(model, scenario).samples["monthly_cost"])


@pytest.mark.problem
def test_the_repair_adds_a_node(original):
    repaired = repair_the_model(original)
    added = set(repaired.nodes) - set(original.nodes)
    assert added, (
        "the repair has to add something. A model that disagrees with an invoice is not fixed by "
        "adjusting the numbers in it."
    )
    for name in sorted(added):
        node = repaired.nodes[name]
        assert node.unit, f"{name}: every node declares a unit"
        if isinstance(node, Input):
            assert node.provenance and node.provenance.source.strip(), (
                f"{name}: every input says where it came from, including one you have just "
                "invented — especially one you have just invented."
            )


@pytest.mark.problem
def test_no_existing_input_was_widened(original):
    repaired = repair_the_model(original)
    for name, node in original.nodes.items():
        if not isinstance(node, Input) or node.distribution is None:
            continue
        after = repaired.nodes[name]
        assert isinstance(after, Input) and after.distribution is not None
        was = _span(node.distribution)
        now = _span(after.distribution)
        assert now <= was * 1.0001, (
            f"{name}: its p10-to-p90 span went from {was:.4g} to {now:.4g}. Making a model vaguer "
            "until it stops contradicting the evidence is not a repair — it is the same error "
            "with a wider error bar on it."
        )


def _span(distribution: dict) -> float:
    shape, parameters = mc.one_shape(distribution)
    low, high = mc.SHAPES[shape](np.array([0.1, 0.9]), **parameters)
    return float(high - low)


@pytest.mark.problem
def test_the_observation_lands_inside_the_interval(original, scenario):
    repaired = repair_the_model(original)
    low, high = _interval(repaired, scenario)
    assert low <= OBSERVED_MONTHLY <= high, (
        f"the repaired model's 90% interval is {low:,.0f} to {high:,.0f} and the service actually "
        f"cost {OBSERVED_MONTHLY:,.0f} a month. Still outside, so the structure is still wrong."
    )


def test_the_fixture_really_is_wrong(original, scenario):
    """Scaffolding: the problem exists.

    Unmarked, so CI keeps checking that the fixture still contradicts the observation. If a change
    to the fixture made this pass, the problem has quietly solved itself and needs rewriting.
    """
    low, high = _interval(original, scenario)
    assert high < OBSERVED_MONTHLY, (
        f"the fixture's interval is {low:,.0f} to {high:,.0f}, which already contains the observed "
        f"{OBSERVED_MONTHLY:,.0f}. There is nothing for the reader to find."
    )
