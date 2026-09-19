"""Chapter 13's problems. Edit this file; the tests beside it say whether you are right.

There is no answer key anywhere in this repository. Each test derives what it expects from the
problem's own statement — from the parameters of a distribution, or from an independent
calculation — so there is nothing to look up and nothing to copy.

Run one at a time:

    python3 -m pytest tests/monte_carlo/test_problem_1_ppf.py
"""

from __future__ import annotations

import numpy as np


def pert_ppf(u: np.ndarray, minimum: float, likely: float, maximum: float) -> np.ndarray:
    """Problem 13.1 — the percentile function of a distribution this book does not have.

    The *PERT* distribution is the triangular's better-behaved cousin, and it is the one most
    estimation tools reach for. Same three parameters — the least it could be, the most, and the
    one you would bet on — but instead of straight edges it is a beta distribution fitted so that
    its mean is::

        (minimum + 4 * likely + maximum) / 6

    That is the whole specification. The mode is weighted four times as heavily as the extremes,
    which is a statement about how much an expert's central guess is worth relative to the bounds
    they put around it.

    Your job is the percentile function: given percentiles in (0, 1), return the values that sit
    at them. You may not use scipy, and you will not need it — a beta distribution on the unit
    interval with the right two shape parameters can be sampled from two gamma draws, or by
    bisection on its own cumulative function, or by any other route you can defend.

    The test checks three things, all derived from the parameters rather than stored:

    * the values it produces have the mean the formula above gives;
    * they are bounded by ``minimum`` and ``maximum``;
    * the percentile function is monotonic, which every percentile function is.

    Hint on shape parameters. Write ``m`` for the mean above, scaled onto (0, 1) by
    ``(m - minimum) / (maximum - minimum)``. Then ``alpha = 1 + 4 * (likely - minimum) /
    (maximum - minimum)`` and ``beta = 1 + 4 * (maximum - likely) / (maximum - minimum)``. Work
    out why those give the right mean before you use them; it is two lines of algebra and it is
    the only part of this problem worth remembering.
    """
    raise NotImplementedError("problem 13.1")


def sample_two_inputs(seed: int, samples: int) -> dict[str, np.ndarray]:
    """Problem 13.2 — sample a model by hand.

    Return a dictionary with two keys, ``host_price`` and ``network_price_per_host``, each
    holding ``samples`` draws from the distributions the web service model declares for them.
    Read the distributions out of ``models/web_service/model.yaml`` — do not copy the numbers here,
    because a problem that goes stale when the model changes is not testing anything.

    Use ``numpy`` and ``sizing.normal`` if you like. Do **not** use ``sizing.mc`` or
    ``sizing.evaluate``: the point of this one is to find out how little machinery there actually
    is between a declared distribution and a bag of numbers.

    The test compares your percentiles against what the declared distribution says they should be,
    to within the sampling error the count allows — which means it also checks that you understood
    what "to within sampling error" has to mean here.
    """
    raise NotImplementedError("problem 13.2")


def make_the_point_estimate_lie() -> dict[str, dict]:
    """Problem 13.3 — find a model whose point estimate is not a typical answer.

    Return a dictionary mapping input node names to replacement distributions, in the same form a
    model file uses::

        {"host_price": {"lognormal": {"p10": 3000, "p90": 14000}}}

    Every input you replace must keep the same *kind* of distribution it already has, and its p10
    and p90 must stay inside the ``range:`` the model declares for it — you are choosing a
    defensible set of beliefs, not breaking the model.

    Find a set for which the five-year total's point estimate — the value the model computes from
    every input's median — falls **outside** the middle 50% of the sampled answers. That is a
    model whose headline number is not merely uncertain but unrepresentative: more than three
    quarters of what the model thinks could happen is on one side of it.

    Then write one sentence, in the docstring of your implementation, naming the property of the
    model that makes this possible. The test does not grade the sentence. Somebody reviewing your
    model will.
    """
    raise NotImplementedError("problem 13.3")
