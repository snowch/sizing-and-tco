"""Problem 14.1 - graded against the storage model's own split."""

from __future__ import annotations

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.capex_opex_and_lifecycle.stubs import crossover_year


@pytest.fixture(scope="module")
def values():
    return point(
        load_model("models/storage_cluster/model.yaml"),
        load_scenario("models/storage_cluster/scenarios/reference.yaml"),
    )


@pytest.mark.problem
def test_it_is_the_ratio(values):
    mine = crossover_year(values["capex"], values["annual_opex"])
    assert mine == pytest.approx(values["capex"] / values["annual_opex"], rel=1e-9)


@pytest.mark.problem
def test_the_cases_you_can_check_in_your_head():
    assert crossover_year(100.0, 100.0) == pytest.approx(1.0)
    assert crossover_year(300.0, 100.0) == pytest.approx(3.0)
    assert crossover_year(50.0, 100.0) == pytest.approx(0.5)


@pytest.mark.problem
def test_free_to_run_never_crosses():
    answer = crossover_year(1000.0, 0.0)
    assert answer == float("inf") or answer > 1e9, (
        "something with no running cost never gets overtaken by its running cost"
    )


def test_the_reference_cluster_crosses_inside_its_horizon(values):
    """Scaffolding: the problem is about something.

    If running cost never caught up with capital within the horizon, this chapter's argument would
    be wrong and would need rewriting rather than the test.
    """
    crossover = values["capex"] / values["annual_opex"]
    assert crossover < values["horizon"], (
        f"running cost overtakes capital at year {crossover:.1f} of a {values['horizon']:.0f}-year "
        "horizon; if that ever stops being true, ch14 needs a different argument"
    )
