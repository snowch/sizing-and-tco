"""Chapter 1's problems. Edit this file; the tests beside it say whether you are right.

The first two are about what a single number leaves out: how far a chain of uncertain quantities
can move, and which of two kinds of model you are holding. Neither needs a sampler — the chapter
is about what a point estimate hides, not yet about how to measure it.

The third has no test. It is about a system you actually run, and there is no oracle for that.
"""

from __future__ import annotations

from sizing.dsl import Model


def spread_of_each(model: Model) -> dict[str, float]:
    """Problem 1.1 - how uncertain is each input, on its own?

    Return a dictionary mapping the name of **every input that declares a lognormal
    distribution** to the ratio of its 90th percentile to its 10th.

    That ratio is the honest width of one quantity: a node declaring ``p10: 1.12, p90: 1.6``
    is a claim that the value is four times out of five somewhere in a band whose top is about
    1.43 times its bottom. Nodes that declare no distribution are not in the answer — somebody
    has decided they are known well enough to fix, and whether that is true is ch03's subject.

    Read the distributions off the model. Do not sample anything.
    """
    raise NotImplementedError("problem 1.1")


def spread_of_the_chain(model: Model) -> float:
    """Problem 1.1 - and how uncertain are they together?

    Return what those ratios become when the quantities are multiplied along a chain: the width
    of a product of uncertain quantities, in the same units as ``spread_of_each`` — a ratio of a
    high estimate to a low one.

    This calculation assumes every input is at its p10 at the same moment and then at its p90 at
    the same moment — a stronger claim than anybody's data supports, and ch13 is where sampling
    replaces it. What this version has over that one is that it needs nothing but the numbers
    already in the file, and what comes out is still far wider than any single input. That is the thing a
    point estimate cannot say, and you can reach it on paper.
    """
    raise NotImplementedError("problem 1.1")


def kind_of(model: Model) -> str:
    """Problem 1.2 - which of the two kinds of model is this?

    Return ``"cost"`` or ``"sizing"``.

    A **cost model** has a deterministic structure with uncertain parameters: accounting
    identities and physics, where sampling the inputs is genuinely sufficient. A **sizing model**
    has the same structure and adds at least one of two things — a constant somebody had to
    measure, or a limit the system runs into — and neither of those is something a chain of
    multiplications can represent.

    Decide by reading the model. The test decides from the node types the loader produced, which
    is the same rule ``scripts/verify-models.py`` applies to every model in this repository.
    """
    raise NotImplementedError("problem 1.2")


def what_decides_it(model: Model) -> list[str]:
    """Problem 1.2 - and which nodes make it that?

    Return the names of the nodes that decide the answer to ``kind_of``, sorted. For a sizing
    model that is every measured constant and every ceiling in it. For a cost model it is the
    empty list, because nothing in a cost model does this job.

    The point of naming them: a sizing model is not a mood. It is a specific short list of
    quantities that a chain of multiplications is quietly lying about, and you can write it down.
    """
    raise NotImplementedError("problem 1.2")
