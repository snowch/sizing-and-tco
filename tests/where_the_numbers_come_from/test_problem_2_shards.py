"""Problem 3.2 - what it would cost to be more sure.

Graded against the square-root law, computed at test time from the arguments. A wrong count is
told which mistake it looks like, and never what the right count is.
"""

from __future__ import annotations

import math

import pytest

from tests.where_the_numbers_come_from.stubs import shards_needed

CASES = [(0.10, 8, 0.05), (1.0, 4, 0.1), (0.02, 16, 0.02), (2.5, 10, 0.5)]

#: What each recognisable wrong count means, in the reader's terms.
EXTRA = "that is the number of extra shards. Return the total: the ones you have already count."
LINEAR = (
    "that grows with the ratio of the two errors, not with its square. Halving the error costs "
    "four times the measuring, not twice."
)
OTHER = (
    "that is not the count the square-root law gives. The standard error falls as one over the "
    "square root of the number of shards: check which way round the ratio goes, then round up."
)


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


def diagnosis(answer, observed: float, shards: int, target: float) -> str | None:
    """None when ``answer`` is right; otherwise which mistake it looks like. Never the count."""
    count = exact(observed, shards, target)
    if rounds_up_to(answer, count):
        return None
    if rounds_up_to(answer, count - shards):
        return EXTRA
    if rounds_up_to(answer, shards * observed / target):
        return LINEAR
    return OTHER


@pytest.mark.problem
@pytest.mark.parametrize(("observed", "shards", "target"), CASES)
def test_it_follows_the_square_root_law(observed, shards, target):
    # pytest.fail rather than assert: pytest explains a failed assert by printing the arguments of
    # every call in it, and one of those arguments is the answer.
    wrong = diagnosis(shards_needed(observed, shards, target), observed, shards, target)
    if wrong:
        pytest.fail(
            f"from a standard error of {observed} at {shards} shards down to {target}: {wrong}",
            pytrace=False,
        )


@pytest.mark.problem
def test_asking_for_what_you_already_have_costs_nothing_more():
    observed, shards = 0.02, 16
    wrong = diagnosis(shards_needed(observed, shards, observed), observed, shards, observed)
    if wrong:
        pytest.fail(f"asking for the standard error you already have: {wrong}", pytrace=False)


@pytest.mark.problem
def test_it_refuses_an_impossible_target():
    with pytest.raises((ValueError, ZeroDivisionError)):
        shards_needed(0.1, 8, 0.0)


def test_the_cases_are_not_all_the_same_answer():
    """Scaffolding: four cases, four answers."""
    answers = [math.ceil(exact(*case)) for case in CASES]
    assert len(set(answers)) >= 3, answers


def test_each_mistake_is_told_apart_from_the_others():
    """Scaffolding: where the law, the linear guess and the extra-only count differ, each gets its
    own diagnosis, so a reader is told which mistake they made rather than a neighbouring one."""
    for observed, shards, target in CASES:
        count = exact(observed, shards, target)
        assert diagnosis(math.ceil(count - 1e-9), observed, shards, target) is None
        assert diagnosis(math.ceil(count - shards - 1e-9), observed, shards, target) == EXTRA
        if not math.isclose(count, shards):
            linear = math.ceil(shards * observed / target - 1e-9)
            assert diagnosis(linear, observed, shards, target) == LINEAR
