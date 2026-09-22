"""Problem 1.2 - how far the answer moves when every input moves at once.

The oracle is the model worked through twice, and the reader is handed the means to do it: the
same bands as problem 1.1, and a way of running the model with inputs held where they choose.
What they are not given is the idea. Put every input at the bottom of its band at once, then at
the top, and the answer moves further than any one input can move it. That is the whole reason a
point estimate cannot be defended by pointing at how carefully each input was chosen.
"""

from __future__ import annotations

import math

import pytest

from sizing.evaluate import point
from tests.point_estimates.oracle import TOTAL, each_alone, ends, on_paper, the_model, total_with
from tests.point_estimates.stubs import spread_on_paper


@pytest.fixture(scope="module")
def model():
    return the_model()


@pytest.fixture(scope="module")
def bands(model) -> dict[str, tuple[float, float]]:
    """What the reader is handed: the same six bands problem 1.1 gave them."""
    return ends(model)


@pytest.fixture(scope="module")
def count_at(model):
    """What the reader is handed: the model worked through with some inputs held."""

    def count(held: dict[str, float]) -> float:
        return total_with(model, dict(held))

    return count


@pytest.mark.problem
def test_the_ends_together_are_the_model_worked_through_twice(model, bands, count_at):
    expected = on_paper(model)
    answer = spread_on_paper(bands, count_at)
    assert math.isclose(answer, expected, rel_tol=1e-9), (
        f"you gave {answer:,.2f}. Every input at the bottom of its band, then every input at the "
        f"top, with the recommended host count worked through both times, comes to {expected:,.2f}."
    )


def test_what_the_reader_is_handed_is_the_model_worked_through(model, count_at):
    """Scaffolding: with nothing held, the count the reader can ask for is the chapter's own
    point estimate, so the two calls the problem needs are the model and not a stand-in."""
    assert count_at({}) == point(model)[TOTAL]


def test_the_ends_together_stretch_the_total_further_than_any_one_input(model):
    """Scaffolding: the claim the problem teaches is true of this model. Move one input across
    its band with the rest at their single numbers, and the total moves less than it does with
    every input at an end at once."""
    assert on_paper(model) > 1.5 * max(each_alone(model).values()), (
        "the ends together barely move the total beyond what one input does, so this model "
        "does not demonstrate the thing the chapter says it does"
    )
