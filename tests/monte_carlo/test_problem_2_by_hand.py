"""Problem 13.2 — sample two of the model's inputs without the model's machinery.

The oracle is the model file. Expected percentiles are computed from the distribution the model
declares, at test time, so editing the model changes what this problem wants — which is the
correct behaviour and the reason the stub tells you not to copy the numbers.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc
from sizing.dsl import load_model
from tests.monte_carlo.stubs import sample_two_inputs

SAMPLES = 50_000
WANTED = ("drive_price", "chassis_price")


@pytest.fixture(scope="module")
def declared():
    model = load_model("models/storage_cluster/model.yaml")
    return {name: model.nodes[name].distribution for name in WANTED}


@pytest.mark.problem
def test_both_inputs_are_sampled(declared):
    drawn = sample_two_inputs(seed=11, samples=SAMPLES)
    assert set(drawn) == set(WANTED), f"expected keys {sorted(WANTED)}, got {sorted(drawn)}"
    for name in WANTED:
        assert len(np.asarray(drawn[name])) == SAMPLES, f"{name}: wrong number of draws"


@pytest.mark.problem
@pytest.mark.parametrize("percentile", [10, 50, 90])
def test_the_percentiles_match_what_the_model_declares(declared, percentile):
    drawn = sample_two_inputs(seed=11, samples=SAMPLES)
    for name in WANTED:
        shape, parameters = mc.one_shape(declared[name])
        wanted = float(mc.SHAPES[shape](np.array([percentile / 100]), **parameters)[0])
        got = float(np.percentile(np.asarray(drawn[name], dtype=float), percentile))
        # A tolerance that is itself a sampling question: at this count a percentile estimate
        # wobbles by roughly this much, and a tighter bound would fail on a correct answer.
        assert abs(got - wanted) < 0.04 * wanted, (
            f"{name}: the model declares a p{percentile} of {wanted:.4g} and your samples give "
            f"{got:.4g}. Read the distribution out of the model file rather than copying numbers."
        )


def test_the_model_still_declares_two_sampled_prices(declared):
    """Scaffolding: the problem's subject exists and is uncertain."""
    for name in WANTED:
        assert declared[name] is not None, (
            f"{name} no longer declares a distribution, so problem 13.2 has nothing to sample. "
            "Either the model changed or the problem needs rewriting."
        )
