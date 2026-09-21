"""Problem 13.3 — where the point estimate sits among the sampled answers.

The oracle is the model's own draws and its own point evaluation, both computed at test time.
The scaffolding holds the chapter to its claim: for at least one output of the web service model
the point estimate sits well away from the middle, and for at least one it does not.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.monte_carlo.stubs import where_the_point_sits

OUTPUTS = ("hosts_recommended", "tco", "capex", "annual_opex")


@pytest.fixture(scope="module")
def evaluated():
    return evaluate(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )


def below(evaluated, name: str) -> float:
    """The share of draws below the point estimate. Derived, never stored."""
    return float(np.mean(evaluated.samples[name] < evaluated.point[name]))


@pytest.mark.problem
def test_every_fraction_is_right(evaluated):
    samples = {name: evaluated.samples[name] for name in OUTPUTS}
    point = {name: evaluated.point[name] for name in OUTPUTS}
    answer = where_the_point_sits(samples, point)
    assert set(answer) == set(OUTPUTS), f"expected {sorted(OUTPUTS)}, got {sorted(answer)}"
    for name in OUTPUTS:
        assert answer[name] == pytest.approx(below(evaluated, name), abs=1e-12), (
            f"{name}: the share of draws below the point estimate is {below(evaluated, name):.3f}"
        )


@pytest.mark.problem
def test_you_named_what_moved_it():
    doc = where_the_point_sits.__doc__ or ""
    marker = "What moved it:"
    said = doc.split(marker, 1)[1].strip() if marker in doc else ""
    assert len(said.split()) >= 4, (
        "finish the last line of the stub's docstring with one sentence naming the step in the "
        "chain that moves the point estimate furthest from the middle, and which way"
    )


def test_the_point_sits_off_centre_for_the_host_count_and_not_for_a_cost(evaluated):
    """Scaffolding: the chapter's claim holds of this model, and there is a contrast to see."""
    hosts = below(evaluated, "hosts_recommended")
    assert not 0.44 < hosts < 0.56, f"the host count's point sits at {hosts:.2f}, near the middle"
    costs = [below(evaluated, name) for name in ("tco", "capex", "annual_opex")]
    assert any(0.40 < share < 0.60 for share in costs), costs
