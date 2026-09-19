"""Problem 18.1 - the quantity one model produces and the other one buys."""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.the_five_year_model.stubs import price_from_web_service


@pytest.fixture(scope="module")
def reference():
    return evaluate(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    ).samples["cost_per_stored_tb_month"]


@pytest.mark.problem
def test_it_is_the_whole_distribution(reference):
    mine = np.asarray(price_from_web_service(), dtype=float)
    assert mine.ndim == 1 and mine.size == reference.size, (
        f"expected {reference.size:,} samples and got {mine.size:,}. A summary is not a "
        "distribution, and handing one across a seam is what 18.2 is about."
    )


@pytest.mark.problem
def test_it_is_the_right_quantity(reference):
    mine = np.asarray(price_from_web_service(), dtype=float)
    assert np.allclose(np.sort(mine), np.sort(reference), rtol=1e-9), (
        "these are not the same values. Read cost_per_stored_tb_month out of the web service model's "
        "reference scenario rather than recomputing it."
    )


@pytest.mark.problem
def test_it_is_wide_enough_to_matter(reference):
    """If the upstream figure were near-certain there would be nothing to carry."""
    low, high = np.percentile(np.asarray(price_from_web_service(), dtype=float), [5, 95])
    assert high / low > 2.0, f"a p5 to p95 of {low:.2f} to {high:.2f} is not a narrow figure"


def test_the_two_models_are_talking_about_the_same_unit():
    """Scaffolding: the seam the problem is about is a real one.

    If these units ever diverge, the two models have stopped describing the same trade and this
    chapter needs rewriting rather than the test.
    """
    upstream = load_model("models/web_service/model.yaml").nodes["cost_per_stored_tb_month"]
    downstream = load_model("models/observability/model.yaml").nodes["storage_price"]
    assert upstream.unit == downstream.unit, (upstream.unit, downstream.unit)
