"""Problem 13.3 — where the point estimate sits among the sampled answers.

The oracle is the model's own draws and its own point evaluation, both computed at test time.
The scaffolding holds the chapter to its claims about this model: one cost line or one chain on
its own sits at its middle, a product of two sits near it, and the steps that add several lines
or take the largest of three chains leave the point below the middle.
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
    """The share of draws strictly below the point estimate. Derived, never stored."""
    return float(np.mean(evaluated.samples[name] < evaluated.point[name]))


def at_or_below(evaluated, name: str) -> float:
    """The share at or below it: the likeliest wrong reading of "below", and never printed."""
    return float(np.mean(evaluated.samples[name] <= evaluated.point[name]))


@pytest.mark.problem
def test_every_fraction_is_right(evaluated):
    samples = {name: evaluated.samples[name] for name in OUTPUTS}
    point = {name: evaluated.point[name] for name in OUTPUTS}
    answer = where_the_point_sits(samples, point)
    assert set(answer) == set(OUTPUTS), f"expected {sorted(OUTPUTS)}, got {sorted(answer)}"
    for name in OUTPUTS:
        if answer[name] == pytest.approx(below(evaluated, name), abs=1e-12):
            continue
        if answer[name] == pytest.approx(at_or_below(evaluated, name), abs=1e-12):
            pytest.fail(
                f"{name}: you counted the draws equal to the point estimate as below it. The host "
                "count is a whole number, so many draws land on the point exactly. Count only the "
                "draws strictly less than the point."
            )
        pytest.fail(
            f"{name}: this is not the fraction of its draws below its point estimate. Count the "
            "draws strictly less than the point and divide by the number of draws, for each "
            "output separately."
        )


@pytest.mark.problem
def test_you_named_what_moved_it():
    doc = where_the_point_sits.__doc__ or ""
    marker = "What moved it:"
    said = doc.split(marker, 1)[1].strip() if marker in doc else ""
    assert len(said.split()) >= 4, (
        "finish the last line of the stub's docstring with a sentence for each output whose "
        "point sits away from the middle, naming the step in its chain that moved it, and which way"
    )


def test_the_point_sits_off_centre_for_some_outputs_and_not_for_others(evaluated):
    """Scaffolding: the page says some of the four sit near a half and some do not, and that the
    ones that do not sit low. The contrast has to be there to see."""
    assert 0.46 < below(evaluated, "capex") < 0.54, below(evaluated, "capex")
    for name in ("hosts_recommended", "tco", "annual_opex"):
        assert below(evaluated, name) < 0.45, (name, below(evaluated, name))


def test_each_line_and_each_chain_alone_sits_at_its_middle(evaluated):
    """Scaffolding: the page says a cost line or a chain on its own sits at its own middle, and a
    product of two inputs near it. So what moves the total is the adding and the largest-of, not
    anything inside the parts."""
    model = evaluated.model
    parts = model.nodes["annual_opex"].depends_on() | model.nodes["hosts_recommended"].depends_on()
    assert len(parts) == 7, sorted(parts)
    for name in sorted(parts):
        assert 0.47 < below(evaluated, name) < 0.53, (name, below(evaluated, name))
    assert model.nodes["annual_staff_cost"].depends_on() == {"staff_fte", "fully_loaded_salary"}
    assert 0.47 < below(evaluated, "annual_staff_cost") < 0.53
