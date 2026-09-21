"""Chapter 18's problems. Edit this file; the tests beside it say whether you are right.

One graded problem, about the seam between two models: where most real cost models are joined,
and where most of them quietly lose their uncertainty.
"""

from __future__ import annotations

import numpy as np


def joined_interval(
    stored: np.ndarray, price: np.ndarray, use_distribution: bool
) -> tuple[float, float]:
    """Problem 18.1 - what a point estimate costs at the seam.

    The observability model buys storage at a price per terabyte per month, and the web service
    model computes exactly that quantity for the records on its own fleet. That is the seam. The
    test evaluates both models in their reference scenarios and hands you its two sides:
    ``stored`` is the observability model's ``known_stored``, in terabytes, one draw per sample;
    ``price`` is the web service model's ``cost_per_stored_tb_month``, one draw per sample. Their
    product is a storage cost per month - the downstream model's ``known_storage_cost``, with the
    upstream model's computed price in place of the assumption the file declares.

    Join them both ways, and return the 5th and 95th percentiles of the storage cost each time:

    * with ``use_distribution`` true, carry the price across **as a distribution**: draw by
      draw, the i-th stored figure priced at the i-th price;
    * with it false, carry it across **as its median**, one number. This is what everybody does.
      Model A produces a figure, somebody writes the figure down, and model B treats it as known.

    The test computes both intervals itself from the same two arrays and grades yours against
    them, so there is nothing to look up and nothing to approximate; ``sizing.mc.interval`` is
    the book's definition of a 90% interval. Predict the direction before you run it.

    The join is arithmetic on two arrays, outside ``sizing.evaluate``, and that is not an
    accident of the exercise. The DSL has no node kind for "a distribution that came from another
    model", so nothing in a model file can be driven by another model's draws - noticing that gap
    is part of the problem. Say in a comment whether you think it should have one.
    """
    raise NotImplementedError("problem 18.1")
