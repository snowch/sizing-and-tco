"""Problem 8.1 - graded against the model's own chain, node by node."""

from __future__ import annotations

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate, point
from tests.capacity.stubs import raw_for

MODEL = "models/storage_cluster/model.yaml"
SCENARIO = "models/storage_cluster/scenarios/reference.yaml"


@pytest.fixture(scope="module")
def values():
    return point(load_model(MODEL), load_scenario(SCENARIO))


@pytest.mark.problem
def test_it_agrees_with_the_model(values):
    mine = raw_for(
        values["usable_capacity"],
        values["replication_factor"],
        values["object_compression"],
        values["metadata_overhead"],
    )
    assert mine == pytest.approx(values["raw_capacity"], rel=1e-9), (
        f"the model makes {values['raw_capacity']:,.0f} TB of it and you make {mine:,.0f}. If you "
        "are out by roughly the square of the compression ratio, the division is upside down."
    )


@pytest.mark.problem
def test_the_cases_you_can_do_in_your_head():
    assert raw_for(100.0, 1.0, 1.0, 1.0) == pytest.approx(100.0), "nothing applied, nothing changes"
    assert raw_for(100.0, 3.0, 1.0, 1.0) == pytest.approx(300.0), "three copies cost three times"
    assert raw_for(100.0, 1.0, 2.0, 1.0) == pytest.approx(50.0), "compression halves what you buy"
    assert raw_for(100.0, 1.0, 1.0, 1.1) == pytest.approx(110.0), "overhead is a surcharge"


@pytest.mark.problem
def test_compression_helps_and_replication_hurts():
    """The signs, which are the half of this that is worth getting right."""
    assert raw_for(100.0, 3.0, 4.0, 1.0) < raw_for(100.0, 3.0, 2.0, 1.0)
    assert raw_for(100.0, 4.0, 2.0, 1.0) > raw_for(100.0, 3.0, 2.0, 1.0)


@pytest.mark.problem
def test_it_holds_across_the_whole_sampled_range():
    evaluation = evaluate(load_model(MODEL), load_scenario(SCENARIO))
    import numpy as np

    mine = raw_for(
        evaluation.samples["usable_capacity"],
        evaluation.point["replication_factor"],
        evaluation.samples["object_compression"],
        evaluation.samples["metadata_overhead"],
    )
    assert np.allclose(mine, evaluation.samples["raw_capacity"], rtol=1e-9)


def test_the_model_still_has_the_four_terms(values):
    """Scaffolding: the chain the problem is about has not been restructured."""
    for name in (
        "usable_capacity",
        "replication_factor",
        "object_compression",
        "metadata_overhead",
    ):
        assert name in values
