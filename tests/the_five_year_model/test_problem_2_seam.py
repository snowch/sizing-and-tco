"""Problem 18.2 - what a point estimate costs at the seam between two models."""

from __future__ import annotations

import pytest

from tests.the_five_year_model.stubs import joined_interval


@pytest.mark.problem
def test_both_directions_produce_an_interval():
    for use_distribution in (True, False):
        low, high = joined_interval(use_distribution)
        assert 0 < low < high, (use_distribution, low, high)


@pytest.mark.problem
def test_the_point_estimate_narrows_the_answer():
    """The finding. Writing a number down between two models throws away what it was worth."""
    wide_low, wide_high = joined_interval(True)
    narrow_low, narrow_high = joined_interval(False)
    assert (narrow_high - narrow_low) < (wide_high - wide_low), (
        "handing a median across the seam should give a narrower interval than handing the "
        "distribution, because the downstream model no longer knows the upstream figure was "
        "uncertain"
    )


@pytest.mark.problem
def test_the_narrowing_is_substantial():
    wide = joined_interval(True)
    narrow = joined_interval(False)
    shrinkage = 1 - (narrow[1] - narrow[0]) / (wide[1] - wide[0])
    assert shrinkage > 0.1, (
        f"the interval only narrows by {shrinkage:.1%}. Check that the upstream price is actually "
        "reaching the downstream model in the distribution case - if the downstream output is "
        "dominated by its own inputs, pick an output the price feeds more directly."
    )


@pytest.mark.problem
def test_the_medians_stay_close():
    """The seam does not move the answer. It moves how sure you are of it, which is worse.

    A change that moved the headline number would be noticed. This one leaves the number where it
    was and quietly deletes the doubt, which is why it survives review.
    """
    wide = joined_interval(True)
    narrow = joined_interval(False)
    wide_mid = (wide[0] + wide[1]) / 2
    narrow_mid = (narrow[0] + narrow[1]) / 2
    assert abs(narrow_mid - wide_mid) / wide_mid < 0.5


def test_the_dsl_has_no_node_kind_for_this():
    """Scaffolding: the gap the problem asks the reader to notice is really there.

    If a kind for "a distribution from another model" is ever added, this test fails and the
    problem's last paragraph needs rewriting - which is the correct outcome, not a nuisance.
    """
    from sizing.dsl import KINDS

    assert set(KINDS) == {"input", "derived", "measured", "ceiling"}, sorted(KINDS)
