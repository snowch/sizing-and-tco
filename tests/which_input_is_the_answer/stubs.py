"""Chapter 18's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations

from sizing.dsl import Model, Scenario


def tornado(model: Model, scenario: Scenario, output: str) -> list[tuple[str, float]]:
    """Problem 18.1 - build the chart yourself.

    Return a list of ``(input_name, span)`` pairs, sorted with the largest span first: for each
    uncertain input, how far ``output`` moves when that input alone is swung from its own 10th to
    its own 90th percentile, with everything else held at its point value.

    Use ``sizing.evaluate.point`` with an overridden scenario; you do not have to sample. Get the
    swing from each input's declared distribution rather than from its slider range, so that every
    bar is answering the same question - "across the middle eighty per cent of what this input
    could be" - and an input somebody gave a wide slider to does not get a long bar for free.

    Skip anything the model cannot evaluate and anything the scenario has already pinned.
    """
    raise NotImplementedError("problem 18.1")


def interaction_gap(model: Model, scenario: Scenario, output: str, a: str, b: str) -> float:
    """Problem 18.2 - what one-at-a-time misses.

    Swing input ``a`` alone from its p10 to its p90 and record the change in ``output``. Swing
    ``b`` alone and record that. Then swing **both together** and record that.

    Return the difference between the change when both move and the sum of the two individual
    changes, as a fraction of the sum.

    Zero means the two inputs do not interact and the tornado's bars can be added up. Anything else
    means they do, and a chart of one-at-a-time swings is understating - or overstating - what
    happens when the world moves two things at once.

    Pick the pair the chapter names when you run it. A model built out of multiplications will
    always show some of this, because a product is not additive in its factors - which is the point,
    and is why a tornado is a guide to what to measure rather than a decomposition of the answer.
    """
    raise NotImplementedError("problem 18.2")
