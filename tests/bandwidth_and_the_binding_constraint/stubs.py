"""Chapter 10's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations

import numpy as np


def size_for_all(
    request_hosts: np.ndarray, memory_hosts: np.ndarray, storage_hosts: np.ndarray
) -> np.ndarray:
    """Problem 10.1 - three chains, one purchase.

    Three chains each say how many hosts the workload needs: one from how many requests arrive at
    the busy hour, one from how much of the data has to stay in memory, one from how much of it has
    to sit on disk. Each argument is an array with one host count per future; position i in each is
    the same future. Return an array of the same length: for every future, the count that satisfies
    all three chains in it. One number for the whole array is not an answer.

    It is one function call and the point is which one. Work out what happens under each of the
    obvious wrong answers before you write the right one:

    * the **average** of the three falls short of the largest chain whenever the three differ;
    * the **working-set** chain, taken because it wins most often, is too small whenever another
      chain asks for more - which the next problem shows is more often than not;
    * **adding** them buys more than any chain asked for: a fleet for a workload nobody has.
    """
    raise NotImplementedError("problem 10.1")


def cost_of_sizing_on_one(
    chosen: np.ndarray, others: tuple[np.ndarray, ...]
) -> tuple[float, float]:
    """Problem 10.2 - what it costs to size on the chain that usually wins.

    Suppose you size on ``chosen`` alone - the working-set chain, say, because in more of the
    futures than any other it asks for the most. ``others`` is a tuple of the chains you ignored.
    Each is an array with one host count per future, all the same length. Return two numbers, as a
    tuple:

    * the fraction of futures, between 0 and 1, in which that fleet is **too small**, because some
      other chain asks for strictly more. A tie is not too small;
    * the median shortfall **in those futures only**, in hosts.

    A chain that wins more often than either of the others can still lose to one of them more often
    than not. "Wins most often" is a statement about a three-way race, and "too small" is a
    statement about losing to anybody. A shortfall counted over every future includes a zero for
    each future where the chosen chain was big enough, and its median looks like a rounding error.
    Counted over the short futures only, it is not one, because a neglected chain that wins often
    wins by a lot.
    """
    raise NotImplementedError("problem 10.2")
