"""Problem 21.1 - graded against the stamped results the table is supposed to come from."""

from __future__ import annotations

import pytest

from bench.stamp import load_result

REQUIRED = {"scenario", "hosts", "tco_p50", "tco_p95", "p_over_the_knee"}
#: The chapter's two designs, by scenario: the fleet the model recommends at the point estimate,
#: and the same fleet sized for the growth we might get rather than the growth we expect.
DESIGNS = ("reference", "sized_for_growth")


def stamped(scenario: str) -> dict:
    return load_result(f"web_service-{scenario}")["summary"]


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
    assert row["hosts"] == pytest.approx(payload["nodes"]["hosts"]["point"])
    assert row["tco_p50"] == pytest.approx(payload["nodes"]["tco"]["summary"]["p50"], rel=1e-9)
    assert row["tco_p95"] == pytest.approx(payload["nodes"]["tco"]["summary"]["p95"], rel=1e-9)
    assert row["p_over_the_knee"] == pytest.approx(
        payload["nodes"]["queueing_headroom"]["ceiling"]["p_over_limit"], rel=1e-9
    )


@pytest.mark.problem
def test_more_machines_costs_more_and_risks_less(table):
    """A table where those two did not trade off would not be a decision."""
    ordered = sorted(table, key=lambda row: row["hosts"])
    assert [r["tco_p50"] for r in ordered] == sorted(r["tco_p50"] for r in ordered)
    assert [r["p_over_the_knee"] for r in ordered] == sorted(
        (r["p_over_the_knee"] for r in ordered), reverse=True
    )


def test_the_two_designs_are_meaningfully_different():
    """Scaffolding: there is a decision to present.

    If the two designs ever converged, the chapter would be about a formality rather than a
    choice. Here their shares of futures over the knee differ by more than a fifth.
    """
    risks = [stamped(s)["nodes"]["queueing_headroom"]["ceiling"]["p_over_limit"] for s in DESIGNS]
    assert max(risks) - min(risks) > 0.2, risks
