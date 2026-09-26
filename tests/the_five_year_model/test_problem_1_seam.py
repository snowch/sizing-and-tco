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


def where_it_is_off(yours: tuple[float, float], expected: tuple[float, float]) -> str:
    """Which end of the reader's interval is off, and which way, without saying where it belongs.

    A message that printed the expected interval would hand the reader both joins, and so the
    chapter's finding, after one wrong attempt.
    """
    said = []
    for end, got, want in zip(("low", "high"), yours, expected, strict=False):
        if not np.isfinite(got):
            said.append(f"the {end} end is not a number")
        elif got != pytest.approx(want, rel=1e-6):
            said.append(f"the {end} end is too {'low' if got < want else 'high'}")
    return " and ".join(said)


def how_much_narrower(wide: tuple[float, float], narrow: tuple[float, float]) -> float:
    """The fraction of the wide interval that the narrow one loses.

    A wide interval with no width has nothing to lose, and dividing by it would stop the test with
    a ZeroDivisionError instead of a message the reader can act on.
    """
    width = wide[1] - wide[0]
    assert width > 0, (
        "your interval with the price carried across as a distribution has no width, so there is "
        "nothing for the other join to narrow. Its high end must be above its low end."
    )
    return 1 - (narrow[1] - narrow[0]) / width


@pytest.mark.problem
def test_the_distribution_carried_across_gives_this_interval(stored, price):
    """Draw by draw: the i-th stored figure priced at the i-th price."""
    expected = mc.interval(joined(stored, price, True))
    yours = mine(stored, price, True)
    # A bare boolean, so that pytest's own report of the comparison cannot print the expected ends.
    right = yours == pytest.approx(expected, rel=1e-6)
    assert right, (
        f"with the price carried across as a distribution, your interval runs from "
        f"{yours[0]:,.0f} to {yours[1]:,.0f}, and {where_it_is_off(yours, expected)}. Multiply "
        "the two arrays element by element and take the 5th and 95th percentiles of the product."
    )


@pytest.mark.problem
def test_the_median_carried_across_gives_this_interval(stored, price):
    """One number crosses the seam: the upstream median, treated downstream as known."""
    expected = mc.interval(joined(stored, price, False))
    yours = mine(stored, price, False)
    # A bare boolean, so that pytest's own report of the comparison cannot print the expected ends.
    right = yours == pytest.approx(expected, rel=1e-6)
    assert right, (
        f"with the price carried across as its median, your interval runs from {yours[0]:,.0f} "
        f"to {yours[1]:,.0f}, and {where_it_is_off(yours, expected)}. Price every stored figure "
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
    shrinkage = how_much_narrower(mine(stored, price, True), mine(stored, price, False))
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


def test_a_wrong_answer_is_not_told_the_right_one(stored, price):
    """Scaffolding: a failure message says which way the reader is off, never where to land.

    The median join is a plausible wrong answer to the distribution join, and the other way round.
    Neither message may carry the interval the reader was graded against.
    """
    wide = mc.interval(joined(stored, price, True))
    narrow = mc.interval(joined(stored, price, False))
    for yours, expected in ((narrow, wide), (wide, narrow)):
        message = where_it_is_off(yours, expected)
        assert message, "a wrong interval produced no explanation"
        for value in expected:
            assert f"{value:,.0f}" not in message, message


def test_an_interval_with_no_width_is_told_so():
    """Scaffolding: a zero-width answer fails with a message, not a ZeroDivisionError.

    The message names the fault and carries no figure, so it cannot give away an expected value.
    Only its first line is the guard's own: pytest's rewriting appends the comparison below it,
    which the page's Check, run with ``--assert=plain``, does not show.
    """
    with pytest.raises(AssertionError, match="no width") as failure:
        how_much_narrower((5.0, 5.0), (1.0, 2.0))
    message = str(failure.value).splitlines()[0]
    assert not any(c.isdigit() for c in message), message


def test_the_dsl_has_no_node_kind_for_this():
    """Scaffolding: the gap the problem asks the reader to notice is really there.

    If a kind for "a distribution from another model" is ever added, this test fails and the
    problem's last paragraph needs rewriting - which is the correct outcome, not a nuisance.
    """
    from sizing.dsl import KINDS

    assert set(KINDS) == {"input", "derived", "measured", "ceiling"}, sorted(KINDS)
