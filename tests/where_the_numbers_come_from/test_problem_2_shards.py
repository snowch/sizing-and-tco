"""Problem 3.2 - what it would cost to be more sure.

Graded against the square-root law, computed at test time from the arguments.
"""

from __future__ import annotations

import math

import pytest

from tests.where_the_numbers_come_from.stubs import shards_needed

CASES = [(0.10, 8, 0.05), (1.0, 4, 0.1), (0.02, 16, 0.02), (2.5, 10, 0.5)]


def exact(observed_sd: float, at_shards: int, target_sd: float) -> float:
    """One over the square root of n, rearranged: the count before rounding up. Derived, never
    stored."""
    return at_shards * (observed_sd / target_sd) ** 2


def rounds_up_to(answer: int, count: float) -> bool:
    """Whether ``answer`` is ``count`` rounded up, allowing for the last digit of a float.

    Two correct derivations differ by a rounding error, and when the count is a whole number one
    of them rounds it up to the next. Either is the law; a count below the exact one, or two
    above it, is not.
    """
    return float(answer).is_integer() and count - 1e-6 <= answer < count + 1 + 1e-6


@pytest.mark.problem
@pytest.mark.parametrize(("observed", "shards", "target"), CASES)
def test_it_follows_the_square_root_law(observed, shards, target):
    count = exact(observed, shards, target)
    assert rounds_up_to(shards_needed(observed, shards, target), count), (
        f"to go from a standard error of {observed} at {shards} shards down to {target}, the law "
        f"says {count:.4g} shards in total, rounded up. Halving the error costs four times the "
        "measuring, not twice."
    )


@pytest.mark.problem
def test_asking_for_what_you_already_have_costs_nothing_more():
    assert shards_needed(0.02, 16, 0.02) == 16


@pytest.mark.problem
def test_it_refuses_an_impossible_target():
    with pytest.raises((ValueError, ZeroDivisionError)):
        shards_needed(0.1, 8, 0.0)


def test_the_cases_are_not_all_the_same_answer():
    """Scaffolding: four cases, four answers."""
    answers = [math.ceil(exact(*case)) for case in CASES]
    assert len(set(answers)) >= 3, answers
