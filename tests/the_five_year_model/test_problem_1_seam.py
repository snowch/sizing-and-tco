"""Problem 18.1 - what a point estimate costs at the seam between two models.

The two arrays are the two sides of the seam, evaluated here from the models' own reference
scenarios. The intervals the reader is graded against are computed from them at test time, from
the same arithmetic the problem describes, and are never stored.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.the_five_year_model.stubs import joined_interval

#: The quantity one model produces and the other one buys.
UPSTREAM = "cost_per_stored_tb_month"
DOWNSTREAM = "known_stored"


@pytest.fixture(scope="module")
def price():
    """The web service's cost per stored terabyte-month, as the model computed it."""
    return evaluate(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    ).samples[UPSTREAM]


@pytest.fixture(scope="module")
def stored():
    """The observability platform's stored terabytes, as the model computed them."""
    return evaluate(
        load_model("models/observability/model.yaml"),
        load_scenario("models/observability/scenarios/reference.yaml"),
    ).samples[DOWNSTREAM]


def joined(stored: np.ndarray, price: np.ndarray, use_distribution: bool) -> np.ndarray:
    """The test's own join: the price as it was drawn, or the price as one written-down number."""
    carried = price if use_distribution else float(np.median(price))
    return stored * carried


def mine(stored, price, use_distribution) -> tuple[float, float]:
    low, high = joined_interval(stored, price, use_distribution)
    return float(low), float(high)


@pytest.mark.problem
def test_the_distribution_carried_across_gives_this_interval(stored, price):
    """Draw by draw: the i-th stored figure priced at the i-th price."""
    expected = mc.interval(joined(stored, price, True))
    low, high = mine(stored, price, True)
    assert (low, high) == pytest.approx(expected, rel=1e-6), (
        f"with the price carried across as a distribution the interval is {expected[0]:,.0f} to "
        f"{expected[1]:,.0f}, and yours is {low:,.0f} to {high:,.0f}. Multiply the two arrays "
        "element by element and take the 5th and 95th percentiles of the product."
    )


@pytest.mark.problem
def test_the_median_carried_across_gives_this_interval(stored, price):
    """One number crosses the seam: the upstream median, treated downstream as known."""
    expected = mc.interval(joined(stored, price, False))
    low, high = mine(stored, price, False)
    assert (low, high) == pytest.approx(expected, rel=1e-6), (
        f"with the price carried across as its median the interval is {expected[0]:,.0f} to "
        f"{expected[1]:,.0f}, and yours is {low:,.0f} to {high:,.0f}. Price every stored figure "
        "at the one median price, and take the 5th and 95th percentiles of that."
    )


@pytest.mark.problem
def test_the_point_estimate_narrows_the_answer(stored, price):
    """The finding. Writing a number down between two models throws away what it was worth."""
    wide_low, wide_high = mine(stored, price, True)
    narrow_low, narrow_high = mine(stored, price, False)
    assert (narrow_high - narrow_low) < (wide_high - wide_low), (
        "handing a median across the seam should give a narrower interval than handing the "
        "distribution, because the downstream model no longer knows the upstream figure was "
        "uncertain"
    )


@pytest.mark.problem
def test_the_narrowing_is_substantial(stored, price):
    wide = mine(stored, price, True)
    narrow = mine(stored, price, False)
    shrinkage = 1 - (narrow[1] - narrow[0]) / (wide[1] - wide[0])
    assert shrinkage > 0.1, (
        f"the interval only narrows by {shrinkage:.1%}. Check that the price is reaching the "
        "product as a distribution in one case and as a single number in the other."
    )


def test_the_two_models_are_talking_about_the_same_unit():
    """Scaffolding: the seam the problem is about is a real one.

    If these units ever diverge, the two models have stopped describing the same trade and this
    chapter needs rewriting rather than the test.
    """
    upstream = load_model("models/web_service/model.yaml").nodes[UPSTREAM]
    downstream = load_model("models/observability/model.yaml").nodes["storage_price"]
    assert upstream.unit == downstream.unit, (upstream.unit, downstream.unit)


def test_the_two_sides_of_the_seam_line_up(stored, price):
    """Scaffolding: a draw-by-draw join is possible, and there is something to carry.

    The two reference scenarios draw the same number of samples, both sides are positive, and the
    upstream price is wide enough that a summary of it loses something worth measuring.
    """
    assert stored.shape == price.shape, (stored.shape, price.shape)
    assert np.all(stored > 0) and np.all(price > 0)
    low, high = mc.interval(price)
    assert high / low > 2.0, f"a p5 to p95 of {low:.2f} to {high:.2f} is not a wide figure"


def test_the_seam_moves_the_doubt_and_not_the_answer(stored, price):
    """Scaffolding: the premise of the chapter's section on the seam.

    The headline number stays roughly where it was and only the doubt around it goes, which is
    why the point estimate survives review. Medians, not the midpoints of the intervals: a
    midpoint moves whenever a tail does, and this is a claim about the answer.
    """
    wide = float(np.median(joined(stored, price, True)))
    narrow = float(np.median(joined(stored, price, False)))
    assert abs(narrow - wide) / wide < 0.1, (wide, narrow)


def test_the_dsl_has_no_node_kind_for_this():
    """Scaffolding: the gap the problem asks the reader to notice is really there.

    If a kind for "a distribution from another model" is ever added, this test fails and the
    problem's last paragraph needs rewriting - which is the correct outcome, not a nuisance.
    """
    from sizing.dsl import KINDS

    assert set(KINDS) == {"input", "derived", "measured", "ceiling"}, sorted(KINDS)
