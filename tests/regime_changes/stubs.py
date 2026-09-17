"""Chapter 7's problems. Edit this file; the tests beside it say whether you are right.

Both are about the same claim: some things a chain of multiplications cannot express, and no
amount of care about the inputs to that chain will warn you.
"""

from __future__ import annotations

import numpy as np


def straight_line_forecast(known: list[tuple[float, float]], at: np.ndarray) -> np.ndarray:
    """Problem 7.1 - do what a spreadsheet would do, and watch it fail.

    ``known`` is a list of ``(utilisation, residence_time)`` pairs measured on a system that has
    never been busy - all of them at low load, which is the data a healthy system actually has.
    ``at`` is the utilisations you want a forecast for.

    Fit a straight line through the known points and return what it predicts at each of ``at``.

    A straight line is not a strawman. It is what a chain of multiplications *is*: every model in
    Parts I and III is linear in each of its inputs, and if you ask one of them what happens when
    load doubles, it doubles something. That is the correct answer right up until it is not.

    The test compares your forecast against the curve the book swept out of the queueing model. At
    the loads you fitted on, the line is excellent. Further out it is not wrong by a percentage;
    it is wrong by a multiple, and the multiple grows.
    """
    raise NotImplementedError("problem 7.1")


def combinatorial_spread(factors: list[np.ndarray]) -> tuple[float, float]:
    """Problem 7.2 - why a cardinality node is the widest thing in any model that has one.

    ``factors`` is a list of sample arrays, each one an uncertain count: distinct values of a
    label, distinct routes, distinct versions in flight. The quantity you care about is their
    **product** - the number of combinations.

    Return two numbers: the ratio of the 95th to the 5th percentile of the widest single factor,
    and the same ratio for the product.

    Predict which is larger before you run it, and by roughly how much. Uncertainties do not add
    when quantities multiply; they compound. Three counts each uncertain by a factor of three give
    a product uncertain by a great deal more than a factor of three, and no amount of care about
    any one of them recovers it.

    This is why the observability model's label cardinality dominates every tornado it appears in,
    and why it is the input nobody's control knobs can touch.
    """
    raise NotImplementedError("problem 7.2")
