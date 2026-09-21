"""Problem 13.2 — sample two of the model's inputs without the model's machinery, and reproduce
the interval the book publishes for the cost they feed.

The oracle for the inputs is the model file: expected percentiles are computed from the
distribution the model declares, at test time, so editing the model changes what this problem
wants — which is the correct behaviour and the reason the stub tells you not to copy the numbers.
The oracle for the cost is the stamped result the chapter's own tables come from. The two inputs
are declared independent of everything else, so the interval is reachable before ch14.
"""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from sizing import mc
from sizing.dsl import load_model
from tests.monte_carlo.stubs import sample_two_inputs

SAMPLES = 50_000
WANTED = ("staff_fte", "fully_loaded_salary")
OUTPUT = "annual_staff_cost"
#: The tolerance is itself a sampling question. At this count a percentile of a lognormal wobbles
#: by about a per cent between seeds and an interval's ends by a little more; this is a few times
#: that, so a correct answer passes on any seed and a wrong shape does not.
TOLERANCE = 0.04


@pytest.fixture(scope="module")
def declared():
    model = load_model("models/web_service/model.yaml")
    return {name: model.nodes[name].distribution for name in WANTED}


@pytest.fixture(scope="module")
def published():
    return load_result("web_service-reference")["summary"]["nodes"][OUTPUT]["summary"]


@pytest.mark.problem
def test_all_three_are_returned(declared):
    drawn = sample_two_inputs(seed=11, samples=SAMPLES)
    assert set(drawn) == {*WANTED, OUTPUT}, f"expected keys {sorted((*WANTED, OUTPUT))}"
    for name in drawn:
        assert len(np.asarray(drawn[name])) == SAMPLES, f"{name}: wrong number of draws"


@pytest.mark.problem
@pytest.mark.parametrize("percentile", [10, 50, 90])
def test_the_percentiles_match_what_the_model_declares(declared, percentile):
    drawn = sample_two_inputs(seed=11, samples=SAMPLES)
    for name in WANTED:
        shape, parameters = mc.one_shape(declared[name])
        wanted = float(mc.SHAPES[shape](np.array([percentile / 100]), **parameters)[0])
        got = float(np.percentile(np.asarray(drawn[name], dtype=float), percentile))
        assert abs(got - wanted) < TOLERANCE * wanted, (
            f"{name}: the model declares a p{percentile} of {wanted:.4g} and your samples give "
            f"{got:.4g}. Read the distribution out of the model file rather than copying numbers."
        )


@pytest.mark.problem
@pytest.mark.parametrize("end", ["p5", "p95"])
def test_the_cost_interval_is_the_one_the_book_publishes(published, end):
    drawn = sample_two_inputs(seed=11, samples=SAMPLES)
    got = float(np.percentile(np.asarray(drawn[OUTPUT], dtype=float), float(end[1:])))
    assert abs(got - published[end]) < TOLERANCE * published[end], (
        f"the book publishes a {end} of {published[end]:,.0f} for the annual staff cost and your "
        f"draws give {got:,.0f}. The formula is the model's own; check the two shapes before the "
        "arithmetic, and the triangular's two branches before the lognormal."
    )


@pytest.mark.problem
def test_the_cost_is_worked_from_the_draws_returned():
    """The same bag, through the formula: one draw's cost comes from that draw's two inputs."""
    drawn = sample_two_inputs(seed=11, samples=SAMPLES)
    expected = np.asarray(drawn[WANTED[0]]) * np.asarray(drawn[WANTED[1]])
    assert np.allclose(np.asarray(drawn[OUTPUT], dtype=float), expected, rtol=1e-9), (
        "the cost has to come from the draws you return, draw by draw, not from a fresh bag"
    )


def test_the_model_still_declares_two_sampled_prices(declared):
    """Scaffolding: the problem's subject exists and is uncertain."""
    for name in WANTED:
        assert declared[name] is not None, (
            f"{name} no longer declares a distribution, so problem 13.2 has nothing to sample. "
            "Either the model changed or the problem needs rewriting."
        )


def test_the_cost_is_still_the_product_of_the_two_and_nothing_else_moves_them():
    """Scaffolding: the formula the reader works by hand is the model's, and the two inputs are
    declared independent, so the published interval is reachable without ch14."""
    model = load_model("models/web_service/model.yaml")
    assert model.nodes[OUTPUT].depends_on() == set(WANTED)
    for correlation in model.correlations:
        assert not {correlation["a"], correlation["b"]} & set(WANTED), correlation
