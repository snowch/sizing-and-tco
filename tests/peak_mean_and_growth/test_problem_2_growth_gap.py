"""Problem 3.2 - compounding an average is not averaging the compounds.

The oracle is the sample set itself, computed both ways at test time. Nothing is stored, and the
direction of the inequality is a fact about convexity rather than about these particular numbers.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc
from tests.peak_mean_and_growth.stubs import growth_gap

T0 = 4000.0


def samples(p10: float, p90: float, n: int = 200_000) -> np.ndarray:
    return mc.sample({"lognormal": {"p10": p10, "p90": p90}}, n, mc.rng(404))


CASES = {
    "narrow": samples(1.18, 1.24),
    "the model's own": samples(1.12, 1.55),
    "wide": samples(1.02, 2.2),
}


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
@pytest.mark.parametrize("years", [1.0, 5.0])
def test_both_are_computed_correctly(name, years):
    growth = CASES[name]
    compound_the_average, average_the_compounds = growth_gap(T0, growth, years)
    assert compound_the_average == pytest.approx(T0 * growth.mean() ** years, rel=1e-9)
    assert average_the_compounds == pytest.approx(float((T0 * growth**years).mean()), rel=1e-9)


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
def test_averaging_the_compounds_is_always_the_larger(name):
    compound_the_average, average_the_compounds = growth_gap(T0, CASES[name], 5.0)
    assert average_the_compounds > compound_the_average, (
        "compounding is convex, so the average of the compounded outcomes is above the compound "
        "of the average rate. Always, for any spread at all. If you got the other order, check "
        "which of the two you returned first."
    )


@pytest.mark.problem
def test_the_gap_widens_with_the_spread():
    gaps = []
    for name in ("narrow", "the model's own", "wide"):
        low, high = growth_gap(T0, CASES[name], 5.0)
        gaps.append(high / low - 1.0)
    assert gaps[0] < gaps[1] < gaps[2], (
        f"the gap should widen as the growth rate becomes less certain: {gaps}. It is smallest "
        "when you know the answer and largest when you do not, which is the wrong way round for "
        "anybody's comfort."
    )


@pytest.mark.problem
def test_the_gap_widens_with_the_horizon():
    one = growth_gap(T0, CASES["the model's own"], 1.0)
    five = growth_gap(T0, CASES["the model's own"], 5.0)
    assert (five[1] / five[0]) > (one[1] / one[0])


def test_a_certain_growth_rate_has_no_gap():
    """Scaffolding: the effect is about spread, and vanishes without it."""
    certain = np.full(1000, 1.3)
    assert float((T0 * certain**5).mean()) == pytest.approx(T0 * certain.mean() ** 5, rel=1e-9)
