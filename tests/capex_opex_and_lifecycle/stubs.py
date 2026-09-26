"""Chapter 15's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations


def crossover_year(capex: float, annual_opex: float) -> float:
    """Problem 15.1 - when does the running cost overtake the purchase?

    Return the number of years at which cumulative running cost equals the capital cost. `capex`
    is the capital cost; `annual_opex` is the running cost for one year. Fractions are fine. If
    `annual_opex` is zero, return `float("inf")`.

    See *The split* in chapter 15: it explains why this matters.
    """
    raise NotImplementedError("problem 15.1")


def lifecycle_total(capex: float, annual_opex: float, years: float, refresh_years: float) -> float:
    """Problem 15.2 - what a refresh cycle does to the total.

    Over ``years`` with the whole capital cost at the start and every ``refresh_years``, return
    the total spend: capital for each purchase plus ``annual_opex`` for every year.

    When a refresh lands exactly on the end of the horizon, decide what to do about a purchase you
    may not use. Defend your choice in a comment. The test accepts either and checks only that you
    apply it consistently, because this is a modelling choice, not a fact.

    The two choices differ by the whole capital cost. This book's model counts one purchase; yours
    may differ if you can defend it. Chapter 15 explains why.
    """
    raise NotImplementedError("problem 15.2")
