"""Chapter 12's problems. Edit this file; the tests beside it say whether you are right.

Both are about the moment a sizing model stops producing a number and starts producing a choice.
"""

from __future__ import annotations

from collections.abc import Callable


def hosts_for_risk(risk_at: Callable[..., float], target: float) -> int:
    """Problem 12.1 - size to a risk, not to a point estimate.

    Return the smallest number of hosts for which the *utilisation at the busy hour* row of the
    ceilings table is past its limit in at most ``target`` of the model's draws. That share is the
    *Over limit* column of that row.

    ``risk_at(hosts)`` asks the model: it works the web service through with that many hosts in the
    fleet and returns the share of its draws in which that ceiling is past its limit.
    ``risk_at(hosts, samples=n)`` does the same over ``n`` draws instead of the full number.

    Search — the relationship is monotonic, so a bisection is a few lines and is much faster than
    stepping, which matters because each call works the whole graph. Reduce the number of draws
    while you search and put it back for the final answer. Comparing candidates needs much less
    precision than reporting one.

    The tests hold the answer to the target exactly, at the full number of draws. The model draws
    the same futures every time, so a fleet always gets the same share at the full number; an answer
    one host too small misses the target, and one host too large is not the smallest.

    This is what sizing is: the chapter's point estimate recommends a number; this asks the model a
    question you can be held to.
    """
    raise NotImplementedError("problem 12.1")


def cost_of_certainty(risk_at: Callable[..., float], from_risk: float, to_risk: float) -> int:
    """Problem 12.2 - what a percentage point of risk costs, in hosts.

    Return the additional hosts between the fleet your ``hosts_for_risk`` finds for ``from_risk``
    and the one it finds for ``to_risk``, asking the same ``risk_at`` both times. Moving to a
    smaller risk costs hosts; moving the other way gives them back, so the sign matters.

    Then look at the shape of the answer as ``to_risk`` falls. Removing risk does not cost the same
    at every point: the last few percentage points cost more hosts than the ones before them, and
    by more than a little. Part III has said nothing about money, so the answer is counted in
    machines. ch21 prices the same pair of fleets, and that price is the argument it has to put to
    the person whose decision it is. The count is where the argument starts.
    """
    raise NotImplementedError("problem 12.2")
