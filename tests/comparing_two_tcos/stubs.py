"""Chapter 22's problems. Edit this file; the tests beside it say whether you are right.

Both are about the difference between two totals rather than about either total.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def paired_difference(incumbent: np.ndarray, challenger: np.ndarray) -> dict:
    """Problem 22.1 - subtract futures, not intervals.

    Two quotes for one workload, the incumbent's and the challenger's. Each has a five-year total
    with an interval on it, and the two intervals overlap. That is not the question. The question
    is what the *difference* between them looks like, future by future.

    The test evaluates both quotes on the same draws and hands you the two totals: ``incumbent``
    and ``challenger``, one five-year total per sampled future, in the same order on both sides.
    The i-th entry of one and the i-th entry of the other are the same future - the same draw of
    the electricity price, the same growth, the same salary - priced once for each design.

    Subtract the incumbent's total from the challenger's, sample by sample, and return a
    dictionary with exactly these keys:

    ``"p5"``, ``"p50"``, ``"p95"``   percentiles of the difference, challenger minus incumbent
    ``"share_challenger_cheaper"``   the fraction of futures in which the challenger costs less

    A negative difference is the challenger being cheaper.

    The test calls your function twice: on every future, and on a subset of the same futures,
    whose answer the chapter does not print. An interval much wider than it should be means two
    independent draws were subtracted - the electricity price from one future against the price
    from another - or the opposite ends of the two intervals. Both throw away the fact that both
    designs live in the same world. An interval narrower than it should be can mean one total's
    percentile minus the other's, each taken on its own. That is not a percentile of the
    difference. The test names each of these mistakes when it sees one, and it names a
    subtraction made the wrong way round.
    """
    raise NotImplementedError("problem 22.1")


def break_even_migration(difference_at: Callable[[float], float]) -> float:
    """Problem 22.2 - how expensive can the move be before the challenger stops being cheaper?

    At the point estimate the challenger's quote is cheaper than the incumbent's before the cost
    of moving is counted. The move is the ``migration_cost`` input, which the incumbent holds at
    zero and the challenger's scenario overrides with the team's own estimate.

    ``difference_at(migration)`` is the model's own point evaluation. Hand it a one-off cost of
    moving and it returns the challenger's five-year total minus the incumbent's at the point
    estimate, with the incumbent on the fleet the test is grading and everything else as the two
    scenarios hold it. Return the cost of moving at which that difference is zero: the cost at
    which the two five-year totals are equal.

    The fleet is the test's to choose because the chapter prints the tie for the fleet the
    incumbent runs. The test builds one ``difference_at`` for that fleet and two for fleets the
    page does not print, and an answer that moves when the fleet does cannot have been copied off
    the page.

    The total is linear in the cost of the move, so two evaluations determine the line. Bisection
    works too, and is the method to reach for when the next break-even is not linear.
    """
    raise NotImplementedError("problem 22.2")
