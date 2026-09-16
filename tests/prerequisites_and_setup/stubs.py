"""Chapter 0's problems. Edit this file; the tests beside it say whether you are right.

Both are about the toolchain rather than about sizing. You are checking that the thing which
refuses a bad model on your machine is the same thing that refuses it in CI — because everything
the rest of the book claims rests on that being true.
"""

from __future__ import annotations


def smallest_model_that_builds() -> str:
    """Problem 0.1 - the smallest model this repository will accept.

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
    raise NotImplementedError("problem 0.1")


def a_model_that_does_not_typecheck() -> str:
    """Problem 0.2 - break it on purpose, in the one way that matters.

    Return the text of another model file: structurally valid, loadable, and **wrong about
    units**. A node must declare a unit that its own formula cannot produce.

    Not a typo, and not an unknown unit - those fail at load, which is a different and less
    interesting failure. This one has to load cleanly and then be refused by the dimensional
    pass, because that is the class of error a spreadsheet cannot see at all: every cell holds a
    number, every number multiplies, and the answer is confidently wrong.

    The test asserts the model loads, that ``check_units`` reports at least one problem, and that
    the message names the node. Make the error one you could imagine somebody making.
    """
    raise NotImplementedError("problem 0.2")
