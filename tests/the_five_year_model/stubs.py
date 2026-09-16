"""Chapter 18's problems. Edit this file; the tests beside it say whether you are right.

Both are about what happens at the seam between two models, which is where most real cost models
are actually joined and where most of them quietly lose their uncertainty.
"""

from __future__ import annotations

import numpy as np


def price_from_storage_model() -> np.ndarray:
    """Problem 18.1 - carry a distribution across a model boundary.

    The observability model buys storage at a price per usable terabyte per month. The storage
    model computes exactly that quantity. Today the observability model declares it as an
    assumption with its own invented distribution, which is a way of not joining them.

    Return the storage model's ``cost_per_usable_tb_month`` as a **sample array** from its
    reference scenario, so that the observability model could be driven by it.

    The whole array, not a summary. A point estimate handed across a seam is the failure mode this
    problem exists to show you, and 18.2 measures what it costs.
    """
    raise NotImplementedError("problem 18.1")


def joined_interval(use_distribution: bool) -> tuple[float, float]:
    """Problem 18.2 - what a point estimate costs at the seam.

    Evaluate the observability model's ``known_storage_cost`` twice.

    With ``use_distribution`` true, drive ``storage_price`` from the storage model's actual
    sampled unit cost - the array from 18.1.

    With it false, drive ``storage_price`` from a single number: the median of that same array.
    This is what everybody does. Model A produces a figure, somebody writes the figure down, and
    model B treats it as known.

    Return the 5th and 95th percentiles of ``known_storage_cost`` in each case.

    You will need to sample the downstream model yourself rather than through
    ``sizing.evaluate``, because the DSL has no node kind for "a distribution that came from
    another model" - and noticing that gap is part of the problem. Say in a comment whether you
    think it should have one.
    """
    raise NotImplementedError("problem 18.2")
