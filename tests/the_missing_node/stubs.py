"""Chapter 20's problems. Edit this file; the tests beside it say whether you are right.

ch14 asked you to repair a model that was wrong in shape. These two ask the harder question that
comes first: how would you know?
"""

from __future__ import annotations

import numpy as np


def is_refuted(samples: np.ndarray, observation: float, observations: int) -> bool:
    """Problem 20.1 - is one number outside the interval evidence of anything?

    ``samples`` is a model's output distribution. ``observation`` is a figure from the real world
    that the model was supposed to describe. ``observations`` is how many such figures you have.

    Return whether the model is refuted by it.

    The whole problem is in the word "refuted", and the trap is that a 90% interval is *supposed*
    to be missed one time in ten. One observation outside it is not evidence; it is the expected
    behaviour of an interval that is doing its job. A model that were rejected on that basis would
    be rejected roughly whenever it was right.

    So decide what would count. State a rule that holds together - what fraction outside would
    surprise you, given how many observations you have - and implement it. The tests check the
    cases at both ends: a single miss is never a refutation, and an observation far enough out
    that no plausible model produces it always is.

    In between, the tests only check that your rule is monotonic and self-consistent, because
    there is no right answer there and pretending otherwise would be the same error the chapter is
    about.
    """
    raise NotImplementedError("problem 20.1")


def widen_until_it_fits(samples: np.ndarray, observation: float) -> float:
    """Problem 20.2 - the wrong repair, measured.

    A model disagrees with an observation. The easiest response is to make the model vaguer until
    it stops disagreeing.

    Return the factor by which the distribution's spread about its median would have to grow for
    ``observation`` to land inside the 90% interval. Scale the samples about their median; do not
    shift them.

    Then look at what that does to the interval. The model now agrees with the observation and can
    no longer distinguish between designs, which is the only thing it was for. A model that cannot
    be wrong has stopped being able to be useful, and this number is what that costs.
    """
    raise NotImplementedError("problem 20.2")
