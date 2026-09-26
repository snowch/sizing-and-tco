"""Chapter 17's problems. Edit this file; the tests beside it say whether you are right.

Both are about the denominator, which is the half of a unit cost nobody checks.
"""

from __future__ import annotations

import numpy as np


def unit_cost(total: float, quantity: float, months: float) -> float:
    """Problem 17.1 - a total, over a quantity, over a period.

    Return the cost per unit per month.

    ``total`` is the five-year total, in dollars. It takes two divisions: by
    the quantity (what is held in terabytes), and by the months (the period
    the total covers). The second division makes it a problem. A cost per terabyte cannot be compared with anything until it
    says per terabyte *per what*. Per TB-month and per TB-year differ by a
    factor of twelve and look equally authoritative.

    In a model file the build catches this: the two units have the same
    dimensions and different sizes, and the build converts. Appendix D lists
    this model's own case. On a slide nothing catches it.
    """
    raise NotImplementedError("problem 17.1")


def denominators(
    stored_samples: np.ndarray, total_samples: np.ndarray, stored_at_start: float, months: float
) -> dict[str, float]:
    """Problem 17.2 - the same cost, over four defensible denominators.

    You have a bag of five-year totals and a bag of what the service holds at
    the horizon, sample by sample, and two plain numbers the test takes from
    the model: ``stored_at_start``, what it holds on day one, and ``months``,
    the months in the horizon. Somebody wants a cost per terabyte per month.
    Return a dictionary with four of them, keyed exactly as below, each a
    single number. Every one is per month: divide by ``months``.

    Each key makes two choices: when in the fleet's life you count what is
    held (day one, the horizon, or the straight-line average of the two), and
    whether you take medians first or divide first.

    ``"at_horizon"``
        Median total over the median of what is held at the horizon. What you
        will be paying for at the end.
    ``"at_start"``
        Median total over what is held on day one, ``stored_at_start``. What
        you are paying for now.
    ``"average_linear"``
        Median total over the mean of ``stored_at_start`` and the median of
        what is held at the horizon: a straight line between the two ends.
        Holdings compound, so the curve bends upward and the straight line
        lies above it; this average overstates what is held.
    ``"per_sample"``
        Divide each total by what that same sample holds at the horizon, then
        take the median of those ratios.

    All four are defensible and not close together. Only ``"per_sample"``
    divides first, so only it keeps each future's total over that same
    future's holding. ``"at_horizon"`` and ``"average_linear"`` set a total
    from one set of futures over a holding from another. ``"at_start"``
    divides by one number, the same in every future. The model's own
    ``cost_per_stored_tb_month`` is none of the four: it divides first, over
    the straight-line holding.

    Return them, look at the spread, and then decide which you would put on a
    slide - and whether you would be willing to say which it was.
    """
    raise NotImplementedError("problem 17.2")
