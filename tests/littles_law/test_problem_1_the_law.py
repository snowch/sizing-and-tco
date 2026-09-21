"""Problem 5.1 - graded against the model's own node, which is the law written as a formula."""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate, point
from tests.littles_law.stubs import concurrency

MODEL = "models/web_service/model.yaml"
SCENARIO = "models/web_service/scenarios/reference.yaml"


@pytest.fixture(scope="module")
def evaluated():
    return evaluate(load_model(MODEL), load_scenario(SCENARIO))


@pytest.mark.problem
def test_it_agrees_with_the_model_at_the_point(evaluated):
    values = point(load_model(MODEL), load_scenario(SCENARIO))
    assert concurrency(values["peak_request_rate"], values["residence_time"]) == pytest.approx(
        values["concurrency"], rel=1e-9
    )


@pytest.mark.problem
def test_it_agrees_across_every_future(evaluated):
    """Not one case: a hundred thousand, over the whole range the model thinks is plausible."""
    mine = concurrency(evaluated.samples["peak_request_rate"], evaluated.samples["residence_time"])
    assert np.allclose(mine, evaluated.samples["concurrency"], rtol=1e-9), (
        "agreeing at the point estimate and disagreeing elsewhere usually means something was "
        "hard-coded that should have been an argument"
    )


@pytest.mark.problem
@pytest.mark.parametrize(("rate", "residence"), [(0.0, 1.0), (100.0, 0.0), (1e6, 1e-6)])
def test_the_degenerate_cases_behave(rate, residence):
    assert concurrency(rate, residence) == pytest.approx(rate * residence)


def test_the_models_node_is_the_law():
    """Scaffolding: the oracle is the law as a formula over the two quantities the reader is
    handed and nothing else, so agreeing across every future means the reader wrote the law."""
    model = load_model(MODEL)
    node = model.nodes["concurrency"]
    assert node.depends_on() == {"peak_request_rate", "residence_time"}
