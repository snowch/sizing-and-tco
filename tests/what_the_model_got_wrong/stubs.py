"""Chapter 22's problems. Edit this file; the tests beside it say whether you are right.

The design failed. Both problems are about what the model can say afterwards — and the second is
about the thing it says with complete confidence and no basis whatsoever.
"""

from __future__ import annotations

import numpy as np


def attribute(draws: dict[str, np.ndarray], failed: np.ndarray) -> list[tuple[str, float]]:
    """Problem 22.1 - which input was doing something unusual when the design failed?

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
    raise NotImplementedError("problem 22.1")


def was_anything_extreme(
    draws: dict[str, np.ndarray], failed: np.ndarray, percentile: float = 90.0
) -> float:
    """Problem 22.2 - how often the story afterwards is allowed to be about one dramatic thing.

    Same arguments. Return the fraction of the failing samples in which *no* input was beyond its
    own ``percentile`` — that is, the share of failures for which there is no culprit to point at,
    because everything involved was merely somewhat above average.

    Predict the answer before you run it, for the web service, and write your prediction in a
    comment. Most people predict something small.

    The number this returns is the one that makes a post-mortem honest. A failure in which nothing
    was extreme is a failure of the *design* rather than of the world: the margin was too thin to
    absorb an ordinary week. That is a much less satisfying story and a much more useful one.
    """
    raise NotImplementedError("problem 22.2")
