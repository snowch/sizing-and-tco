"""Problem 1.1 - the width of a product, graded against the distributions the model declares.

The oracle is the model's own ``p10`` and ``p90``, which the reader is reading too. What they are
not given is the arithmetic: the answer is not the widest input, and it is not the average of the
widths. It is the product, and that is the whole reason a point estimate cannot be defended by
pointing at how carefully each input was chosen.
"""

from __future__ import annotations

import math

import pytest

from sizing.dsl import load_model
from tests.what_one_number_hides.stubs import spread_of_each, spread_of_the_chain

MODEL = "models/web_service/model.yaml"


@pytest.fixture(scope="module")
def model():
    return load_model(MODEL)


def declared(model) -> dict[str, float]:
    """Each lognormal input's p90 over its p10, from the file and nothing else."""
    out = {}
    for name, node in model.nodes.items():
        shape = getattr(node, "distribution", None) or {}
        parameters = shape.get("lognormal")
        if parameters:
            out[name] = parameters["p90"] / parameters["p10"]
    return out


@pytest.mark.problem
def test_every_lognormal_input_is_measured(model):
    answer = spread_of_each(model)
    expected = declared(model)
    assert set(answer) == set(expected), (
        f"missing {sorted(set(expected) - set(answer))[:5]}, "
        f"unexpected {sorted(set(answer) - set(expected))[:5]}"
    )
    wrong = {
        k: (answer[k], v)
        for k, v in expected.items()
        if not math.isclose(answer[k], v, rel_tol=1e-9)
    }
    assert not wrong, "these do not match the distribution the model declares: " + str(wrong)


@pytest.mark.problem
def test_the_chain_is_the_product_and_not_the_worst_of_them(model):
    expected = declared(model)
    answer = spread_of_the_chain(model)
    product = math.prod(expected.values())
    assert math.isclose(answer, product, rel_tol=1e-9), (
        f"you gave {answer:,.1f}. Multiplying uncertain quantities multiplies their widths: "
        f"{len(expected)} inputs whose widest is {max(expected.values()):.2f} compound to "
        f"{product:,.1f}."
    )


def test_the_model_has_several_uncertain_inputs(model):
    """Scaffolding: a product of one number would make the problem say nothing."""
    assert len(declared(model)) >= 3, "too few declared distributions for the point to hold"


def test_the_chain_is_wider_than_any_single_input(model):
    """Scaffolding: the claim the problem is teaching is true of this model."""
    widths = declared(model)
    assert math.prod(widths.values()) > max(widths.values()) * 2, (
        "the compounded width is barely wider than the widest input, so this model does not "
        "demonstrate the thing the chapter says it does"
    )
