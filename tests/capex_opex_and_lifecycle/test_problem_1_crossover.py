"""Problem 15.1 - graded against the web service's own split."""

from __future__ import annotations

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.capex_opex_and_lifecycle.stubs import crossover_year


@pytest.fixture(scope="module")
def values():
    return point(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )


@pytest.mark.problem
def test_it_agrees_with_the_reference_split(values):
    mine = crossover_year(values["capex"], values["annual_opex"])
    assert mine == pytest.approx(values["capex"] / values["annual_opex"], rel=1e-9)


@pytest.mark.problem
def test_the_cases_you_can_check_in_your_head():
    assert crossover_year(100.0, 100.0) == pytest.approx(1.0)
    assert crossover_year(300.0, 100.0) == pytest.approx(3.0)
    assert crossover_year(50.0, 100.0) == pytest.approx(0.5)


@pytest.mark.problem
def test_free_to_run_never_crosses():
    try:
        answer = crossover_year(1000.0, 0.0)
    except ZeroDivisionError:
        pytest.fail(
            "crossover_year divided by a running cost of zero. A fleet that costs nothing to run "
            "is never overtaken by its running cost: the docstring says what to return."
        )
    assert answer == float("inf") or answer > 1e9, (
        "a fleet with no running cost is never overtaken by its running cost; the docstring "
        "says what to return"
    )


def test_the_reference_fleet_crosses_inside_its_horizon(values):
    """Scaffolding: the problem is about something.

    If running cost never caught up with capital within the horizon, this chapter's argument would
    be wrong and would need rewriting rather than the test.
    """
    crossover = values["capex"] / values["annual_opex"]
    assert crossover < values["horizon"], (
        f"running cost overtakes capital at year {crossover:.1f} of a {values['horizon']:.0f}-year "
        "horizon; if that ever stops being true, ch15 needs a different argument"
    )
