"""Problem 14.1 — show the square-root law.

The target is the law itself, not a stored number: the test asks whether the reader's measured
spread falls by a factor of root ten per decade, with a tolerance derived from how many
replicates they were told to run.
"""

from __future__ import annotations

import math

import pytest

from tests.correlation_and_convergence.stubs import spread_at

COUNTS = (1_000, 10_000, 100_000)
REPLICATES = 12

#: The standard deviation of a sample standard deviation is itself about 1/sqrt(2(k-1)) of it, so
#: with twelve replicates each measured spread carries roughly this much relative noise. The
#: tolerance is derived from that rather than guessed, and a reader who wants a tighter one has to
#: run more replicates — which is the chapter's own argument, applied to the chapter's own
#: experiment.
RELATIVE_NOISE = 1.0 / math.sqrt(2 * (REPLICATES - 1))
TOLERANCE = 3.0 * RELATIVE_NOISE * math.sqrt(10.0)


@pytest.mark.problem
def test_the_spread_falls_as_one_over_root_n():
    spreads = [spread_at(samples=count, replicates=REPLICATES) for count in COUNTS]
    assert all(s > 0 for s in spreads), (
        "a spread of zero means every replicate gave the same answer, which means the seeds were "
        "not different. Re-read what `replicates` is for."
    )
    for i in range(len(COUNTS) - 1):
        ratio = spreads[i] / spreads[i + 1]
        assert abs(ratio - math.sqrt(10.0)) < TOLERANCE, (
            f"going from {COUNTS[i]:,} to {COUNTS[i + 1]:,} samples changed the run-to-run spread "
            f"by {ratio:.2f}x; the law says about {math.sqrt(10.0):.2f}x. If your ratio is near "
            "1.0 you are probably measuring the interval width, which does not shrink — that is "
            "the whole point of the section."
        )


def test_the_tolerance_is_derived_and_not_absurd():
    """Scaffolding: the problem is passable and is not trivially passable."""
    assert 0.1 < TOLERANCE < math.sqrt(10.0), (
        f"a tolerance of {TOLERANCE:.3f} either cannot be met or cannot be failed"
    )
