"""Chapter 10's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations

import numpy as np


def size_for_both(capacity_nodes: np.ndarray, throughput_nodes: np.ndarray) -> np.ndarray:
    """Problem 10.1 - two chains, one purchase.

    Two independent chains each say how many machines the workload needs: one from how much there
    is to store, one from how fast it has to be read. Return, for every sample, the count that
    satisfies both.

    It is one function call and the point is which one. Work out what happens under each of the
    obvious wrong answers before you write the right one:

    * take the **average** of the two, and the cluster satisfies neither chain;
    * take the **capacity** one because it is usually larger, and you are under-provisioned
      whenever it is not;
    * **add** them, and you have bought a cluster for a workload nobody has.
    """
    raise NotImplementedError("problem 10.1")


def cost_of_ignoring_a_chain(
    capacity_nodes: np.ndarray, throughput_nodes: np.ndarray
) -> tuple[float, float]:
    """Problem 10.2 - what it costs to forget the chain that usually loses.

    Suppose somebody sizes on the capacity chain alone, because in most of the samples it is the
    larger of the two. Return two numbers:

    * the fraction of samples in which that cluster is **too small**, because the other chain
      wanted more;
    * the median shortfall **in those samples only**, in machines.

    The second is the one that matters and the one people do not compute. A constraint that binds
    rarely is easy to dismiss - and a shortfall conditional on it binding is not small, because the
    cases where the neglected chain wins are exactly the cases where it wins by a lot.
    """
    raise NotImplementedError("problem 10.2")
