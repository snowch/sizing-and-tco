"""Chapter 4's problems. Edit this file; the tests beside it say whether you are right.

Both are about the same mistake in two disguises: using an average where an average does not
answer the question.
"""

from __future__ import annotations

import numpy as np


def busy_hour_rate(hourly_shape: np.ndarray, daily_total: float) -> float:
    """Problem 4.1 - the number that sizes you is not the daily mean.

    ``hourly_shape`` is twenty-four relative weights describing how a day's demand is distributed:
    a flat day is twenty-four equal numbers, a spiky one is not. ``daily_total`` is how much
    arrives across the whole day, in whatever unit you like.

    Return the **rate during the busiest hour**, in that unit per hour.

    The weights are relative, not absolute, and they do not necessarily sum to anything in
    particular - normalise them. That is most of the problem, and getting it wrong gives an answer
    that is confidently off by whatever the weights happened to add up to.

    The test also checks a flat day, where the busy-hour rate and the daily mean rate must agree,
    because a system with no peak has nothing to size for.
    """
    raise NotImplementedError("problem 4.1")


def growth_gap(t0: float, growth_factors: np.ndarray, years: float) -> tuple[float, float]:
    """Problem 4.2 - compound the average, or average the compounds?

    You have a starting capacity ``t0`` and a bag of plausible annual growth factors
    (``growth_factors``: 1.2 means twenty per cent a year). You want the capacity after ``years``.

    There are two things you could compute and people compute the wrong one:

    * take the **average growth rate** and compound it over the years;
    * compound **every** growth rate over the years, and average the results.

    Return both, in that order.

    They are not equal, and one of them is always larger. Work out which before you run it, then
    run it. The gap widens with the spread of the growth rates and with the horizon, which means
    it is largest in exactly the situation people use a five-year plan for.

    The test asserts the order and that the gap is material. It does not tell you the answer; the
    values come from the bag you are handed.
    """
    raise NotImplementedError("problem 4.2")
