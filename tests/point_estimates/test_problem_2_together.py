"""Problem 1.2 - how the commute's inputs combine, graded against the commute itself.

The chapter's taxi table shows the year's fares with each input moved alone and with all three
moved at once. The reader is handed how far each input alone raises the cost and asked for how
far a set of them raises it together. The oracle is the commute: the test moves the inputs in
the example file and divides, so nothing here states the answer. It asks for pairs as well as
all three, so a number read off the table's last row is not a rule.
"""

from __future__ import annotations

import itertools
import math

import pytest

from tests.point_estimates.oracle import commute, rise
from tests.point_estimates.stubs import spread_together


def sets_of_inputs() -> list[tuple[str, ...]]:
    """All three first, because that is the table's last row; then every pair."""
    names = tuple(commute())
    return [names, *itertools.combinations(names, 2)]


@pytest.mark.problem
def test_together_follows_from_each_alone():
    alone = {name: rise((name,)) for name in commute()}
    for moving in sets_of_inputs():
        given = {name: alone[name] for name in moving}
        answer = spread_together(dict(given))
        ok = math.isclose(answer, rise(moving), rel_tol=1e-9)
        if answer <= max(given.values()):
            hint = (
                "Your answer is no bigger than one of them manages alone. Every input here costs "
                "more at its most, so moving more of them cannot cost less."
            )
        elif math.isclose(answer, sum(given.values()), rel_tol=1e-9) or math.isclose(
            answer, 1 + sum(v - 1 for v in given.values()), rel_tol=1e-9
        ):
            hint = (
                "You have added the rises. Work out each row of the table as a multiple of the "
                "usual commute's cost, and see how the last row's follows from the three above it."
            )
        else:
            hint = (
                "Work out each row of the table as a multiple of the usual commute's cost, and see "
                "how the last row's follows from the three above it."
            )
        names = ", ".join(moving[:-1]) + " and " + moving[-1]
        assert ok, f"not how far {names} together raise the year's fares. {hint}"


def test_the_commute_moves_further_together_than_any_input_alone():
    """Scaffolding: the page says all three together raise the cost more than any one alone, and
    the problem has nothing to find if that is not so."""
    names = tuple(commute())
    assert all(rise((name,)) > 1 for name in names), "an input's most does not cost more"
    assert rise(names) > max(rise((name,)) for name in names)


def test_every_set_the_test_asks_about_is_different():
    """Scaffolding: a single number cannot pass, because the sets do not all give the same rise."""
    rises = [rise(moving) for moving in sets_of_inputs()]
    assert len({round(r, 9) for r in rises}) == len(rises)
