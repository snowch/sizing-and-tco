"""Chapter 23's problems. Edit this file; the tests beside it say whether you are right.

Both are about a break-even: the value of one assumption at which the seller's saving is zero.
A break-even is what a seller can defend when the saving itself rests on guesses about a customer
the seller cannot see.
"""

from __future__ import annotations

from collections.abc import Callable


def break_even_transfer(saving_at: Callable[[float], float]) -> float:
    """Problem 23.1 - how much of the benchmark has to carry over?

    The seller's benchmark says one proposed host does the work of several of the customer's. The
    transfer factor is the share of that advantage that survives on the customer's own work: one
    if the benchmark is the customer's workload, less if it is not.

    ``saving_at(transfer)`` is the seller's model at its point estimate, run on ch22's customer.
    Hand it a transfer factor and it returns the five-year saving in dollars: the customer's
    spend as it is, minus the spend with the product. Everything else is pinned, including a
    share of the spend that scales, which the test chooses.

    Return the transfer factor at which the saving is zero, to within a dollar of saving.

    The test builds ``saving_at`` for three shares of the spend that scales, none of which the
    chapter prints a break-even for. The saving is not a straight line in the transfer factor:
    the proposed fleet is the customer's hosts divided by it. So either work the model's formula
    through by hand, or search: the saving rises as the transfer factor does, so bisection
    between a factor that loses money and one that saves it will find the zero.
    """
    raise NotImplementedError("problem 23.1")


def smallest_customer(saving_for: Callable[[float], float]) -> float | None:
    """Problem 23.2 - how small a customer can the seller take?

    The move costs the same whatever the customer's size, and every host the customer runs saves
    (or loses) the same amount a year after it. So a large enough customer pays for the move, if
    each host saves anything at all, and no customer does if each host loses.

    ``saving_for(hosts)`` is the seller's model at its point estimate. Hand it the number of hosts
    the customer runs and it returns the five-year saving in dollars. Everything else is pinned,
    including a share of the spend that scales and a transfer factor, which the test chooses.

    Return the number of hosts at which the saving is zero, to within a dollar of saving. If no
    number of hosts pays for the move, return ``None``: that answer is right for some of the cases
    the test tries, and a negative number of hosts is not a customer.

    The saving is a straight line in the number of hosts, so two evaluations fix it.
    """
    raise NotImplementedError("problem 23.2")
