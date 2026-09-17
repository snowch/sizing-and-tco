"""Chapter 11's problems. Edit this file; the tests beside it say whether you are right.

Both are about the moment a sizing model stops producing a number and starts producing a choice.
"""

from __future__ import annotations


def nodes_for_risk(target_p_over: float) -> int:
    """Problem 11.1 - size to a risk, not to a point estimate.

    Return the smallest number of nodes to purchase for which the storage model's capacity
    ceiling is breached in at most ``target_p_over`` of its samples.

    Use the model. Load ``models/storage_cluster/model.yaml``, override ``nodes_purchased``, and
    read ``fill_level``'s ``p_over_limit`` out of the evaluation. Search - the relationship is
    monotonic, so a bisection is a few lines and is much faster than stepping, which matters
    because each evaluation samples the whole graph.

    Reduce the sample count while you search and put it back for the final answer. A search that
    takes a minute is a search nobody runs twice, and the precision you need to compare candidates
    is much lower than the precision you need to report one.

    This is what sizing actually is. ch11's point estimate recommends a number; this asks the
    model a question somebody can be accountable for.
    """
    raise NotImplementedError("problem 11.1")


def cost_of_certainty(from_risk: float, to_risk: float) -> float:
    """Problem 11.2 - what a percentage point of risk costs.

    Return the additional five-year total cost of moving from a design that breaches the capacity
    ceiling in ``from_risk`` of samples to one that breaches it in ``to_risk``.

    Use your answer to 12.1 to find each node count, then read the median five-year total at each.

    Then look at the shape of the answer as ``to_risk`` falls. The cost of removing risk is not
    linear in the risk removed - it climbs, steeply, and the last few percentage points cost more
    than all the ones before them. That is the argument ch20 has to put to somebody, and having
    the number is the difference between an argument and a preference.
    """
    raise NotImplementedError("problem 11.2")
