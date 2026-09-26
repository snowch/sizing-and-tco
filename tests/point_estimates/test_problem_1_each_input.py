"""Problem 1.1 - how wide each input is on its own, graded against the bands the model declares.

The oracle is the model's own file. The reader is handed the two ends of every band that can
move a host count and asked for the top over the bottom, which is a division and nothing else.
That is the point of putting it first: a reader on their first problem should find out that the
file, the Check and the runner all work before being asked to think.

A wrong answer is told which inputs are wrong and, where the whole answer has one recognisable
slip in it, which slip. It is never told the expected ratios: a list of them is the answer.
"""

from __future__ import annotations

import math

import pytest

from tests.point_estimates.oracle import ends, the_model, total_with
from tests.point_estimates.stubs import spread_of_each


@pytest.fixture(scope="module")
def model():
    return the_model()


@pytest.fixture(scope="module")
def bands(model) -> dict[str, tuple[float, float]]:
    """What the reader is handed: every band's two ends, bottom first."""
    return ends(model)


@pytest.mark.problem
def test_every_band_is_its_top_over_its_bottom(model, bands):
    answer = spread_of_each(bands)
    expected = {name: top / bottom for name, (bottom, top) in ends(model).items()}
    missing = sorted(set(expected) - set(answer))
    unexpected = sorted(set(answer) - set(expected))
    assert not missing and not unexpected, (
        f"return one entry per input you are handed. Missing: {missing or 'none'}. "
        f"Not handed to you: {unexpected or 'none'}."
    )
    wrong = sorted(k for k, v in expected.items() if not math.isclose(answer[k], v, rel_tol=1e-9))
    upside_down = all(
        math.isclose(answer[k], bottom / top, rel_tol=1e-9)
        for k, (bottom, top) in bands.items()
        if k in wrong
    )
    as_a_share = all(
        math.isclose(answer[k], (top - bottom) / bottom, rel_tol=1e-9)
        for k, (bottom, top) in bands.items()
        if k in wrong
    )
    if upside_down:
        hint = "Every one of them is the bottom over the top; turn the division over."
    elif as_a_share:
        hint = (
            "Every one of them is how far the top is above the bottom, as a share of the bottom. "
            "The problem asks for the top itself over the bottom."
        )
    else:
        hint = "Each is the second number of its pair divided by the first."
    ok = not wrong
    assert ok, (
        f"{len(wrong)} of {len(expected)} are not top over bottom: {', '.join(wrong)}. {hint}"
    )


def test_the_model_has_several_uncertain_inputs(model):
    """Scaffolding: a band on one input would make the next problem say nothing."""
    assert len(ends(model)) >= 3, "too few inputs with a band for the point to hold"


def test_every_band_handed_over_can_move_the_answer(model):
    """Scaffolding: nothing inert is handed to the reader.

    An input that cannot move the host count is one the reader holds at both ends for no effect,
    and then has to be told to ignore. The chapter should not have to apologise for the problem.
    """
    for name, (bottom, top) in ends(model).items():
        assert total_with(model, {name: bottom}) != total_with(model, {name: top}), (
            f"{name} is handed to the reader and cannot change the answer"
        )


def test_the_file_writes_a_band_both_ways(model):
    """Scaffolding: the stub says a band is its two ends however the file writes it, so the file
    has to write one both ways, or that rule is never exercised."""
    styles = set()
    for node in model.nodes.values():
        for parameters in (getattr(node, "distribution", None) or {}).values():
            styles.add("p10" in parameters)
    assert styles == {True, False}, "every band is written the same way, so the rule is untested"
