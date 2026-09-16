"""Chapter 2's problems. Edit this file; the tests beside it say whether you are right.

Both are about telling three kinds of quantity apart. It sounds like pedantry until the first
time somebody sizes a retention store from a rate.
"""

from __future__ import annotations

from sizing.dsl import Model


def stocks_and_flows(model: Model) -> dict[str, str]:
    """Problem 2.1 - which quantities are levels, and which are rates?

    Return a dictionary mapping **every node name** in ``model`` to one of three strings:

    ``"stock"``
        A level. How much there is, right now. Storage held, series alive, requests in flight.
    ``"flow"``
        A rate. How much per unit of time. Bytes ingested per second, requests arriving per
        second, dollars per year.
    ``"neither"``
        A ratio, a count, a price per unit of something that is not time, a duration.

    Classify by **meaning**, from the node's name, label and note. The test classifies by
    **dimension**, from the unit the model declares - a flow has time in its denominator, a stock
    does not, and a duration has time in its numerator. If your reading of what a quantity *is*
    and the unit somebody declared for it disagree, one of the two is wrong, and finding out which
    is the exercise.

    Why it matters: a stock and a flow are added, compared and budgeted differently, and the two
    commonest sizing errors in this book's experience are multiplying a flow by nothing and
    calling it a stock, and sizing a store from a peak rate that only holds for an hour.
    """
    raise NotImplementedError("problem 2.1")


def daily_volume(model: Model) -> Model:
    """Problem 2.2 - turn a rate into a volume, and make the build agree.

    The observability model knows how many bytes a second arrive. Nobody reasons in bytes a
    second; people reason in "how much a day", because that is what a retention conversation is
    about and what an invoice is denominated in.

    Return a copy of ``model`` with one more node, called ``daily_ingest``, giving the bytes that
    arrive in a day across metrics and logs together. Declare it in ``TB`` - terabytes a day, with
    the day already divided out, which is the form somebody can act on.

    You will need a node carrying a duration before the multiplication means anything, exactly as
    ``one_year`` and ``one_sample_per_series`` do elsewhere in this book. That is not a workaround:
    a rate times a pure number is still a rate, and the only thing that turns one into a volume is
    multiplying by an amount of time.

    The test checks the unit typechecks, and that the answer is the ingest rate multiplied by a
    day - derived from the model's own numbers at test time, so there is nothing to look up.
    """
    raise NotImplementedError("problem 2.2")
