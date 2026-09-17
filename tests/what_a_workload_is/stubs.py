"""Chapter 1's problems. Edit this file; the tests beside it say whether you are right.

The first two are about telling three kinds of quantity apart, which sounds like pedantry until
the first time somebody sizes a retention store from a rate. The other two are about the file
itself: the smallest one the build will accept, and one that loads and is still wrong.
"""

from __future__ import annotations

from sizing.dsl import Model


def stocks_and_flows(model: Model) -> dict[str, str]:
    """Problem 1.1 - which quantities are levels, and which are rates?

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
    raise NotImplementedError("problem 1.1")


def daily_volume(model: Model) -> Model:
    """Problem 1.2 - turn a rate into a volume, and make the build agree.

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
    raise NotImplementedError("problem 1.2")


def smallest_model_that_builds() -> str:
    """Problem 1.3 - the smallest model this repository will accept.

    Return the *text* of a model file, as YAML, that:

    * declares a model name and a title;
    * has exactly one ``input`` node and one ``derived`` node;
    * declares one output;
    * passes ``sizing.evaluate.check_units`` with no problems;
    * passes every rule in ``scripts/verify-models.py`` that applies to it.

    That last clause is the problem. Read the eight rules at the top of that script before
    writing anything: an input with no provenance source, or a node that feeds no output, will be
    refused, and the refusal is the thing you are here to meet.

    Return the YAML as a string. The test writes it to a file and loads it exactly as the build
    would.
    """
    raise NotImplementedError("problem 1.3")


def a_model_that_does_not_typecheck() -> str:
    """Problem 1.4 - break it on purpose, in a way that still loads.

    Return the text of another model file: structurally valid, loadable, and **wrong about
    units**. A node must declare a unit that its own formula cannot produce.

    Not a typo, and not an unknown unit - those fail at load, which is a different and less
    interesting failure. This one has to load cleanly and then be refused by the dimensional
    pass, because that is the class of error a spreadsheet cannot see at all: every cell holds a
    number, every number multiplies, and the answer is confidently wrong.

    The test asserts the model loads, that ``check_units`` reports at least one problem, and that
    the message names the node. Make the error one you could imagine somebody making.
    """
    raise NotImplementedError("problem 1.4")
