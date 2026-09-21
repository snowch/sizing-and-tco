"""Chapter 5's problems. Edit this file; the tests beside it say whether you are right.

Little's law is one multiplication. Both problems are about what that multiplication lets you
infer, which is more than people expect in one direction and much less in the other.
"""

from __future__ import annotations

import numpy as np


def concurrency(
    arrival_rate: float | np.ndarray, residence_time: float | np.ndarray
) -> float | np.ndarray:
    """Problem 5.1 - the law itself.

    ``arrival_rate`` is requests per second. ``residence_time`` is how long each one stays, in
    seconds, from arriving to leaving - queueing included. Return how many are in the system at
    any moment. The test hands both as single numbers and then as arrays holding every future
    the model drew, so write it as arithmetic that works on either.

    One multiplication. The test checks it against the web service model's own node, which is
    the law written as a formula, at the point estimate and then across every future.

    Worth knowing what you are *not* assuming. Nothing about how requests arrive, nothing about
    the order they are served in, nothing about the shape of anything. Only that the system
    is in a steady state - as much going out as coming in, over the window you are looking at.
    That is why this is the one relationship in Part II that is always true.
    """
    raise NotImplementedError("problem 5.1")


def residence_from_observation(
    in_flight: float | np.ndarray, arrival_rate: float | np.ndarray
) -> float | np.ndarray:
    """Problem 5.2 - the law backwards, which is how it is actually used.

    You almost never know residence time. You know how many requests are in flight, because a
    connection count or a thread-pool gauge is trivial to expose, and you know the arrival rate,
    because everybody counts requests.

    Return the residence time those two imply, in seconds.

    This is the useful direction and it is why the law is worth knowing. A latency you cannot
    measure directly falls out of two numbers you already have - and it is the *true* latency,
    including every queue the request sat in on the way, which is generally not what an
    application's own timer reports.

    Then decide what to return when nothing is arriving. With no arrivals there is no residence
    time to infer: raise, or return an infinity, but not a number somebody could put in a slide.
    """
    raise NotImplementedError("problem 5.2")
