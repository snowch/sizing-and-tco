"""Problem 19.2 - the limitation of every one-at-a-time chart, measured."""

from __future__ import annotations

import pytest

from sizing.dsl import load_model, load_scenario
from tests.which_input_is_the_answer.stubs import interaction_gap

#: Two inputs that meet in a product, and two that do not.
INTERACTING = ("annual_growth", "metadata_overhead")
SEPARATE = ("electricity_price", "staff_fte")


@pytest.fixture(scope="module")
def model():
    return load_model("models/storage_cluster/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/storage_cluster/scenarios/reference.yaml")


@pytest.mark.problem
def test_inputs_that_meet_in_a_product_interact(model, scenario):
    gap = interaction_gap(model, scenario, "raw_capacity", *INTERACTING)
    assert abs(gap) > 0.02, (
        f"{INTERACTING[0]} and {INTERACTING[1]} multiply each other on the way to raw capacity, so "
        f"moving both cannot be the sum of moving each - and you make the gap {gap:.1%}"
    )


@pytest.mark.problem
def test_inputs_that_only_meet_in_a_sum_do_not(model, scenario):
    gap = interaction_gap(model, scenario, "annual_opex", *SEPARATE)
    assert abs(gap) < 0.01, (
        f"{SEPARATE[0]} and {SEPARATE[1]} are added together and nothing else, so their effects "
        f"should be exactly additive - and you make the gap {gap:.1%}"
    )


@pytest.mark.problem
def test_the_gap_is_signed(model, scenario):
    """Direction matters: a tornado can understate as well as overstate."""
    gap = interaction_gap(model, scenario, "raw_capacity", *INTERACTING)
    assert gap == pytest.approx(gap, abs=0), "return a signed number, not a magnitude"


def test_both_pairs_are_still_in_the_model(model):
    """Scaffolding: the problem's two cases exist and are what it claims."""
    for name in INTERACTING + SEPARATE:
        assert name in model.nodes, f"{name} is gone; problem 19.2 needs rewriting"
    assert "annual_growth" in model.ancestors("raw_capacity")
    assert "electricity_price" in model.ancestors("annual_opex")
