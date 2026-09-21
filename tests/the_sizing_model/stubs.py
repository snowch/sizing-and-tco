"""Chapter 12's problems. Edit this file; the tests beside it say whether you are right.

Both are about the moment a sizing model stops producing a number and starts producing a choice.
"""

from __future__ import annotations


def hosts_for_risk(target_p_over: float) -> int:
    """Problem 12.1 - size to a risk, not to a point estimate.

    Return the smallest number of hosts for which the web service's queueing ceiling is breached
    in at most ``target_p_over`` of its samples.

    Use the model. Load ``models/web_service/model.yaml``, override ``hosts``, and read
    ``queueing_headroom``'s ``p_over_limit`` out of the evaluation. Search - the relationship is
    monotonic, so a bisection is a few lines and is much faster than stepping, which matters
    because each evaluation samples the whole graph.

    Reduce the number of draws while you search and put it back for the final answer. A search that
    takes a minute is a search nobody runs twice, and the precision you need to compare candidates
    is much lower than the precision you need to report one.

    This is what sizing actually is. ch12's point estimate recommends a number; this asks the
    model a question somebody can be accountable for.
    """
    raise NotImplementedError("problem 12.1")


def cost_of_certainty(from_risk: float, to_risk: float) -> int:
    """Problem 12.2 - what a percentage point of risk costs, in hosts.

    Return the additional hosts between the fleet your ``hosts_for_risk`` finds for ``from_risk``
    and the one it finds for ``to_risk``. Moving to a smaller risk costs hosts; moving the other
    way gives them back, so the sign matters.

    Then look at the shape of the answer as ``to_risk`` falls. Removing risk does not cost the same
    at every point: the last few percentage points cost more hosts than the ones before them, and
    by more than a little. Part III has said nothing about money, so the answer is counted in
    machines. ch21 prices the same pair of fleets, and that price is the argument it has to put to
    the person whose decision it is. The count is where the argument starts.
    """
    raise NotImplementedError("problem 12.2")
