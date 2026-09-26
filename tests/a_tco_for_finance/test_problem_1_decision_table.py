"""Problem 21.1 - graded against the stamped results the table is built from.

The test hands the reader each design's stamped summary and grades the rows against the same
summaries, so a figure that did not come out of the build has nowhere to come from. Where a
figure is wrong, the message names the likeliest mix-up and never the figure itself.
"""

from __future__ import annotations

import math

import pytest

from bench.stamp import load_result

REQUIRED = {"scenario", "hosts", "tco_p50", "tco_p95", "p_over_the_knee"}
#: The chapter's two designs, by scenario: the fleet the model recommends at the point estimate,
#: and the fleet it recommends when growth comes in at its p90.
DESIGNS = ("reference", "sized_for_growth")


def stamped(scenario: str) -> dict:
    return load_result(f"web_service-{scenario}")["summary"]


def expected(nodes: dict) -> dict[str, float]:
    """Where each column lives in a stamped summary: the paths the stub's docstring gives."""
    return {
        "hosts": nodes["hosts"]["point"],
        "tco_p50": nodes["tco"]["summary"]["p50"],
        "tco_p95": nodes["tco"]["summary"]["p95"],
        "p_over_the_knee": nodes["queueing_headroom"]["ceiling"]["p_over_limit"],
    }


def close(got: object, want: float) -> bool:
    return isinstance(got, int | float) and math.isclose(got, want, rel_tol=1e-9)


#: How far a figure may sit from another before it is not "the same figure, rounded for a
#: page": a dollar on a total, half a host, half a percentage point on a share.
NEAR = {"hosts": 0.5, "tco_p50": 1.0, "tco_p95": 1.0, "p_over_the_knee": 0.005}


def mix_up(key: str, got: object, nodes: dict) -> str:
    """What a wrong figure most likely is, said without saying what the right one is."""
    if not isinstance(got, int | float):
        return f"{key} is not a number."
    want = expected(nodes)[key]
    ceiling = nodes["queueing_headroom"]["ceiling"]

    def near(value: float) -> bool:
        return abs(got - value) <= NEAR[key]

    if key == "hosts" and near(nodes["hosts_recommended"]["point"]):
        return (
            "hosts is what the model recommends. The column is what the design bought: "
            "nodes['hosts']."
        )
    if key.startswith("tco") and near(nodes["tco"]["point"]):
        return (
            f"{key} is the point estimate, the total with every input at its central value. "
            "The column wants a figure from the node's summary, which describes the sampled "
            "futures."
        )
    if key == "tco_p50" and near(nodes["tco"]["summary"]["mean"]):
        return "tco_p50 is the mean. The median is a different figure in the same summary."
    if key == "p_over_the_knee" and abs(got / 100 - want) <= NEAR[key]:
        return "p_over_the_knee is a percentage. The column is a share, between 0 and 1."
    if key == "p_over_the_knee" and near(ceiling.get("p_over_allowed", math.nan)):
        return (
            "p_over_the_knee is how often the margin is used up (p_over_allowed). The column is "
            "how often the limit itself is crossed."
        )
    if near(want):
        return (
            f"{key} has been rounded. Take it from the stamped summary, not from a table on the "
            "page: those are rounded for reading."
        )
    return f"{key} does not match its place in the stamped summary. The docstring gives the path."


@pytest.fixture(scope="module")
def table():
    from tests.a_tco_for_finance.stubs import decision_table

    return decision_table({scenario: stamped(scenario) for scenario in DESIGNS})


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
    nodes = stamped(scenario)["nodes"]
    wrong = [
        mix_up(key, row.get(key), nodes)
        for key, want in expected(nodes).items()
        if not close(row.get(key), want)
    ]
    assert not wrong, f"{scenario}: " + " ".join(wrong)


@pytest.mark.problem
def test_more_machines_costs_more_and_risks_less(table):
    """A table where those two did not trade off would not be a decision."""
    ordered = sorted(table, key=lambda row: row["hosts"])
    assert [r["tco_p50"] for r in ordered] == sorted(r["tco_p50"] for r in ordered), (
        "the design with more hosts should cost more. If it does not, a total is in the wrong row."
    )
    assert [r["p_over_the_knee"] for r in ordered] == sorted(
        (r["p_over_the_knee"] for r in ordered), reverse=True
    ), "the design with more hosts should cross the limit less often. Check which row is which."


def test_the_two_designs_are_meaningfully_different():
    """Scaffolding: there is a decision to present.

    If the two designs ever converged, the chapter would be about a formality rather than a
    choice. Here their shares of futures over the knee differ by more than a fifth.
    """
    risks = [stamped(s)["nodes"]["queueing_headroom"]["ceiling"]["p_over_limit"] for s in DESIGNS]
    assert max(risks) - min(risks) > 0.2, risks


def test_every_summary_holds_the_figures_the_table_needs():
    """Scaffolding: the places the problem says to look exist in both stamped results."""
    for scenario in DESIGNS:
        nodes = stamped(scenario)["nodes"]
        assert nodes["hosts"]["point"] > 0
        assert nodes["tco"]["summary"]["p50"] < nodes["tco"]["summary"]["p95"]
        assert 0 <= nodes["queueing_headroom"]["ceiling"]["p_over_limit"] <= 1


def test_each_mix_up_the_messages_name_is_a_different_figure():
    """Scaffolding: every hint in ``mix_up`` can tell its mistake from the right answer.

    If the point estimate ever equalled the median, or the recommendation the fleet bought, a
    reader who made that mistake would pass and the hint could never fire. The bigger design is
    the one where the recommendation and the purchase differ, so that is where the hint is live.
    """
    for scenario in DESIGNS:
        nodes = stamped(scenario)["nodes"]
        want = expected(nodes)
        for key in ("tco_p50", "tco_p95"):
            assert abs(nodes["tco"]["point"] - want[key]) > NEAR[key], (scenario, key)
        assert abs(nodes["tco"]["summary"]["mean"] - want["tco_p50"]) > NEAR["tco_p50"], scenario
        allowed = nodes["queueing_headroom"]["ceiling"]["p_over_allowed"]
        assert abs(allowed - want["p_over_the_knee"]) > NEAR["p_over_the_knee"], scenario
    growth = stamped("sized_for_growth")["nodes"]
    recommended = growth["hosts_recommended"]["point"]
    assert abs(recommended - expected(growth)["hosts"]) > NEAR["hosts"]
