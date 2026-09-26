"""Problem 4.2 - compounding an average is not averaging the compounds.

The oracle is the sample set itself, computed both ways at test time. Nothing is stored, and the
direction of the inequality is a fact about how compounding curves upwards, not about these
particular numbers.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc
from sizing.dsl import load_model
from tests.peak_mean_and_growth.stubs import growth_gap

T0 = 4000.0


def samples(p10: float, p90: float, n: int = 200_000) -> np.ndarray:
    return mc.sample({"lognormal": {"p10": p10, "p90": p90}}, n, mc.rng(404))


#: The web service's growth band, read from the model rather than retyped here.
GROWTH = (
    load_model("models/web_service/model.yaml").nodes["annual_growth"].distribution["lognormal"]
)

CASES = {
    "narrow": samples(1.18, 1.24),
    "the model's own": samples(GROWTH["p10"], GROWTH["p90"]),
    "wide": samples(1.02, 2.2),
}


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
@pytest.mark.parametrize("years", [1.0, 5.0])
def test_both_are_computed_correctly(name, years):
    growth = CASES[name]
    compound_the_average, average_the_compounds = growth_gap(T0, growth, years)
    assert compound_the_average == pytest.approx(T0 * growth.mean() ** years, rel=1e-9), (
        f"{name}, {years:g} year(s): the first value is off. Take the ordinary average of the "
        "factors (add them up and divide by how many), then compound that from t0. A doubling "
        "and a halving do not average to no growth."
    )
    assert average_the_compounds == pytest.approx(float((T0 * growth**years).mean()), rel=1e-9), (
        f"{name}, {years:g} year(s): the second value is off. Compound every factor from t0 "
        "first, then take the ordinary average of the results."
    )


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(CASES))
def test_averaging_the_compounds_is_always_the_larger(name):
    compound_the_average, average_the_compounds = growth_gap(T0, CASES[name], 5.0)
    assert average_the_compounds > compound_the_average, (
        "compounding curves upwards, so the average of the compounded outcomes is above the "
        "compound of the average rate, for any spread, over any horizon longer than a year. If "
        "you got the other order, check which of the two you returned first."
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


def test_one_year_has_no_gap():
    """Scaffolding: compounding once is one multiplication, so the two ways agree at one year."""
    for name, growth in CASES.items():
        once = float((T0 * growth**1.0).mean())
        assert once == pytest.approx(T0 * growth.mean() ** 1.0, rel=1e-9), name
