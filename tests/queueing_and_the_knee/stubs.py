"""Chapter 6's problems. Edit this file; the tests beside it say whether you are right.

The first asks you to write the formula the whole chapter is about. The second asks you to define
"the knee", which turns out not to have a definition and to need a decision instead.
"""

from __future__ import annotations

import numpy as np


def residence_time(service_time: float, utilisation: np.ndarray | float) -> np.ndarray:
    """Problem 6.1 - the formula, and the division that is the whole subject.

    A request takes ``service_time`` seconds of work. The system is ``utilisation`` busy, as a
    fraction between zero and one. Return how long the request takes in total, including the time
    it spends waiting.

    One division. Work out what you are dividing by before you look it up: if the system is busy
    a fraction of the time, what fraction of it is available to you, and what does that do to the
    time your work takes?

    Handle a utilisation of one or above. The formula divides by what is left of the system, and
    at one there is nothing left - returning an infinity is defensible and so is raising, but
    returning a large finite number is not, because somebody will put it in a slide.

    The test checks it against the curve the book publishes, swept out of the model, so your
    formula has to be the model's formula rather than one that happens to be close.
    """
    raise NotImplementedError("problem 6.1")


def knee_at(tolerance: float) -> float:
    """Problem 6.2 - where is the knee?

    Return the utilisation at which a request takes ``tolerance`` times as long as it would on an
    idle system. For ``tolerance`` of 2.0, the utilisation at which everything takes twice as long.

    Derive it algebraically from your answer to 6.1 rather than searching for it numerically. It
    is one line, it inverts cleanly, and having the closed form is what turns "the knee" from a
    thing people gesture at into a number you can put in a headroom rule.

    Then read what comes out for a few tolerances, and notice that **there is no knee**. The curve
    has no special point - it is smooth everywhere, and the place people point at when they say
    "the knee" is simply the place where the slope first exceeded what they were willing to put up
    with. That is a decision about tolerance, not a discovery about queues, and ch11 is about
    making it deliberately.
    """
    raise NotImplementedError("problem 6.2")
