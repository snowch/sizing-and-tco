"""Chapter 11's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations


def failure_reserve(hosts: int, tolerated_losses: int) -> float:
    """Problem 11.1 - the margin a host loss costs.

    A fleet of ``hosts`` machines has to survive losing ``tolerated_losses`` of them and still
    serve the busy hour. Return the fraction of the fleet's capacity that has to be kept free for
    that, as a number between zero and one.

    Two things follow from the answer. First, every fleet keeps one host free for each host it
    plans to lose, but as a share of the fleet a small fleet pays far more. Losing one host out of
    five costs a fifth of the capacity. If that capacity is not free beforehand, the lost host's
    share of the requests lands on survivors that are already busy. That is a capacity argument
    for larger pools, where each loss is a smaller share. It is not an argument for larger
    failure domains: a failure domain is the set of hosts one fault takes out together, and a
    larger one is worse.

    Second, the margin is for a *loss*, not for a failure. A host drained for a kernel upgrade
    removes the same capacity as one that has died. A rolling upgrade drains hosts on purpose,
    so planned work spends this margin by design.
    """
    raise NotImplementedError("problem 11.1")


def compose(margins: list[float]) -> float:
    """Problem 11.2 - two margins are not one margin twice.

    ``margins`` are separate reasons to keep capacity free: a rebuild reserve, a queueing
    margin, room for the growth between now and the next purchase. Each is a fraction between
    zero and one.

    Return the combined margin: the fraction of the system kept free once all of them are
    applied. If a quarter of the system is left doing the work, return 0.75.

    Do not add them. Work out what applying one margin and then another does to what is left.
    The combined margin is never as large as the sum. For large margins the sum is not even
    a fraction: three margins of ninety per cent add to more than the whole system, which is
    a clue.

    Then look at what three modest margins leave doing the work, and understand what a sizing
    conversation achieves when each margin is a separate reasonable request.
    """
    raise NotImplementedError("problem 11.2")
