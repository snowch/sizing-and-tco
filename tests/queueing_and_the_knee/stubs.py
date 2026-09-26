"""Chapter 6's problems. Edit this file; the tests beside it say whether you are right.

The first asks you to write the formula the whole chapter is about. The second asks you to define
"the knee", which turns out not to have a definition and to need a decision instead.
"""

from __future__ import annotations

import numpy as np


def residence_time(service_time: float, utilisation: np.ndarray | float) -> np.ndarray:
    """Problem 6.1 - the formula.

    The formula is on this page in the first YAML. Your job is to write it as a function,
    deciding what to return at a utilisation of one and above. At one the division gives
    infinity; above one it gives a negative number. An infinity is defensible, as is an
    error. A large finite number is not, because somebody will put it in a slide.

    The model clamps utilisation, but it can only do that because its ceiling watches the
    uncapped value and reports **over**. Your function has nothing beside it, so you must not
    clamp when the utilisation is one or above.

    The utilisation may be one number or a numpy array of them. Return one answer per
    utilisation - a single number if the input is a number, an array if it is an array.

    The test checks it against the curve the book publishes, swept out of the model, so your
    formula has to be the model's formula rather than one that happens to be close.
    """
    raise NotImplementedError("problem 6.1")


def knee_at(tolerance: float) -> float:
    """Problem 6.2 - where is the knee?

    Return the utilisation at which a request takes ``tolerance`` times as long as it would on an
    idle system. For ``tolerance`` of 2.0, the utilisation at which everything takes twice as long.
    The tolerance multiplies the whole time in the system, waiting included.

    Derive it algebraically from your answer to 6.1 rather than searching for it numerically. It
    is one line and inverts cleanly. The closed form turns "the knee" from something people gesture
    at into a number you can put in a headroom rule.

    Then read what comes out for a few tolerances, and notice that there is no knee. The curve has
    no special point - it is smooth everywhere. The place people point at when they say "the knee"
    is where the slope first exceeded what they were willing to put up with. That is a decision
    about tolerance, not a discovery about queues, and ch11 is about making it deliberately.
    """
    raise NotImplementedError("problem 6.2")
