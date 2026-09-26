"""Chapter 13's problems. Edit this file; the tests beside it say whether you are right.

There is no answer key anywhere in this repository. Each test derives what it expects from the
problem's own statement — from the parameters of a distribution, or from an independent
calculation — so there is nothing to look up and nothing to copy.

Run one at a time:

    python3 -m pytest tests/monte_carlo/test_problem_1_ppf.py
"""

from __future__ import annotations

import numpy as np


def log_uniform_ppf(u: np.ndarray, minimum: float, maximum: float) -> np.ndarray:
    """Problem 13.1 — the percentile function of a shape this book does not have.

    A quantity you know to within a factor and no better: as likely to sit anywhere in its range on
    a multiplicative scale, so that doubling is as plausible as halving wherever you start. Its
    density is proportional to one over the value, between ``minimum`` and ``maximum`` and zero
    outside them::

        density(x) = 1 / (x * ln(maximum / minimum))     for minimum <= x <= maximum

    That is the whole specification. It is the shape for a ballpark: how many distinct label values
    a service will turn out to carry, the size of a table nobody has counted.

    Your job is the percentile function: given fractions between 0 and 1, return the value each
    fraction of the bag is below. Derive it the way the chapter derived the triangular's: the area
    under the density from the minimum up to a value, set equal to the fraction, then inverted. It
    needs one integral, and it comes out as one line.

    The test integrates the density numerically up to each value you return and checks that the area
    is the fraction you were given. So there is nothing to look up, and a function that is monotonic
    and bounded but the wrong shape fails.
    """
    raise NotImplementedError("problem 13.1")


def sample_two_inputs(declared: dict[str, dict], seed: int, samples: int) -> dict[str, np.ndarray]:
    """Problem 13.2 — sample a model by hand.

    ``declared`` holds two of the web service model's inputs, ``staff_fte`` and
    ``fully_loaded_salary``, each keyed to the distribution the model declares for it, as the file
    writes it. One is a triangular::

        {"triangular": {"minimum": ..., "likely": ..., "maximum": ...}}

    and one is a lognormal::

        {"lognormal": {"p10": ..., "p90": ...}}

    The test reads both out of ``models/web_service/model.yaml`` and hands them to you, so a change
    to the model changes what you are given instead of going stale in a number typed here. Sample
    what you are handed.

    Return a dictionary with three keys. ``staff_fte`` and ``fully_loaded_salary`` each hold
    ``samples`` draws from their distribution, seeded with ``seed``; ``annual_staff_cost`` holds
    what those draws imply, worked draw by draw through the model's own formula for it:
    ``staff_fte * fully_loaded_salary``, quoted under the problem on the chapter page.

    Do it the way the chapter did: for each input, draw its own random fractions between 0 and 1,
    then ask its distribution for the value at each. Drawing both inputs from the same fractions
    makes them rise and fall together, which the model does not declare, and the test checks for it.
    Use ``numpy`` and ``sizing.normal`` for ``normal_ppf``: the normal's percentile function, which
    the lognormal needs. ``Z90`` in the chapter's ``lognormal_ppf`` is ``normal_ppf(0.9)``. Do
    **not** use ``sizing.mc`` or ``sizing.evaluate``: the point of this one is to find out how
    little machinery there is between a declared distribution and a bag of numbers, and between the
    bag and an interval the book publishes.

    The test compares your inputs' percentiles with what the declared distributions say, checks that
    each input had its own draw, and compares your cost's 5th and 95th percentiles with the ones the
    book publishes for the reference scenario. Each comparison allows for the wobble a finite number
    of draws brings. These two inputs are declared independent of everything else in the model,
    which is what makes the interval reachable by hand; ch14 is about the ones that are not.
    """
    raise NotImplementedError("problem 13.2")


def where_the_point_sits(
    samples: dict[str, np.ndarray], point: dict[str, float]
) -> dict[str, float]:
    """Problem 13.3 — where the point estimate sits among the sampled answers.

    ``samples`` holds every output's draws and ``point`` the same outputs' point estimates: the
    value the model computes from every input's middle. Return, for every output in ``point``, the
    fraction of that output's draws that fall strictly below its point estimate. A draw equal to the
    point is not below it. The host count is a whole number, so many of its draws equal the point
    exactly.

    For a quantity that is one input passed straight through, the fraction is a half. For a product
    of two of the model's shapes, it is close to a half. Of the four outputs you are given, some sit
    near a half and some do not, by more than the wobble that a finite number of draws brings.

    Then finish the last line of this docstring: for each output whose point sits away from the
    middle, one sentence naming the step in its chain that moved it, and in which direction. The
    test grades the fractions, not the sentences; whoever reads your model will grade the sentences.

    What moved it:
    """
    raise NotImplementedError("problem 13.3")
