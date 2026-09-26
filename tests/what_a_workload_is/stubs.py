"""Chapter 2's problems. Edit this file; the tests beside it say whether you are right.

Problem 2.1 is about telling a stock from a flow by what a quantity means, and checking that
against the unit the model declares. Problems 2.3 and 2.4 are about the file itself: the smallest
one the build will accept, and one that loads and is still wrong. Problem 2.2 is not here: you
edit ``problem_2_daily_ingest.yaml``, a fragment of the model file, beside this one.
"""

from __future__ import annotations


def stocks_and_flows(nodes: dict[str, str]) -> dict[str, str]:
    """Problem 2.1 - which quantities are levels, and which are rates?

    ``nodes`` maps the name of **every node** in the observability model to what it is, in
    words: the label the file gives it, or its note, or failing both its name. Return a
    dictionary mapping every one of those names to one of three strings:

    ``"stock"``
        A level. How much there is, right now. Storage held, series alive, requests in flight.
    ``"flow"``
        A rate. How much per unit of time. Bytes ingested per second, requests arriving per
        second, dollars per year.
    ``"neither"``
        A pure number, a ratio, a price per unit of something that is not time, a duration.

    Classify by **meaning**, from the name and the words beside it. The test classifies by
    **dimension**, from the unit the model declares - a flow has time in its denominator, a stock
    does not, and a duration has time in its numerator. If your reading of what a quantity *is*
    and the unit somebody declared for it disagree, one of the two is wrong, and finding out which
    is the exercise.

    Why it matters: a stock and a flow are added, compared and budgeted differently, and the two
    commonest sizing errors in this book's experience are multiplying a flow by nothing and
    calling it a stock, and sizing a store from a peak rate that only holds for an hour.
    """
    raise NotImplementedError("problem 2.1")


def smallest_model_that_builds() -> str:
    """Problem 2.3 - the smallest model this repository will accept.

    Return the *text* of a model file, as YAML, that:

    * declares a model name and a title;
    * has exactly one ``input`` node and one ``derived`` node;
    * declares one output;
    * passes ``sizing.evaluate.check_units`` with no problems;
    * passes every rule in ``scripts/verify-models.py`` that applies to it.

    That last clause is the problem. The rules are listed in Appendix A of the book, under
    "What the build checks", and at the top of ``scripts/verify-models.py``. Read them before
    writing anything. An input with no ``decided`` line or no provenance source, or a node that
    feeds no output, is refused, and the refusal is what you are here to meet.

    Return the YAML as a string. The test writes it to a file and loads it exactly as the build
    would.
    """
    raise NotImplementedError("problem 2.3")


def a_model_that_does_not_typecheck() -> str:
    """Problem 2.4 - break it on purpose, in a way that still loads.

    Return the text of another model file: structurally valid, loadable, and **wrong about
    units**. A node must declare a unit that its own formula cannot produce.

    Not a typo, and not an unknown unit - those fail at load, which is a different and less
    interesting failure. This one has to load cleanly and then be refused by the dimensional
    pass, because that is the class of error a spreadsheet cannot see at all: every cell holds a
    number, every number multiplies, and the answer is confidently wrong.

    The test asserts the model loads, that ``check_units`` reports at least one problem, and that
    the message names the node. Make the error one you could imagine somebody making.
    """
    raise NotImplementedError("problem 2.4")
