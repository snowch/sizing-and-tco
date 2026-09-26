"""Problem 9.1 - graded against the model's own chain, node by node."""

from __future__ import annotations

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate, point
from tests.capacity.stubs import raw_for

MODEL = "models/web_service/model.yaml"
SCENARIO = "models/web_service/scenarios/reference.yaml"


@pytest.fixture(scope="module")
def values():
    return point(load_model(MODEL), load_scenario(SCENARIO))


def diagnosis(mine: float, values) -> str:
    """What a wrong answer to the chain most likely got wrong, without saying what is right."""
    ratio = mine / values["raw_data"]
    if ratio == pytest.approx(values["record_compression"] ** 2, rel=1e-6):
        return (
            "You are out by the square of the compression ratio, so the division is upside down. "
            "Compression makes what you buy smaller."
        )
    overhead = values["index_overhead"]
    if ratio == pytest.approx((1 + overhead) / overhead, rel=1e-6):
        return (
            "The overhead is already a multiplier: 1.3 means thirty per cent more. Adding one to "
            "it buys a whole extra copy of every byte."
        )
    return (
        "The model works it out differently. Get the four cases you can do in your head right "
        "first: one term at a time, with the other three at one."
    )


@pytest.mark.problem
def test_it_agrees_with_the_model(values):
    mine = raw_for(
        values["stored_data"],
        values["replication_factor"],
        values["record_compression"],
        values["index_overhead"],
    )
    if mine != pytest.approx(values["raw_data"], rel=1e-9):
        pytest.fail(diagnosis(mine, values), pytrace=False)


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
        evaluation.samples["stored_data"],
        evaluation.point["replication_factor"],
        evaluation.samples["record_compression"],
        evaluation.samples["index_overhead"],
    )
    assert np.allclose(mine, evaluation.samples["raw_data"], rtol=1e-9), (
        "the chain agrees at the point estimates but not across every future the model drew: "
        "something in it is not a plain multiplication or division"
    )


def test_the_model_still_has_the_four_terms(values):
    """Scaffolding: the chain the problem is about has not been restructured."""
    for name in (
        "stored_data",
        "replication_factor",
        "record_compression",
        "index_overhead",
    ):
        assert name in values


def test_the_two_mistakes_get_different_messages(values):
    """Scaffolding: an upside-down division and an overhead with one added are told apart."""
    upside_down = values["raw_data"] * values["record_compression"] ** 2
    overhead = values["index_overhead"]
    one_added = values["raw_data"] * (1 + overhead) / overhead
    assert "upside down" in diagnosis(upside_down, values)
    assert "already a multiplier" in diagnosis(one_added, values)
