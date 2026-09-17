"""Problem 20.1 - graded against the stamped results the table is supposed to come from."""

from __future__ import annotations

import pytest

from bench.stamp import load_result

REQUIRED = {"scenario", "nodes", "tco_p50", "tco_p95", "p_out_of_space"}
#: The storage-model scenarios that represent something somebody could buy.
DESIGNS = ("reference", "sized_for_growth", "power_first")


def stamped(scenario: str) -> dict:
    return load_result(f"storage_cluster-{scenario}")["summary"]


@pytest.fixture(scope="module")
def table():
    from tests.a_tco_for_finance.stubs import decision_table

    return decision_table()


@pytest.mark.problem
def test_it_has_a_row_per_design(table):
    assert {row["scenario"] for row in table} == set(DESIGNS), (
        f"expected {sorted(DESIGNS)}, got {sorted(row['scenario'] for row in table)}"
    )


@pytest.mark.problem
def test_the_columns_are_exactly_what_the_decision_needs(table):
    for row in table:
        assert set(row) == REQUIRED, (
            f"{row.get('scenario')}: {sorted(set(row) ^ REQUIRED)} is the difference. Every column "
            "answers the question or it should not be there."
        )


@pytest.mark.problem
@pytest.mark.parametrize("scenario", DESIGNS)
def test_every_figure_came_from_the_build(table, scenario):
    row = next(r for r in table if r["scenario"] == scenario)
    payload = stamped(scenario)
    assert row["nodes"] == pytest.approx(payload["nodes"]["nodes_purchased"]["point"])
    assert row["tco_p50"] == pytest.approx(payload["nodes"]["tco"]["summary"]["p50"], rel=1e-9)
    assert row["tco_p95"] == pytest.approx(payload["nodes"]["tco"]["summary"]["p95"], rel=1e-9)
    assert row["p_out_of_space"] == pytest.approx(
        payload["nodes"]["fill_level"]["ceiling"]["p_over_limit"], rel=1e-9
    )


@pytest.mark.problem
def test_more_machines_costs_more_and_risks_less(table):
    """A table where those two did not trade off would not be a decision."""
    ordered = sorted(table, key=lambda row: row["nodes"])
    assert [r["tco_p50"] for r in ordered] == sorted(r["tco_p50"] for r in ordered)
    assert [r["p_out_of_space"] for r in ordered] == sorted(
        (r["p_out_of_space"] for r in ordered), reverse=True
    )


def test_the_three_designs_are_meaningfully_different():
    """Scaffolding: there is a decision to present.

    If the options ever converged, the chapter would be about a formality rather than a choice.
    """
    risks = [stamped(s)["nodes"]["fill_level"]["ceiling"]["p_over_limit"] for s in DESIGNS]
    assert max(risks) - min(risks) > 0.2, risks
