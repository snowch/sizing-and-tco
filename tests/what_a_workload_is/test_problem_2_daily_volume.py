"""Problem 1.2 - a rate times an amount of time, and not a rate times a number."""

from __future__ import annotations

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import check_units, point
from tests.what_a_workload_is.stubs import daily_volume

SECONDS_PER_DAY = 86_400
BYTES_PER_TB = 1e12


@pytest.fixture(scope="module")
def base():
    return load_model("models/observability/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/observability/scenarios/reference.yaml")


@pytest.mark.problem
def test_the_node_exists_and_is_a_volume(base):
    extended = daily_volume(base)
    node = extended.nodes.get("daily_ingest")
    assert node is not None, "no node called daily_ingest"
    assert node.unit == "TB", f"declared {node.unit!r}; a volume is not a rate"


@pytest.mark.problem
def test_it_typechecks(base):
    problems, _ = check_units(daily_volume(base))
    assert not problems, (
        "\n".join(problems)
        + "\n\nA rate multiplied by a pure number is still a rate. Something in the formula has "
        "to carry a duration."
    )


@pytest.mark.problem
def test_it_is_the_ingest_rate_times_a_day(base, scenario):
    extended = daily_volume(base)
    values = point(extended, scenario)
    # Derived from the model at test time: whatever the ingest rate currently is, a day of it is
    # this. Nothing here is stored, so changing the model changes what the problem wants.
    rate_mb_per_s = values["metrics_ingest"] + values["logs_ingest"]
    expected = rate_mb_per_s * 1e6 * SECONDS_PER_DAY / BYTES_PER_TB
    assert values["daily_ingest"] == pytest.approx(expected, rel=1e-6), (
        f"daily_ingest is {values['daily_ingest']:,.3f} TB and a day of "
        f"{rate_mb_per_s:,.2f} MB/s is {expected:,.3f} TB"
    )


def test_the_two_computable_chains_are_still_there(base):
    """Scaffolding: the problem's subject exists and is not blocked."""
    blocked = base.blocked()
    for name in ("metrics_ingest", "logs_ingest"):
        assert name in base.nodes and name not in blocked, (
            f"{name} is missing or blocked; problem 1.2 needs rewriting"
        )
