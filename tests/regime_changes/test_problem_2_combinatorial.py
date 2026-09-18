"""Problem 8.2 - uncertainty compounds when quantities multiply.

Graded against the samples themselves, computed both ways at test time.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc
from tests.regime_changes.stubs import combinatorial_spread


def spread_of(values: np.ndarray) -> float:
    low, high = np.percentile(values, [5, 95])
    return float(high / low)


CASES = {
    "three narrow counts": [
        mc.sample(
            {"triangular": {"minimum": 4.0, "likely": 6.0, "maximum": 9.0}}, 100_000, mc.rng(i)
        )
        for i in range(3)
    ],
    "the model's own labels": [
        mc.sample(
            {"triangular": {"minimum": 2.0, "likely": 6.0, "maximum": 20.0}}, 100_000, mc.rng(11)
        ),
        mc.sample(
            {"triangular": {"minimum": 2.0, "likely": 3.0, "maximum": 6.0}}, 100_000, mc.rng(12)
        ),
        mc.sample({"lognormal": {"p10": 1.0, "p90": 6.0}}, 100_000, mc.rng(13)),
    ],
    "two only": [
        mc.sample({"lognormal": {"p10": 2.0, "p90": 8.0}}, 100_000, mc.rng(21)),
        mc.sample({"lognormal": {"p10": 2.0, "p90": 8.0}}, 100_000, mc.rng(22)),
    ],
}


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
def test_both_numbers_are_computed_correctly(name):
    factors = CASES[name]
    widest, product = combinatorial_spread(factors)
    assert widest == pytest.approx(max(spread_of(f) for f in factors), rel=1e-9)
    assert product == pytest.approx(spread_of(np.prod(factors, axis=0)), rel=1e-9)


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
def test_the_product_is_always_wider(name):
    widest, product = combinatorial_spread(CASES[name])
    assert product > widest, (
        f"{name}: the product spans {product:.1f}x and the widest single factor spans "
        f"{widest:.1f}x. Uncertainties do not add when quantities multiply; they compound."
    )


@pytest.mark.problem
def test_more_factors_means_more_spread():
    two = combinatorial_spread(CASES["two only"])[1]
    three = combinatorial_spread(CASES["three narrow counts"])[1]
    narrow = max(spread_of(f) for f in CASES["three narrow counts"])
    assert three > narrow**1.5, (
        "three counts that are each barely uncertain make a product that is substantially so, "
        "which is why a cardinality node dominates a tornado even when nobody thinks any of its "
        "factors is worrying"
    )
    assert two > 1.0


def test_one_factor_is_its_own_product():
    """Scaffolding: the degenerate case behaves, so the effect is about multiplying."""
    single = [CASES["two only"][0]]
    assert spread_of(np.prod(single, axis=0)) == pytest.approx(spread_of(single[0]), rel=1e-9)
