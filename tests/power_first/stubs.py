"""Chapter 15's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations


def nodes_that_fit(budget_kw: float, watts_per_node: float, pue: float) -> int:
    """Problem 15.1 - sizing runs the other way when power is the constraint.

    ``budget_kw`` is the power allocation, at the wall. ``watts_per_node`` is what one machine
    draws. ``pue`` is the facility multiplier - what the building spends on cooling and losses for
    every watt the machines use.

    Return how many whole machines fit in the allocation.

    Two things to get right. The multiplier applies to the machines' draw and not the other way
    round, so a rack full of efficient machines in an inefficient building buys you fewer of them,
    not more. And you round **down** - every other rounding in this book goes up, because every
    other constraint is a demand to be satisfied, and this one is a supply that cannot be
    exceeded.
    """
    raise NotImplementedError("problem 15.1")


def pue_premium(pue: float) -> float:
    """Problem 15.2 - what the building costs, as a fraction of the bill.

    Return the share of the electricity bill that goes to the facility rather than to the
    machines, as a number between zero and one.

    It is one line and it is worth having in your head, because a facility multiplier is quoted as
    a ratio and paid as a fraction, and the two feel very different. A building that sounds a
    little inefficient turns out to be spending a third of the bill on itself.
    """
    raise NotImplementedError("problem 15.2")
