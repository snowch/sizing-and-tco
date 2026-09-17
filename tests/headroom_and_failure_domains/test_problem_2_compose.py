"""Problem 10.2 - margins compose multiplicatively, and the arithmetic surprises people."""

from __future__ import annotations

import math

import pytest

from tests.headroom_and_failure_domains.stubs import compose

CASES = [
    [0.25],
    [0.25, 0.30],
    [0.25, 0.30, 0.20],
    [0.10] * 5,
    [0.5, 0.5],
    [],
]


def expected(margins: list[float]) -> float:
    """What is left after each margin takes its share of what the last one left."""
    return 1.0 - math.prod(1.0 - m for m in margins)


@pytest.mark.problem
@pytest.mark.parametrize("margins", CASES)
def test_they_compose_multiplicatively(margins):
    assert compose(margins) == pytest.approx(expected(margins), rel=1e-12), (
        "each margin takes its share of what the previous one left, not of the original"
    )


@pytest.mark.problem
def test_no_margins_is_no_margin():
    assert compose([]) == pytest.approx(0.0)


@pytest.mark.problem
def test_it_never_leaves_a_negative_system():
    """Adding three margins of ninety per cent would. That is the clue the problem mentions."""
    assert compose([0.3, 0.3, 0.3]) < 1.0
    assert compose([0.9, 0.9, 0.9]) < 1.0


@pytest.mark.problem
def test_the_composed_margin_is_less_than_the_sum():
    """For small margins, which is the case everybody is actually in."""
    margins = [0.25, 0.30, 0.20]
    assert compose(margins) < sum(margins)


@pytest.mark.problem
def test_three_reasonable_requests_take_most_of_the_system():
    """The point of the problem, and the reason a sizing meeting ends where it does."""
    left = 1.0 - compose([0.25, 0.30, 0.20])
    assert left < 0.45, (
        f"three separately reasonable margins leave {left:.0%} of the cluster doing the work it "
        "was bought for. Each request was defensible; nobody in the room multiplied them."
    )


def test_the_book_declares_more_than_one_margin():
    """Scaffolding: the problem's premise holds — real models have several."""
    from sizing.dsl import discover

    ceilings = sum(len(model.of_kind("ceiling")) for model in discover())
    assert ceilings >= 3, "if models only ever had one margin, composing them would not matter"
