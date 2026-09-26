"""Chapter 16's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations


def hosts_that_fit(budget_kw: float, watts_per_host: float, pue: float) -> int:
    """Problem 16.1 - sizing runs the other way when power is the constraint.

    ``budget_kw`` is the power allocation at the wall, in kilowatts. ``watts_per_host`` is what one
    machine draws, in watts. ``pue`` is the facility multiplier - what the whole facility draws for
    each watt the machines draw. It is never less than one.

    Return how many whole machines fit in the allocation.

    Three things to get right. The allocation and the draw per machine are in different units. The
    multiplier applies to the machines' draw and not the other way round, so a rack full of
    efficient machines in an inefficient building buys you fewer of them, not more. And you round
    **down** - every other rounding in this book goes up, because every other constraint is a
    demand to be satisfied, and this one is a supply that cannot be exceeded.
    """
    raise NotImplementedError("problem 16.1")


def pue_premium(pue: float) -> float:
    """Problem 16.2 - what the building costs, as a fraction of the bill.

    Return the share of the electricity bill that goes to the facility rather than to the machines,
    as a number between zero and one.

    ``pue`` is the facility multiplier - what the whole facility draws for each watt the machines
    draw. It is never less than one. The multiplier is quoted as a ratio to what the machines draw.
    The share is of the whole bill, the machines' own draw included. The two are different numbers,
    and they sound different in a conversation about money.
    """
    raise NotImplementedError("problem 16.2")
