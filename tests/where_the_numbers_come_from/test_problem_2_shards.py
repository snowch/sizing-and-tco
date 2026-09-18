"""Problem 3.2 - what it would cost to be more sure.

Graded against the square-root law, computed at test time from the arguments.
"""

from __future__ import annotations

import math

import pytest

from tests.where_the_numbers_come_from.stubs import shards_needed

CASES = [(0.10, 8, 0.05), (1.0, 4, 0.1), (0.02, 16, 0.02), (2.5, 10, 0.5)]


def expected(observed_sd: float, at_shards: int, target_sd: float) -> int:
    """One over the square root of n, rearranged. Derived, never stored."""
    return int(math.ceil(at_shards * (observed_sd / target_sd) ** 2))


@pytest.mark.problem
@pytest.mark.parametrize(("observed", "shards", "target"), CASES)
def test_it_follows_the_square_root_law(observed, shards, target):
    assert shards_needed(observed, shards, target) == expected(observed, shards, target), (
        f"to go from a standard error of {observed} at {shards} shards down to {target}, the law "
        f"says {expected(observed, shards, target)} shards in total. Halving the error costs four "
        "times the measuring, not twice."
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
    answers = [expected(*case) for case in CASES]
    assert len(set(answers)) >= 3, answers
