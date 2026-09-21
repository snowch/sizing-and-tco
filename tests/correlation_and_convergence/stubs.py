"""Chapter 14's problems. Edit this file; the tests beside it say whether you are right.

No answer key. Each test derives what it expects from the problem's own terms.
"""

from __future__ import annotations

from sizing.dsl import Model


def spread_at(samples: int, replicates: int) -> float:
    """Problem 14.1 — show the square-root law yourself.

    Return the *run-to-run spread* of the 95th percentile of the web service's five-year total:
    run the model ``replicates`` times at ``samples`` draws, each with a different seed, take the
    p95 of each run, and return how far those p95 values spread from run to run, measured as their
    standard deviation, since that is the quantity the law is about.

    That is the quantity one-over-root-n governs. The interval itself is not — ch14 is mostly
    about the difference, and this problem is where you convince yourself.

    Use ``sizing.evaluate.evaluate`` with a replaced scenario; you do not have to rebuild the
    sampler. The test calls this at several sample counts and asserts that the value you return
    falls as one over the square root of the count, to a tolerance it computes rather than one
    that is written down.
    """
    raise NotImplementedError("problem 14.1")


def correlated_model(model: Model, a: str, b: str, rho: float) -> Model:
    """Problem 14.2 — correlate two inputs without disturbing their distributions.

    Return a copy of ``model`` that declares a rank correlation ``rho`` between inputs ``a`` and
    ``b``, with a ``because`` saying why they move together: the chapter calls the reason the
    required column. Both are inputs with distributions; ``rho`` is the rank correlation the
    modeller wants, not whatever intermediate quantity the method happens to need.

    The test then checks two things, and the second is the one that matters:

    * the interval on an output fed by both inputs is **wider** than it was;
    * each input's own distribution is **unchanged** — same values, same percentiles, only the
      pairing differs.

    If you find yourself adjusting the values rather than reordering them, stop and re-read the
    section on why the obvious approach is wrong.
    """
    raise NotImplementedError("problem 14.2")
