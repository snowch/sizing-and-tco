"""Problem 22.2 - graded by putting the answer back into the model and reading the difference."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point

MODEL = "models/web_service/model.yaml"
INCUMBENT = "models/web_service/scenarios/incumbent.yaml"
CHALLENGER = "models/web_service/scenarios/challenger.yaml"


def difference_at(migration: float) -> float:
    """Challenger minus incumbent at the point estimate, with the move costing ``migration``."""
    model = load_model(MODEL)
    incumbent = point(model, load_scenario(INCUMBENT))["tco"]
    challenger = load_scenario(CHALLENGER)
    moved = replace(challenger, overrides={**challenger.overrides, "migration_cost": migration})
    return point(model, moved)["tco"] - incumbent


@pytest.fixture(scope="module")
def answer():
    from tests.comparing_two_tcos.stubs import break_even_migration

    return break_even_migration()


@pytest.mark.problem
def test_it_is_a_positive_amount_of_money(answer):
    assert isinstance(answer, int | float) and answer > 0


@pytest.mark.problem
def test_the_totals_tie_there(answer):
    gap = difference_at(answer)
    assert abs(gap) < 1.0, (
        f"with the move costing {answer:,.0f} the challenger is still {gap:+,.0f} away from the "
        "incumbent at the point estimate. Two evaluations fix the line; solve it for zero."
    )


# -- scaffolding ------------------------------------------------------------------------------------


def test_a_break_even_exists():
    """The challenger is cheaper with the move free and dearer with it very expensive."""
    assert difference_at(0.0) < 0
    assert difference_at(5_000_000.0) > 0


def test_the_difference_is_linear_in_the_move():
    """So the problem's hint is true, and a reader who solves the line gets the right answer."""
    d0, d1, d2 = (difference_at(m) for m in (0.0, 100_000.0, 200_000.0))
    assert d1 - d0 == pytest.approx(d2 - d1, rel=1e-9)
    assert d1 - d0 == pytest.approx(100_000.0, rel=1e-9)
