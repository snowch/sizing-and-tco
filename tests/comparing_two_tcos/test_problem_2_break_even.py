"""Problem 22.2 - graded by putting the answer back into the model and reading the difference.

The chapter's break-even table prints the tie for the fleet the incumbent runs, so the answer is
graded at that fleet and at two the page does not print. A tie that moves with the fleet was
computed; one that does not was copied.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point

MODEL = "models/web_service/model.yaml"
INCUMBENT = "models/web_service/scenarios/incumbent.yaml"
CHALLENGER = "models/web_service/scenarios/challenger.yaml"

#: The fleet the incumbent's scenario runs, which is the one the chapter prints a tie for.
OWN_FLEET = int(load_scenario(INCUMBENT).overrides["hosts"])
#: Where the answer is graded: the incumbent's own fleet, and a few hosts fewer and a few more.
FLEETS = (OWN_FLEET, OWN_FLEET - 4, OWN_FLEET + 4)
#: How far from a tie the graded answer may land, in dollars.
TOLERANCE = 1.0


def difference_at(incumbent_hosts: int, migration: float) -> float:
    """Challenger minus incumbent at the point estimate.

    The incumbent runs ``incumbent_hosts`` hosts and the move costs ``migration``. Everything
    else is as the two scenarios hold it.
    """
    model = load_model(MODEL)
    incumbent = load_scenario(INCUMBENT)
    fleet = replace(incumbent, overrides={**incumbent.overrides, "hosts": float(incumbent_hosts)})
    challenger = load_scenario(CHALLENGER)
    moved = replace(challenger, overrides={**challenger.overrides, "migration_cost": migration})
    return point(model, moved)["tco"] - point(model, fleet)["tco"]


@pytest.fixture(scope="module", params=FLEETS)
def fleet(request) -> int:
    return request.param


@pytest.fixture(scope="module")
def answer(fleet):
    from tests.comparing_two_tcos.stubs import break_even_migration

    return break_even_migration(fleet)


@pytest.mark.problem
def test_it_is_a_positive_amount_of_money(answer):
    assert isinstance(answer, int | float) and answer > 0


@pytest.mark.problem
def test_the_totals_tie_there(answer, fleet):
    gap = difference_at(fleet, answer)
    assert abs(gap) < TOLERANCE, (
        f"with the incumbent on {fleet} hosts and the move costing {answer:,.0f}, the challenger "
        f"is still {gap:+,.0f} away from the incumbent at the point estimate. Two evaluations fix "
        "the line; solve it for zero."
    )


# -- scaffolding -----------------------------------------------------------------------------------


@pytest.mark.parametrize("hosts", FLEETS)
def test_a_break_even_exists(hosts):
    """At every graded fleet the challenger is cheaper with the move free and dearer with it very
    expensive, so there is a tie to find."""
    assert difference_at(hosts, 0.0) < 0
    assert difference_at(hosts, 5_000_000.0) > 0


@pytest.mark.parametrize("hosts", FLEETS)
def test_the_difference_is_linear_in_the_move(hosts):
    """So the problem's hint is true, and a reader who solves the line gets the right answer."""
    d0, d1, d2 = (difference_at(hosts, m) for m in (0.0, 100_000.0, 200_000.0))
    assert d1 - d0 == pytest.approx(d2 - d1, rel=1e-9)
    assert d1 - d0 == pytest.approx(100_000.0, rel=1e-9)


def test_the_fleet_moves_the_tie():
    """No one cost of moving ties the totals at two of the graded fleets, so the tie the page
    prints passes at the incumbent's own fleet and fails at the other two."""
    free = [difference_at(hosts, 0.0) for hosts in FLEETS]
    for i, a in enumerate(free):
        for b in free[i + 1 :]:
            assert abs(a - b) > 2 * TOLERANCE, (FLEETS, free)
