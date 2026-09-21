"""Chapter 11's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations


def failure_reserve(hosts: int, tolerated_losses: int) -> float:
    """Problem 11.1 - the margin a host loss actually costs.

    A fleet of ``hosts`` machines has to survive losing ``tolerated_losses`` of them and still
    serve the busy hour. Return the fraction of the fleet's capacity that has to be kept free for
    that, as a number between zero and one.

    Two things fall out of this that people get wrong in opposite directions.

    A small fleet pays an enormous margin. Losing one host out of five costs a fifth of the
    capacity, and if the margin is not there beforehand its share of the requests lands on
    survivors that are already busy. A large fleet pays almost nothing per host, which is a real
    argument for large failure domains and is not the argument people usually give for them.

    And the margin is for a *loss*, not for a failure. A host that is being drained for a kernel
    upgrade costs exactly the same capacity as one that has died - and planned work is far more
    common than failure, which is why this margin is spent most often on a Tuesday afternoon
    rather than on an incident.
    """
    raise NotImplementedError("problem 11.1")


def compose(margins: list[float]) -> float:
    """Problem 11.2 - two margins are not one margin twice.

    ``margins`` are independent reasons to keep capacity free: a rebuild reserve, a queueing
    margin, a headroom for the growth between now and the next purchase. Each is a fraction
    between zero and one.

    Return the single fraction of the system that is actually available once all of them are
    applied, expressed as **the margin** - so if a quarter of the system is usable, return 0.75.

    Do not add them. Work out what applying one margin and then another does to what is left, and
    notice that the answer is never as large as the sum, and that for large margins the sum is not
    even a fraction: adding three ninety per cent margins gets you a negative system, which is a
    clue.

    Then look at what a few realistic sets of margins actually leave you, and understand why a
    sizing conversation that treats each margin as a separate reasonable request ends with a
    cluster twice the size anybody intended.
    """
    raise NotImplementedError("problem 11.2")
