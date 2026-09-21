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

    A quantity you know to within a factor and no better: as likely to sit anywhere in its range
    on a multiplicative scale, so that doubling is as plausible as halving wherever you start. Its
    density is proportional to one over the value, between ``minimum`` and ``maximum`` and zero
    outside them::

        density(x) = 1 / (x * ln(maximum / minimum))     for minimum <= x <= maximum

    That is the whole specification. It is the shape for a ballpark: how many distinct label
    values a service will turn out to carry, the size of a table nobody has counted.

    Your job is the percentile function: given percentiles in (0, 1), return the values that sit
    at them. Derive it the way the chapter derived the triangular's: the area under the density
    from the minimum up to a value, set equal to the percentile, then inverted. It comes out as
    one line.

    The test grades it against the density rather than against a formula. It integrates the
    density numerically up to each value you return and checks that the area is the percentile
    you were given. So there is nothing to look up, and a function that is monotonic and bounded
    but the wrong shape fails.
    """
    raise NotImplementedError("problem 13.1")


def sample_two_inputs(seed: int, samples: int) -> dict[str, np.ndarray]:
    """Problem 13.2 — sample a model by hand.

    Return a dictionary with three keys. ``staff_fte`` and ``fully_loaded_salary`` each hold
    ``samples`` draws from the distributions the web service model declares for them, one a
    triangular and one a lognormal; ``annual_staff_cost`` holds what those draws imply, worked
    through the model's own formula for it by hand. Read the distributions and the formula out of
    ``models/web_service/model.yaml`` — do not copy the numbers here, because a problem that goes
    stale when the model changes is not testing anything.

    Use ``numpy`` and ``sizing.normal`` if you like. Do **not** use ``sizing.mc`` or
    ``sizing.evaluate``: the point of this one is to find out how little machinery there actually
    is between a declared distribution and a bag of numbers, and between the bag and an interval
    the book publishes.

    The test compares your inputs' percentiles against what the declared distributions say, and
    your cost's interval against the one the book publishes for the reference scenario, each to
    within the sampling error the count allows — which means it also checks that you understood
    what "to within sampling error" has to mean here. These two inputs are declared independent
    of everything else in the model, which is what makes the interval reachable by hand; ch14 is
    about the ones that are not.
    """
    raise NotImplementedError("problem 13.2")


def where_the_point_sits(
    samples: dict[str, np.ndarray], point: dict[str, float]
) -> dict[str, float]:
    """Problem 13.3 — where the point estimate sits among the sampled answers.

    ``samples`` holds every output's draws and ``point`` the same outputs' point estimates: the
    value the model computes from every input's middle. Return, for every output in ``point``,
    the fraction of that output's draws that fall below its point estimate.

    For a quantity that is one input passed straight through, the answer is a half. For a product
    of the model's shapes it is close to a half. For the web service's recommended host count it
    is not, by more than sampling error, and the chain says why: at least two of its steps are
    not multiplications, a maximum over three chains and a rounding up inside each, and a point
    estimate walks through them as if they were.

    Then finish the last line of this docstring with one sentence naming the step that moves the
    point furthest from the middle, and in which direction. The test grades the fractions, not
    the sentence; whoever reads your model will grade the sentence.

    What moved it:
    """
    raise NotImplementedError("problem 13.3")
