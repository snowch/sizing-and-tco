"""Problem 9.4 - the classification the whole book rests on, from the inside."""

from __future__ import annotations

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import check_units, point
from tests.capacity.stubs import make_it_a_cost_model


@pytest.fixture(scope="module")
def base():
    return load_model("models/web_service/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/web_service/scenarios/reference.yaml")


@pytest.mark.problem
def test_it_classifies_as_a_cost_model(base):
    converted = make_it_a_cost_model(base)
    assert converted.classification == "cost", (
        f"still a {converted.classification} model. A model is a sizing model if it has a "
        "measured node or a ceiling in it - both, here."
    )
    assert not converted.of_kind("measured") and not converted.of_kind("ceiling")


@pytest.mark.problem
def test_it_still_works(base, scenario):
    converted = make_it_a_cost_model(base)
    assert not check_units(converted)[0]
    values = point(converted, scenario)
    assert converted.outputs, "you may delete nodes; you may not delete the outputs"
    for output in converted.outputs:
        assert output in values, f"{output} no longer evaluates"


@pytest.mark.problem
def test_you_said_what_was_lost():
    """The part that is not arithmetic.

    Not graded for content - nothing here can grade a sentence. Graded for existing, because a
    model you cannot say the limits of is a model you should not hand to anybody.
    """
    doc = (make_it_a_cost_model.__doc__ or "").strip()
    assert "problem 9.4" not in doc.lower() or len(doc) > 400, (
        "write one sentence in the stub's docstring naming what the cost model can no longer "
        "tell anybody. If you cannot name it, you removed something that was doing no work."
    )


def test_the_web_service_model_is_a_sizing_model_to_begin_with(base):
    """Scaffolding: there is something to remove."""
    assert base.classification == "sizing"
    assert base.of_kind("measured") and base.of_kind("ceiling")
