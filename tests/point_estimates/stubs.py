"""Chapter 1's problems. Edit this file; the tests beside it say whether you are right.

The first three are about what a point estimate hides: how far one input can move, how far six move the answer together, and which kind of model you hold. None needs a sampler yet.

The fourth has no test. It is about a system you run, and there is no oracle for that.
"""

from __future__ import annotations

from collections.abc import Callable

from sizing.dsl import Model


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


def spread_on_paper(
    bands: dict[str, tuple[float, float]], count_at: Callable[[dict[str, float]], float]
) -> float:
    """Problem 1.2 - how uncertain are they together?

    ``count_at`` runs the model with inputs at the values you give, returning hosts_recommended.

    Call it with every input in ``bands`` at its bottom. Then at its top. Return the second count over the first.

    Set it beside the six from problem 1.1. It is not the largest and not their average.
    """
    raise NotImplementedError("problem 1.2")


def kind_of(model: Model) -> str:
    """Problem 1.3 - which kind of model is this?

    Return ``"cost"`` or ``"sizing"``.

    A **cost model** has a deterministic structure with uncertain parameters.
    A **sizing model** adds a measured constant or a ceiling.

    Decide by reading the model.
    """
    raise NotImplementedError("problem 1.3")


def what_decides_it(model: Model) -> list[str]:
    """Problem 1.3 - which nodes decide it?

    Return the node names that make it a sizing model, sorted. For a cost model, return empty.

    A sizing model is a specific list of quantities the multiplication is lying about.
    """
    raise NotImplementedError("problem 1.3")
