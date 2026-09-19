"""Chapter 10's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations

import numpy as np


def size_for_all(
    request_hosts: np.ndarray, memory_hosts: np.ndarray, storage_hosts: np.ndarray
) -> np.ndarray:
    """Problem 10.1 - three chains, one purchase.

    Three independent chains each say how many hosts the workload needs: one from how many
    requests arrive at the busy hour, one from how much of the data has to stay in memory, one
    from how much of it has to sit on disk. Return, for every sample, the count that satisfies all
    three.

    It is one function call and the point is which one. Work out what happens under each of the
    obvious wrong answers before you write the right one:

    * take the **average** of the three, and the fleet satisfies none of them;
    * take the **working-set** chain because it wins most often, and you are under-provisioned
      whenever it does not - which the next problem shows is most of the time;
    * **add** them, and you have bought a fleet for a workload nobody has.
    """
    raise NotImplementedError("problem 10.1")


def cost_of_sizing_on_one(
    chosen: np.ndarray, others: tuple[np.ndarray, ...]
) -> tuple[float, float]:
    """Problem 10.2 - what it costs to size on the chain that usually wins.

    Suppose somebody sizes on ``chosen`` alone - the working-set chain, say, because in more of
    the samples than any other it is the one that asks for the most. ``others`` are the chains
    they ignored. Return two numbers:

    * the fraction of samples in which that fleet is **too small**, because some other chain
      wanted more;
    * the median shortfall **in those samples only**, in hosts.

    The first is the one people do not expect. A chain that wins more often than either of the
    others still loses to one of them more often than not, because "wins most often" is a
    statement about a three-way race and "too small" is a statement about losing to anybody. The
    second is the one they do not compute: a shortfall conditional on being short is not a
    rounding error, because the cases where a neglected chain wins are the cases where it wins by
    a lot.
    """
    raise NotImplementedError("problem 10.2")
