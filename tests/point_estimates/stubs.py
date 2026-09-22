"""Chapter 1's problems. Edit this file; the tests beside it say whether you are right.

The first three are about what a single number leaves out: how far one uncertain quantity can
move, how far the six of them move the answer together, and which of two kinds of model you are
holding. None needs a sampler — the chapter is about what a point estimate hides, not yet about
how to measure it.

The fourth has no test. It is about a system you actually run, and there is no oracle for that.
"""

from __future__ import annotations

from collections.abc import Callable

from sizing.dsl import Model


def spread_of_each(bands: dict[str, tuple[float, float]]) -> dict[str, float]:
    """Problem 1.1 - how uncertain is each input, on its own?

    ``bands`` holds the six inputs the chapter has been using -- the ones the panel draws and the
    ones that can move a host count -- mapped to the two ends of each band, bottom first::

        bands = {
            'annual_growth': (bottom, top),
            'service_demand': (bottom, top),
            ...   # six in all, the six the chapter has been using
        }

    Return a dictionary mapping each of those names to the top of its band over its bottom. That
    is one division per input, and the next problem is what those six do together.

    The file writes the two ends one of two ways, and ``bands`` has already reduced both to a
    bottom and a top, so you do not have to care which. What the two kinds mean by their ends
    differs, and that is ch13's business rather than yours here.

    Nothing is drawn at random.
    """
    raise NotImplementedError("problem 1.1")


def spread_on_paper(
    bands: dict[str, tuple[float, float]], count_at: Callable[[dict[str, float]], float]
) -> float:
    """Problem 1.2 - and how uncertain are they together?

    ``bands`` is the same dictionary problem 1.1 handed you: the six inputs, each mapped to the
    two ends of its band, bottom first.

    ``count_at`` works the model through with the inputs you name held at the values you give,
    and returns the hosts it then recommends: the ``hosts_recommended`` output, the first row of
    the chapter's table. Call it with every input in ``bands`` held at the bottom of its band,
    all at once. Call it again with every one held at the top. Return the second count over the
    first: the same kind of number problem 1.1 gave you for one input, now for the answer.

    Then set it beside the six you got from problem 1.1. It is not the largest of them, and it is
    not their average.

    This is the arithmetic you could do on paper, and it claims something nobody's data supports:
    that every input sits at the same end of its band at the same moment. ch13 replaces that
    claim with a program that picks each input's value many times over. What this version has is
    that it needs nothing but the numbers already in the file, and what comes out is still wider
    than any one input can make it on its own. That is the thing a point estimate cannot say.
    """
    raise NotImplementedError("problem 1.2")


def kind_of(model: Model) -> str:
    """Problem 1.3 - which of the two kinds of model is this?

    Return ``"cost"`` or ``"sizing"``.

    A **cost model** has a deterministic structure with uncertain parameters: accounting
    identities and physics, where sampling the inputs is genuinely sufficient. A **sizing model**
    has the same structure and adds at least one of two things — a constant somebody had to
    measure, or a limit the system runs into — and neither of those is something a chain of
    multiplications can represent.

    Decide by reading the model. The test decides from the node types the loader produced, which
    is the same rule ``scripts/verify-models.py`` applies to every model in this repository.
    """
    raise NotImplementedError("problem 1.3")


def what_decides_it(model: Model) -> list[str]:
    """Problem 1.3 - and which nodes make it that?

    Return the names of the nodes that decide the answer to ``kind_of``, sorted. For a sizing
    model that is every measured constant and every ceiling in it. For a cost model it is the
    empty list, because nothing in a cost model does this job.

    The point of naming them: a sizing model is not a mood. It is a specific short list of
    quantities that a chain of multiplications is quietly lying about, and you can write it down.
    """
    raise NotImplementedError("problem 1.3")
