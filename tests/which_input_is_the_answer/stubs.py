"""Chapter 19's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations

from collections.abc import Callable


def tornado(
    swings: dict[str, tuple[float, float]], output_at: Callable[[dict[str, float]], float]
) -> list[tuple[str, float]]:
    """Problem 19.1 - build the chart yourself.

    ``swings`` maps each uncertain input of the web service model to the two ends of its band:
    its tenth and its ninetieth percentile, as its declared distribution gives them. The swing
    comes from the distribution rather than from the slider range, so that every bar is answering
    the same question - "across the middle eighty per cent of what this input could be" - and an
    input somebody gave a wide slider to does not get a long bar for free.

    ``output_at(held)`` is the model at a point. Hand it a dictionary of input names and values
    and it returns the number of hosts the model recommends with those inputs held there and
    everything else at its point value. ``output_at({})`` is the point estimate itself.

    Return a list of ``(input_name, span)`` pairs, sorted with the largest span first: for each
    input in ``swings``, how far the output moves when that input alone is swung from one end of
    its band to the other. Two calls per input; you do not have to sample.

    The test builds both arguments from the model file and the reference scenario. It leaves out
    anything the scenario has already pinned, anything the model cannot evaluate, and the
    measured constants: their uncertainty is a standard error rather than a band, and the build
    swings them by a different rule.
    """
    raise NotImplementedError("problem 19.1")


def interaction_gap(
    output_at: Callable[[dict[str, float]], float], swings: dict[str, tuple[float, float]]
) -> float:
    """Problem 19.2 - what one-at-a-time misses.

    ``swings`` holds exactly two inputs, each mapped to the two ends of its band, its tenth and
    its ninetieth percentile. ``output_at(held)`` returns one output of the model with the named
    inputs held at the given values and everything else at its point value, as in problem 19.1.

    Swing the first input alone from the low end of its band to the high end and record the
    change in the output. Swing the second alone and record that. Then swing **both together**
    and record that.

    Return the difference between the change when both move and the sum of the two individual
    changes, as a fraction of the sum of the two individual changes. Dividing by the sum of the
    separate changes, not by the joint change, shows how far the tornado's bars, added up, miss
    the joint move.

    Zero means the two inputs do not interact here and the tornado's bars can be added up. Anything
    else means they do, and a chart of one-at-a-time swings is understating - or overstating -
    what happens when the world moves two things at once.

    When you swing one input alone, the other is not included in the dictionary you pass to
    ``output_at``, so it is held at its point value.

    The test names the two pairs: one that meets in a product on the way to the raw data, and one
    that meets in a sum on the way to the annual running cost. Where two inputs meet in a product,
    a gap usually shows, because a product is not additive in its factors - which is the point, and
    is why a tornado is a guide to what to measure rather than a decomposition of the answer.
    """
    raise NotImplementedError("problem 19.2")
