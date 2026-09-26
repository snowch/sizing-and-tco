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


@pytest.fixture(scope="module")
def at_the_point():
    return point(load_model(MODEL), load_scenario(SCENARIO))


def agrees_at_the_point(law, values) -> bool:
    """Whether a function gives the model's own answer at the point estimate. Never raises: a
    function that fails on a single number has not agreed, and the point test says why."""
    try:
        return bool(
            np.isclose(
                law(values["peak_request_rate"], values["residence_time"]),
                values["concurrency"],
                rtol=1e-9,
            )
        )
    except Exception:
        return False


@pytest.mark.problem
def test_it_agrees_with_the_model_at_the_point(at_the_point):
    values = at_the_point
    assert concurrency(values["peak_request_rate"], values["residence_time"]) == pytest.approx(
        values["concurrency"], rel=1e-9
    )


@pytest.mark.problem
def test_it_agrees_across_every_future(evaluated, at_the_point):
    """Not one case: a hundred thousand, over the whole range the model thinks is plausible."""
    mine = concurrency(evaluated.samples["peak_request_rate"], evaluated.samples["residence_time"])
    assert np.allclose(mine, evaluated.samples["concurrency"], rtol=1e-9), (
        "agreeing at the point estimate and disagreeing elsewhere usually means something was "
        "hard-coded that should have been an argument"
        if agrees_at_the_point(concurrency, at_the_point)
        else "this is wrong at the point estimate as well, so fix that test first: one mistake "
        "is failing both"
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


def test_both_messages_for_every_future_can_be_reached(evaluated, at_the_point):
    """Scaffolding: the every-future test chooses its message on whether the point test would
    pass. A function that returns the model's point value whatever it is handed must agree at the
    point and disagree across the futures, or the hard-coded message is never seen; and a
    function that divides must disagree at the point, or the other one never is. The fixed value
    comes from the model at test time, like every expected value here."""
    fixed = at_the_point["concurrency"]

    def hard_coded(rate, residence):
        return fixed

    assert agrees_at_the_point(hard_coded, at_the_point)
    assert not np.allclose(
        hard_coded(evaluated.samples["peak_request_rate"], evaluated.samples["residence_time"]),
        evaluated.samples["concurrency"],
    )
    assert not agrees_at_the_point(lambda rate, residence: rate / residence, at_the_point)
