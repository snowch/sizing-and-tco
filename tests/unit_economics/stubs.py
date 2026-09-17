"""Chapter 16's problems. Edit this file; the tests beside it say whether you are right.

Both are about the denominator, which is the half of a unit cost nobody checks.
"""

from __future__ import annotations

import numpy as np


def unit_cost(total: float, quantity: float, months: float) -> float:
    """Problem 16.1 - a total, over a quantity, over a period.

    Return the cost per unit per month.

    Two divisions, and the reason it is a problem rather than an aside is the second one. A cost
    per terabyte is not comparable to anything until it says per terabyte *per what*, and the two
    figures people quote - per TB-month and per TB-year - differ by a factor of twelve while
    looking equally authoritative.

    The build catches this in a model, because those two have identical dimensions and different
    units and sizing/units.py converts. In a slide nothing catches it.
    """
    raise NotImplementedError("problem 16.1")


def denominators(capacity_samples: np.ndarray, total_samples: np.ndarray) -> dict[str, float]:
    """Problem 16.2 - the same cost, over four defensible denominators.

    You have a bag of five-year totals and a bag of capacities at the horizon, sample by sample.
    Somebody wants a cost per terabyte per month. Return a dictionary with four of them, keyed
    exactly as below, each a single number:

    ``"at_horizon"``
        Median total over median horizon capacity. What you will be able to store at the end.
    ``"at_start"``
        Median total over the day-one capacity, which you can get from the model. What you can
        store now.
    ``"average_linear"``
        Median total over the mean of the two, which is a straight line drawn under a curve that
        is not straight.
    ``"per_sample"``
        The median of the *per-sample* ratio: divide each total by its own capacity first, then
        take the median.

    All four are defensible, they are not close together, and the last one is the only one that is
    a statement about the same future in numerator and denominator. The other three divide a
    figure from one possible world by a figure from another.

    Return them, look at the spread, and then decide which you would put on a slide - and whether
    you would be willing to say which it was.
    """
    raise NotImplementedError("problem 16.2")
