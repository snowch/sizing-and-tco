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


def new_hosts_for_requests(
    busy_cores: float,
    old_hosts: int,
    cores_per_old_host: float,
    cores_per_new_host: float,
    margin: float,
    routing: str,
) -> int:
    """Problem 10.3 - how many new hosts the requests need, when some old ones stay.

    ``busy_cores`` is how many cores the busy hour keeps busy. ``old_hosts`` are already in
    service, each with ``cores_per_old_host`` cores; every new host has ``cores_per_new_host``.
    ``margin`` is the queueing margin: a share of every host's cores the fleet keeps free, between
    0 and 1. Return the number of new hosts to buy, as a whole number, for ``routing``:

    * ``"capacity"``: the load balancer sends each host requests in proportion to its cores, so
      every host is equally busy and the two generations' cores add up;
    * ``"equal"``: every host gets the same share of the requests, so the smallest host in the
      pool is the busiest and reaches its margin first. With no old hosts, every host is a new
      one.    Routed equally, the old hosts carry the load if, on their own, each held to
    its own cores, they serve the busy hour below the margin; then the answer is
    no new hosts. The smallest host is a new one only once a new host exists.
    Either routing, the answer is never a negative number.
    """
    raise NotImplementedError("problem 10.3")
