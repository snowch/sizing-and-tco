"""Chapter 14's problems. Edit this file; the tests beside it say whether you are right.

No answer key. Each test derives what it expects from the problem's own terms.
"""

from __future__ import annotations

from sizing.dsl import Model


def spread_at(samples: int, replicates: int) -> float:
    """Problem 14.1 — show the square-root law yourself.

    Return the *run-to-run spread* of the 95th percentile of the storage model's five-year total:
    run the model ``replicates`` times at ``samples`` draws, each with a different seed, take the
    p95 of each run, and return the standard deviation of those p95 values.

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
    ``b``. Both are inputs with distributions; ``rho`` is the rank correlation the modeller wants,
    not whatever intermediate quantity the method happens to need.

    The test then checks two things, and the second is the one that matters:

    * the interval on an output fed by both inputs is **wider** than it was;
    * each input's own distribution is **unchanged** — same values, same percentiles, only the
      pairing differs.

    If you find yourself adjusting the values rather than reordering them, stop and re-read the
    section on why the obvious approach is wrong.
    """
    raise NotImplementedError("problem 14.2")


def repair_the_model(model: Model) -> Model:
    """Problem 14.3 — find the missing node.

    ``tests/correlation_and_convergence/fixtures/model.yaml`` is a small monthly cost model for a
    hosted service. It is arithmetically correct, its inputs carry honest distributions, and it
    converges beautifully. It is also wrong, because a cost line is missing from it, and no amount
    of sampling can see that.

    The evidence is in the test: an observed twelve-month total for the service the model
    describes. It falls **outside** the model's 90% interval — comfortably outside, on the high
    side.

    Return a repaired model whose interval contains the observation.

    Two rules, both enforced:

    * you may **not** widen any existing input's distribution. Making a model vaguer until it
      stops disagreeing with reality is the most common wrong answer to this situation, and it
      makes the model less useful every time;
    * the repair must be a **new node** with a unit, a formula or a distribution, and a provenance
      source, like every other node.

    The missing line is a real one and it is findable. Ask what a hosted service pays for that is
    neither a machine, nor a disk, nor a support contract — and which is billed on a quantity
    nothing in this model currently mentions.
    """
    raise NotImplementedError("problem 14.3")
