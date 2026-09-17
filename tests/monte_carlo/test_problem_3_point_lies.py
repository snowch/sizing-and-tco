"""Problem 12.3 — make the point estimate unrepresentative.

No stored answer: the test takes whatever distributions the reader proposes, checks they are
legal under the model's own declared ranges, then runs the model and asks whether the point
estimate has fallen outside the middle half of the sampled answers.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from sizing import mc
from sizing.dsl import Input, load_model, load_scenario
from sizing.evaluate import evaluate, point
from tests.monte_carlo.stubs import make_the_point_estimate_lie

OUTPUT = "tco"


@pytest.fixture(scope="module")
def model():
    return load_model("models/storage_cluster/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/storage_cluster/scenarios/reference.yaml")


def _rebuilt(model, proposal):
    nodes = dict(model.nodes)
    for name, distribution in proposal.items():
        nodes[name] = replace(nodes[name], distribution=distribution, value=None)
    return replace(model, nodes=nodes)


@pytest.mark.problem
def test_the_proposal_is_legal(model):
    proposal = make_the_point_estimate_lie()
    assert proposal, "return at least one replacement distribution"
    for name, distribution in proposal.items():
        node = model.nodes.get(name)
        assert isinstance(node, Input), f"{name!r} is not an input of this model"
        assert node.distribution is not None, f"{name!r} was not uncertain to begin with"
        was, _ = mc.one_shape(node.distribution)
        now, parameters = mc.one_shape(distribution)
        assert now == was, (
            f"{name}: keep the same kind of distribution ({was}). Changing the shape as well "
            "makes this a different problem."
        )
        if node.slider:
            low, high = mc.SHAPES[now](np.array([0.1, 0.9]), **parameters)
            assert node.slider[0] <= low and high <= node.slider[1], (
                f"{name}: p10 {low:.4g} and p90 {high:.4g} must stay inside the declared range "
                f"{node.slider}. You are choosing defensible beliefs, not breaking the model."
            )


@pytest.mark.problem
def test_the_point_estimate_falls_outside_the_middle_half(model, scenario):
    altered = _rebuilt(model, make_the_point_estimate_lie())
    at_point = point(altered, scenario)[OUTPUT]
    drawn = evaluate(altered, scenario).samples[OUTPUT]
    p25, p75 = np.percentile(drawn, [25, 75])
    assert not (p25 <= at_point <= p75), (
        f"the point estimate {at_point:,.0f} is still inside the middle half "
        f"({p25:,.0f} to {p75:,.0f}). Look for the place where the model is least linear — a "
        "product of skewed inputs, or a ceil, or a max of two chains — and widen what feeds it."
    )


def test_the_reference_model_does_not_already_do_this(model, scenario):
    """Scaffolding: the problem is not already solved by the model as shipped.

    Unmarked, so CI checks there is something to find. If a change to the model made this pass
    on its own, the problem has stopped being a problem and needs rewriting rather than ignoring.
    """
    at_point = point(model, scenario)[OUTPUT]
    p25, p75 = np.percentile(evaluate(model, scenario).samples[OUTPUT], [25, 75])
    assert p25 <= at_point <= p75, (
        "the reference model's point estimate is already outside its own middle half, so problem "
        "13.3 is solved before the reader starts. Rewrite the problem."
    )
