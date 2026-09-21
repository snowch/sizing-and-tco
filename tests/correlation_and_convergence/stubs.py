"""Chapter 14's problems. Edit this file; the tests beside it say whether you are right.

No answer key. Each test derives what it expects from the problem's own terms.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def spread_at(run: Callable[[int, int], np.ndarray], samples: int, replicates: int) -> float:
    """Problem 14.1 — show the square-root law yourself.

    ``run(samples, seed)`` is one run of the web service model: that many draws of its five-year
    total, from that seed. The test builds it, so you do not have to touch the sampler; the seeds
    are yours to choose.

    Return the *run-to-run spread* of the 95th percentile of the total: call ``run``
    ``replicates`` times at ``samples`` draws, each with a different seed, take the p95 of each
    run, and return how far those p95 values spread from run to run, measured as their standard
    deviation, since that is the quantity the law is about.

    That is the quantity one-over-root-n governs. The interval itself is not — ch14 is mostly
    about the difference, and this problem is where you convince yourself.

    The test calls this at several sample counts and asserts that the value you return falls as
    one over the square root of the count, to a tolerance it computes rather than one that is
    written down.
    """
    raise NotImplementedError("problem 14.1")
