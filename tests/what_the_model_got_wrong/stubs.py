"""Chapter 23's problems. Edit this file; the tests beside it say whether you are right.

The design failed. Both problems are about what the model can say afterwards, about the web
service's failures. The first ranks the inputs by how far each one moved in the failures. The
second counts the failures in which nothing was extreme, and holds that count against its base
rate: how often something is extreme when nothing has failed.
"""

from __future__ import annotations

import numpy as np


def attribute(draws: dict[str, np.ndarray], failed: np.ndarray) -> list[tuple[str, float]]:
    """Problem 23.1 - which input was doing something unusual when the design failed?

    ``draws`` is one array per uncertain input, all the same length: the values that were drawn
    together, sample by sample. ``failed`` is a boolean array of the same length, true in the
    samples where the design was asked to do something it could not.

    Return ``(name, shift)`` pairs, ordered with the largest shift first, where *shift* is how far
    that input's typical value in the failures sits from its typical value across everything, as a
    fraction of the latter. An input that behaves the same way in the failures as it does anywhere
    else gets a shift near zero, and belongs at the bottom.

    Use a median rather than a mean. Every input in this book is skewed, and a mean would report a
    shift that is mostly the tail moving rather than the ordinary case changing.

    Two things the tests check that are easy to miss. An input that never varies has no shift and
    must not raise. And the ordering is by *size* of shift, not by sign: an input that is unusually
    low in the failures is exactly as much of a cause as one that is unusually high.
    """
    raise NotImplementedError("problem 23.1")


def share_with_nothing_extreme(
    draws: dict[str, np.ndarray], failed: np.ndarray, percentile: float = 90.0
) -> float:
    """Problem 23.2 - how often the story afterwards is allowed to be about one dramatic thing.

    Same arguments as ``attribute``. Return the fraction of the failing samples in which *no*
    input was above its own ``percentile``, taken across all the draws and not the failing ones
    alone. The name says what it returns: the share in which nothing was extreme, not the share in
    which something was. The attribution table prints the other one.

    Only the upper end counts. A value is extreme when it is above the percentile; a value below
    the 10th percentile does not count, however unusual. This differs from problem 23.1, where a
    low shift counted as much as a high one.

    These are the failures with no culprit to point at, because every input involved was merely
    somewhat above average. Before you run the tests: one test passes you eight inputs drawn with
    no connection to which samples failed. Work out on paper what share of failures it should
    return, from one fact: each input is above its own 90th percentile in one future in ten,
    independently of the others. Write your working in a comment below. The test holds your
    function to that arithmetic, so a pass means your function and your working agree.

    Why the figure matters: a failure in which nothing was extreme is a failure of the *design*
    rather than of the world. The margin was too thin to absorb an ordinary week, and you fix that
    by changing the margin, not by blaming an input.
    """
    raise NotImplementedError("problem 23.2")
