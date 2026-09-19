"""Chapter 22's problems. Edit this file; the tests beside it say whether you are right.

Both are about the difference between two totals rather than about either total.
"""

from __future__ import annotations


def paired_difference() -> dict:
    """Problem 22.1 - subtract futures, not intervals.

    Two quotes for one workload: ``models/web_service/scenarios/incumbent.yaml`` and
    ``models/web_service/scenarios/challenger.yaml``. Each has a five-year total with an interval
    on it, and the two intervals overlap. That is not the question. The question is what the
    *difference* between them looks like, future by future.

    Evaluate both scenarios with ``sizing.evaluate.evaluate`` and subtract the incumbent's
    five-year total from the challenger's, sample by sample: the same draw of the electricity
    price, the same growth, the same salary, on both sides. Return a dictionary with exactly
    these keys:

    ``"p5"``, ``"p50"``, ``"p95"``   percentiles of the difference, challenger minus incumbent
    ``"share_challenger_cheaper"``   the fraction of futures in which the challenger costs less

    A negative difference is the challenger being cheaper.

    If your interval comes out several times wider than the book's, you have subtracted two
    independent draws - the electricity price from one future against the price from another -
    and thrown away the fact that both designs live in the same world. The test says so.
    """
    raise NotImplementedError("problem 22.1")


def break_even_migration() -> float:
    """Problem 22.2 - how expensive can the move be before the challenger stops being cheaper?

    At the point estimate the challenger's quote is cheaper than the incumbent's before the cost
    of moving is counted. The move is the ``migration_cost`` input, which the incumbent holds at
    zero and the challenger's scenario overrides with the team's own estimate.

    Return the one-off cost of moving at which the two five-year totals are equal at the point
    estimate. Use the model's own point evaluation - ``sizing.evaluate.point`` with the
    challenger's scenario and a different ``migration_cost`` in its overrides - rather than
    arithmetic of your own, so that the answer moves when the model does.

    The total is linear in that one input, so two evaluations determine the line. Bisection
    works too, and is the method to reach for when the next break-even is not linear.
    """
    raise NotImplementedError("problem 22.2")
