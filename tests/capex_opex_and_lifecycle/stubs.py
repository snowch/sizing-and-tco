"""Chapter 15's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations


def crossover_year(capex: float, annual_opex: float) -> float:
    """Problem 15.1 - when does the running cost overtake the purchase?

    Return the number of years at which cumulative running cost equals the capital cost. Fractions
    are fine; nobody's horizon lands on a birthday.

    One division, and the point is what it does to a conversation. Capital is the number that gets
    argued about, because it arrives as a single invoice with somebody's signature on it. Running
    cost arrives in pieces, monthly, from several directions, and is nobody's decision in
    particular. For most infrastructure the second overtakes the first well inside the horizon it
    was bought for, and the argument was had about the smaller part.
    """
    raise NotImplementedError("problem 15.1")


def lifecycle_total(capex: float, annual_opex: float, years: float, refresh_years: float) -> float:
    """Problem 15.2 - what a refresh cycle does to the total.

    Over ``years``, with the whole capital cost paid again every ``refresh_years``, return the
    total spend.

    The first purchase happens at the start. Decide what happens when a refresh falls exactly on
    the end of the horizon - whether you have bought a fleet you will not use - and defend
    whichever you choose in a comment. The test accepts either, and checks only that you are
    consistent about it, because this is a modelling choice rather than a fact.

    That is the honest state of the question. A five-year horizon with a five-year refresh is
    either one purchase or two depending on a convention nobody wrote down, and the difference is
    the largest single line in the model.
    """
    raise NotImplementedError("problem 15.2")
