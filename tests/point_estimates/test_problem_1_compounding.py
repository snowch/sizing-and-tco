"""Problem 1.1 - the width of a product, graded against the bands the model gives its inputs.

The oracle is the model's own bands and its own arithmetic, and the test hands the reader both:
the two ends of every band, and a way of working the model through with inputs held where they
choose. What they are not given is the idea: put every input at the bottom of its band at once,
then at the top, and the answer moves further than any one input can move it. That is the whole
reason a point estimate cannot be defended by pointing at how carefully each input was chosen.
"""

from __future__ import annotations

import math

import pytest

from sizing.dsl import Scenario, load_model
from sizing.evaluate import point
from tests.point_estimates.stubs import spread_of_each, spread_on_paper

MODEL = "models/web_service/model.yaml"
TOTAL = "hosts_recommended"


@pytest.fixture(scope="module")
def model():
    return load_model(MODEL)


def ends(model) -> dict[str, tuple[float, float]]:
    """The bottom and top of each input's band, however the file writes it."""
    out = {}
    for name, node in model.nodes.items():
        for parameters in (getattr(node, "distribution", None) or {}).values():
            if "p10" in parameters:
                out[name] = (parameters["p10"], parameters["p90"])
            else:
                out[name] = (parameters["minimum"], parameters["maximum"])
    return out


def total_with(model, held: dict[str, float]) -> float:
    """The hosts the model recommends with these inputs held at these values."""
    return point(model, Scenario("held", "held", held))[TOTAL]


def on_paper(model) -> float:
    """Every input at the bottom of its band, then every input at the top, and the ratio."""
    bands = ends(model)
    low = total_with(model, {name: bottom for name, (bottom, _top) in bands.items()})
    high = total_with(model, {name: top for name, (_bottom, top) in bands.items()})
    return high / low


@pytest.fixture(scope="module")
def bands(model) -> dict[str, tuple[float, float]]:
    """What the reader is handed: every band's two ends, bottom first."""
    return ends(model)


@pytest.fixture(scope="module")
def count_at(model):
    """What the reader is handed: the model worked through with some inputs held."""

    def count(held: dict[str, float]) -> float:
        return total_with(model, dict(held))

    return count


@pytest.mark.problem
def test_every_band_is_its_top_over_its_bottom(model, bands):
    answer = spread_of_each(bands)
    expected = {name: top / bottom for name, (bottom, top) in ends(model).items()}
    assert set(answer) == set(expected), (
        f"missing {sorted(set(expected) - set(answer))[:5]}, "
        f"unexpected {sorted(set(answer) - set(expected))[:5]}"
    )
    wrong = {
        k: (answer[k], v)
        for k, v in expected.items()
        if not math.isclose(answer[k], v, rel_tol=1e-9)
    }
    assert not wrong, "these do not match the band the file gives: " + str(wrong)


@pytest.mark.problem
def test_the_ends_together_are_the_model_worked_through_twice(model, bands, count_at):
    expected = on_paper(model)
    answer = spread_on_paper(bands, count_at)
    assert math.isclose(answer, expected, rel_tol=1e-9), (
        f"you gave {answer:,.2f}. Every input at the bottom of its band, then every input at the "
        f"top, with the recommended host count worked through both times, comes to {expected:,.2f}."
    )


def test_the_model_has_several_uncertain_inputs(model):
    """Scaffolding: a band on one input would make the problem say nothing."""
    assert len(ends(model)) >= 3, "too few inputs with a band for the point to hold"


def test_the_file_writes_a_band_both_ways(model):
    """Scaffolding: the stub says a band is its two ends however the file writes it, so the file
    has to write one both ways, or that rule is never exercised."""
    styles = set()
    for node in model.nodes.values():
        for parameters in (getattr(node, "distribution", None) or {}).values():
            styles.add("p10" in parameters)
    assert styles == {True, False}, "every band is written the same way, so the rule is untested"


def test_what_the_reader_is_handed_is_the_model_worked_through(model, count_at):
    """Scaffolding: with nothing held, the count the reader can ask for is the chapter's own
    point estimate, so the two calls the problem needs are the model and not a stand-in."""
    assert count_at({}) == point(model)[TOTAL]


def test_the_ends_together_stretch_the_total_further_than_any_one_input(model):
    """Scaffolding: the claim the problem teaches is true of this model. Move one input across
    its band with the rest at their single numbers, and the total moves less than it does with
    every input at an end at once."""
    alone = []
    for name, (bottom, top) in ends(model).items():
        low, high = total_with(model, {name: bottom}), total_with(model, {name: top})
        alone.append(max(low, high) / min(low, high))
    assert on_paper(model) > 1.5 * max(alone), (
        "the ends together barely move the total beyond what one input does, so this model "
        "does not demonstrate the thing the chapter says it does"
    )
