"""Problem 1.1 - how wide each input is on its own, graded against the bands the model declares.

The oracle is the model's own file. The reader is handed the two ends of every band that can
move a host count and asked for the top over the bottom, which is a division and nothing else.
That is the point of putting it first: the chapter's argument needs a ratio per input before it
can say anything about the six together, and a reader on their first problem should find out
that the file, the Check and the runner all work before being asked to think.
"""

from __future__ import annotations

import inspect
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


def test_the_stub_shows_the_names_it_actually_hands_over(model):
    """Scaffolding: the example in the stub is of this model, not of one it used to be.

    The stub shows the reader what `bands` looks like, because a type is not a picture and a
    reader at ch01 has never opened the model file. An example naming inputs the model no longer
    bands would be worse than none.
    """
    shown = [
        line.split("'")[1]
        for line in inspect.getdoc(spread_of_each).splitlines()
        if line.strip().startswith("'") and "': (" in line
    ]
    assert shown, "the stub no longer shows what bands looks like"
    handed = ends(model)
    missing = [name for name in shown if name not in handed]
    assert not missing, f"the stub's example names {missing}, which the reader is not handed"


def test_the_file_writes_a_band_both_ways(model):
    """Scaffolding: the stub says a band is its two ends however the file writes it, so the file
    has to write one both ways, or that rule is never exercised."""
    styles = set()
    for node in model.nodes.values():
        for parameters in (getattr(node, "distribution", None) or {}).values():
            styles.add("p10" in parameters)
    assert styles == {True, False}, "every band is written the same way, so the rule is untested"
