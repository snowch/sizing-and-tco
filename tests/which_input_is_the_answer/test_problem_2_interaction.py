"""Problem 19.2 - the limitation of every one-at-a-time chart, measured.

The test hands the reader two bands and a way to ask the model for an output with either input,
or both, held. It names the pairs; the reader measures the gap.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from sizing import mc
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.which_input_is_the_answer.stubs import interaction_gap

#: Two inputs that meet in a product on the way to the raw data, and two that meet in a sum on
#: the way to the annual running cost and nowhere else.
INTERACTING = ("annual_growth", "index_overhead")
SEPARATE = ("electricity_price", "staff_fte")
PRODUCT, SUM = "raw_data", "annual_opex"
#: The two ends of a band: the middle eighty per cent of what an input could be.
LOW, HIGH = 0.1, 0.9


@pytest.fixture(scope="module")
def model():
    return load_model("models/web_service/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/web_service/scenarios/reference.yaml")


def swings(model, names: tuple[str, str]) -> dict[str, tuple[float, float]]:
    """Each named input, mapped to its tenth and its ninetieth percentile."""
    out = {}
    for name in names:
        shape, parameters = mc.one_shape(model.nodes[name].distribution)
        low, high = mc.SHAPES[shape](np.array([LOW, HIGH]), **parameters)
        out[name] = (float(low), float(high))
    return out


def output_at(model, scenario, output: str):
    """One output at a point: the named inputs held, everything else at its point value."""

    def at(held: dict[str, float]) -> float:
        return point(model, replace(scenario, overrides={**scenario.overrides, **held}))[output]

    return at


@pytest.mark.problem
def test_inputs_that_meet_in_a_product_interact(model, scenario):
    gap = interaction_gap(output_at(model, scenario, PRODUCT), swings(model, INTERACTING))
    assert abs(gap) > 0.02, (
        f"{INTERACTING[0]} and {INTERACTING[1]} multiply each other on the way to the raw data, so "
        f"moving both cannot be the sum of moving each - and you make the gap {gap:.1%}"
    )


@pytest.mark.problem
def test_inputs_that_only_meet_in_a_sum_do_not(model, scenario):
    gap = interaction_gap(output_at(model, scenario, SUM), swings(model, SEPARATE))
    assert abs(gap) < 0.01, (
        f"{SEPARATE[0]} and {SEPARATE[1]} are added together and nothing else, so their effects "
        f"should be exactly additive - and you make the gap {gap:.1%}"
    )


@pytest.mark.problem
def test_the_gap_is_signed(model, scenario):
    """Direction matters: a tornado can understate as well as overstate."""
    gap = interaction_gap(output_at(model, scenario, PRODUCT), swings(model, INTERACTING))
    assert gap > 0, (
        "two factors of a product swung upward together move it further than the sum of their "
        "separate moves, so this gap is positive. Zero or negative has lost the sign, or the "
        "direction of a swing."
    )


def test_both_pairs_are_still_in_the_model(model, scenario):
    """Scaffolding: the problem's two cases exist, have bands to swing, and are what it claims."""
    for name in INTERACTING + SEPARATE:
        assert name in model.nodes, f"{name} is gone; problem 19.2 needs rewriting"
        assert model.nodes[name].distribution, f"{name} has no band to swing"
        assert name not in scenario.overrides, f"the reference scenario pins {name}"
    for name in INTERACTING:
        assert name in model.ancestors(PRODUCT), name
    for name in SEPARATE:
        assert name in model.ancestors(SUM), name
