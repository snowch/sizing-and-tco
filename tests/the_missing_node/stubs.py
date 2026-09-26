"""Chapter 20's problems. Edit this file; the tests beside it say whether you are right.

Three problems about a model that is wrong in shape. The first two ask the question that comes
before any repair: how would you know? The third is the repair, graded against a figure the model
file does not contain: an invented monthly invoice average, kept in that problem's test.
"""

from __future__ import annotations

import numpy as np


def is_refuted(samples: np.ndarray, observed: np.ndarray) -> bool:
    """Problem 20.1 - what would count as evidence against the model?

    ``samples`` is a model's output distribution. ``observed`` is every figure you have from the
    real system the model was supposed to describe, one per observation: a single number in an
    array of one, a year of invoices in an array of twelve.

    Return whether the set refutes the model.

    The whole problem is in the word "refuted", and the trap is that a 90% interval is *supposed*
    to be missed one time in ten. One observation outside it is not evidence; it is the expected
    behaviour of an interval that is doing its job. A model rejected on that basis would be
    rejected roughly whenever it was right.

    Two things bear on the verdict, and a rule has to weigh both: how much of the model's belief
    lies beyond each observation, and how many observations you have. A figure the model puts a
    twentieth of its belief beyond is unremarkable once and damning fifty times over; a figure it
    puts none of its belief beyond is damning on its own. So a rule is a threshold on how
    surprising the whole set would be if the model were right. State one that holds together, and
    implement it.

    The tests check the cases at both ends: a single miss just outside the interval is never a
    refutation, and an observation far enough out that no plausible model produces it always is,
    however few of them you have. In between, the tests only check that your rule is monotonic
    in both directions - never less damning with more copies of the same figure, never less
    damning further out - because there is no right answer there and pretending otherwise would
    be the same error the chapter is about.
    """
    raise NotImplementedError("problem 20.1")


def widen_until_it_fits(samples: np.ndarray, observation: float) -> float:
    """Problem 20.2 - the wrong repair, measured.

    A model disagrees with an observation. The easiest response is to make the model vaguer until
    it stops disagreeing.

    Return the factor by which the distribution's spread about its median would have to grow for
    ``observation`` to land inside the 90% interval. Scale the samples about their median; do not
    shift them. Scaling the output's own draws stands in for widening the inputs, which is what
    somebody would do to the file: the same repair, one step downstream. The factor is at least
    one, because an observation already inside needs no widening.

    Then look at what that does to the interval. The model now agrees with the observation, and the
    interval becomes that many times wider - every draw moves away from the median by that factor.
    The median does not move, so the answer looks the same. The interval now contains figures the
    model used to rule out, so fewer observations could show it wrong; a model that cannot be wrong
    has stopped being able to be useful, and this number is what that costs.
    """
    raise NotImplementedError("problem 20.2")
