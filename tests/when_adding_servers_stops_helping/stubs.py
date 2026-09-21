"""Chapter 7's problems. Edit this file; the tests beside it say whether you are right.

Two coefficients, fitted from measurements you could actually take, and one square root that tells
you where the money stops working.
"""

from __future__ import annotations

import numpy as np


def throughput(
    hosts: np.ndarray | float, one_host: float, contention: float, crosstalk: float
) -> np.ndarray:
    """Problem 7.1 - the scalability law, written out.

    ``one_host`` is what a single machine achieves alone. ``contention`` is the fraction of the
    work that cannot be done in parallel. ``crosstalk`` is the cost of machines having to agree
    with each other. Return the throughput of ``hosts`` machines.

    Two terms in the denominator and they behave differently, which is the whole of the chapter:

    * contention costs a fixed share of every machine you add - it grows with the *count*, and it
      flattens the curve;
    * crosstalk is machines coordinating with each other, so it grows with the number of *pairs* -
      and it is what makes the curve turn over and come back down.

    With crosstalk at zero you have Amdahl's ceiling: the curve flattens and stays flat. With both
    at zero you have the straight line nobody has ever measured.

    The test checks it against the sweep the book publishes, so it has to be the model's formula
    and not one that happens to be close near the middle.
    """
    raise NotImplementedError("problem 7.1")


def fit(measurements: list[tuple[float, float]]) -> tuple[float, float, float]:
    """Problem 7.2 - the two coefficients, from measurements somebody could actually take.

    ``measurements`` is a list of ``(hosts, throughput)`` pairs. You will usually have three: one
    machine, the fleet you have, and the fleet you had before you grew it. That is not much
    data and it is what exists.

    Return ``(one_host, contention, crosstalk)``.

    Three unknowns, so three measurements determine them exactly - solve, do not optimise. With
    the one-machine measurement in hand, ``one_host`` falls straight out, and the remaining two
    come from two linear equations once you rearrange the law to put the denominator on the other
    side. Write the rearrangement down before you code it; it is the part worth understanding.

    Then notice what you have done. You have fitted a two-parameter curve, extending to hundreds
    of machines, from three points clustered at the low end. ch07 says what that is worth.
    """
    raise NotImplementedError("problem 7.2")


def peak_hosts(contention: float, crosstalk: float) -> float:
    """Problem 7.3 - where adding machines stops helping.

    Return the host count at which throughput is greatest, from the two coefficients alone.

    Differentiate your answer to 7.1 with respect to the host count and set it to zero. It comes
    out as a square root and it is worth the five minutes: it says the peak is a property of the
    *software* - of how much it serialises and how much it coordinates - and that no budget moves
    it.

    Handle zero crosstalk. With no coordination cost the curve never turns over, and the honest
    answer is that there is no peak: raise, or return an infinity. A large number is not the
    same answer.
    """
    raise NotImplementedError("problem 7.3")
