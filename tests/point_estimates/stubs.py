"""Chapter 1's problems. Edit this file; the tests beside it say whether you are right.

The first three are about what a point estimate hides: how far one input can move, how far six move the answer together, and which kind of model you hold. None needs a sampler yet.

The fourth has no test. It is about a system you run, and there is no oracle for that.
"""

from __future__ import annotations


def spread_of_each(bands: dict[str, tuple[float, float]]) -> dict[str, float]:
    """Problem 1.1 - how uncertain is each input?

    ``bands`` maps the six inputs to their bottom and top values::

        bands = {
            'annual_growth': (bottom, top),
            'service_demand': (bottom, top),
            ...
        }

    Return a dictionary mapping each name to top/bottom. One division per input.
    """
    raise NotImplementedError("problem 1.1")


def spread_on_paper() -> float:
    """Problem 1.2 - how uncertain are they together?

    Look at the taxi table in the chapter: run 1 costs £3,125, run 4 costs £7,800.

    Return the ratio: run 4 cost divided by run 1 cost.
    """
    raise NotImplementedError("problem 1.2")


def stages_and_kinds() -> list[str]:
    """Problem 1.3 - which kind of model is this?

    The chapter shows three model descriptions: A, B, and C.

    Return a list of three strings, each ``"cost"`` or ``"sizing"``, in order: A, B, C.

    A **cost model** has a deterministic structure with uncertain parameters.
    A **sizing model** adds a measured constant or a ceiling.

    Read each description and decide by looking for measured constants and ceilings.
    """
    raise NotImplementedError("problem 1.3")
