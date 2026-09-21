"""Problem 2.2 - a rate times an amount of time, and not a rate times a number.

Graded by writing the text the reader returns to a file and loading it as the build would, the
same way problems 2.3 and 2.4 are graded. The model's own numbers are the oracle.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import check_units, point
from tests.what_a_workload_is.stubs import daily_volume

MODEL = "models/observability/model.yaml"
SECONDS_PER_DAY = 86_400
BYTES_PER_TB = 1e12


@pytest.fixture(scope="module")
def base():
    return load_model(MODEL)


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/observability/scenarios/reference.yaml")


@pytest.fixture
def extended(tmp_path):
    """The reader's text, written to a file and loaded exactly as the build would load it."""
    path = tmp_path / "model.yaml"
    path.write_text(daily_volume(Path(MODEL).read_text()))
    return load_model(path)


@pytest.mark.problem
def test_the_node_exists_and_is_a_volume(extended):
    node = extended.nodes.get("daily_ingest")
    assert node is not None, "no node called daily_ingest"
    assert node.unit == "TB", f"declared {node.unit!r}; a volume is not a rate"


@pytest.mark.problem
def test_it_typechecks(extended):
    problems, _ = check_units(extended)
    assert not problems, (
        "\n".join(problems)
        + "\n\nA rate multiplied by a pure number is still a rate. Something in the formula has "
        "to carry a duration."
    )


@pytest.mark.problem
def test_it_is_the_ingest_rate_times_a_day(extended, scenario):
    values = point(extended, scenario)
    # Derived from the model at test time: whatever the ingest rate currently is, a day of it is
    # this. Nothing here is stored, so changing the model changes what the problem wants.
    rate_mb_per_s = values["metrics_ingest"] + values["logs_ingest"]
    expected = rate_mb_per_s * 1e6 * SECONDS_PER_DAY / BYTES_PER_TB
    assert values["daily_ingest"] == pytest.approx(expected, rel=1e-6), (
        f"daily_ingest is {values['daily_ingest']:,.3f} TB and a day of "
        f"{rate_mb_per_s:,.2f} MB/s is {expected:,.3f} TB"
    )


@pytest.mark.problem
def test_the_rest_of_the_model_is_as_it_was(base, extended):
    """The problem adds to the file. It does not rewrite what was there."""
    for name, node in base.nodes.items():
        after = extended.nodes.get(name)
        assert after is not None, f"{name} is gone; add a node, do not remove one"
        assert after.unit == node.unit, f"{name}: the unit changed from {node.unit!r}"
        assert getattr(after, "formula_text", "") == getattr(node, "formula_text", ""), (
            f"{name}: the formula changed"
        )


def test_the_two_computable_chains_are_still_there(base):
    """Scaffolding: the problem's subject exists and is not blocked."""
    blocked = base.blocked()
    for name in ("metrics_ingest", "logs_ingest"):
        assert name in base.nodes and name not in blocked, (
            f"{name} is missing or blocked; problem 2.2 needs rewriting"
        )


def test_the_text_the_reader_is_handed_loads_from_a_file_of_its_own(base, tmp_path):
    """Scaffolding: the route the grader takes, writing text to a file elsewhere and loading it,
    finds the model's measured constants and gives the model as the book loads it."""
    path = tmp_path / "model.yaml"
    path.write_text(Path(MODEL).read_text())
    again = load_model(path)
    assert set(again.nodes) == set(base.nodes)
    assert again.blocked() == base.blocked()
    assert point(again) == point(base)
