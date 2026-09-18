"""Chapter 5's problems. Edit this file; the tests beside it say whether you are right.

Little's law is one multiplication. Both problems are about what that multiplication lets you
infer, which is more than people expect in one direction and much less in the other.
"""

from __future__ import annotations


def concurrency(arrival_rate: float, residence_time: float) -> float:
    """Problem 5.1 - the law itself.

    ``arrival_rate`` is requests per second. ``residence_time`` is how long each one stays, in
    seconds, from arriving to leaving - queueing included. Return how many are in the system at
    any moment.

    One multiplication. The test checks it against the service tier model's own node, which is
    computed by a different route through the graph, so agreeing is evidence rather than
    tautology.

    Worth knowing what you are *not* assuming. Nothing about how requests arrive, nothing about
    the order they are served in, nothing about the distribution of anything. Only that the system
    is in a steady state - as much going out as coming in, over the window you are looking at.
    That is why this is the one relationship in Part II that is always true.
    """
    raise NotImplementedError("problem 5.1")


def residence_from_observation(in_flight: float, arrival_rate: float) -> float:
    """Problem 5.2 - the law backwards, which is how it is actually used.

    You almost never know residence time. You know how many requests are in flight, because a
    connection count or a thread-pool gauge is trivial to expose, and you know the arrival rate,
    because everybody counts requests.

    Return the residence time those two imply, in seconds.

    This is the useful direction and it is why the law is worth knowing. A latency you cannot
    measure directly falls out of two numbers you already have - and it is the *true* latency,
    including every queue the request sat in on the way, which is generally not what an
    application's own timer reports.
    """
    raise NotImplementedError("problem 5.2")
