"""Problem 11.3 - add a ceiling, and meet the three things declaring one commits you to."""

from __future__ import annotations

import pytest

from sizing.dsl import Ceiling, load_model
from sizing.evaluate import check_units, evaluate, load_scenario
from tests.headroom_and_failure_domains.stubs import add_a_ceiling

NAME, OF, LIMIT, HEADROOM = "drive_pressure", "raw_capacity / installed_raw_capacity", 1.0, 0.2


@pytest.fixture(scope="module")
def base():
    return load_model("models/storage_cluster/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/storage_cluster/scenarios/reference.yaml")


@pytest.fixture
def extended(base):
    return add_a_ceiling(base, NAME, OF, LIMIT, HEADROOM)


@pytest.mark.problem
def test_the_ceiling_exists_and_is_a_ceiling(extended):
    node = extended.nodes.get(NAME)
    assert isinstance(node, Ceiling), f"{NAME} is {type(node).__name__}, not a Ceiling"
    assert NAME in extended.outputs, "a ceiling that is not an output is a ceiling nobody reads"


@pytest.mark.problem
def test_it_declares_a_margin_and_a_reason(extended):
    node = extended.nodes[NAME]
    assert node.declares_headroom, (
        "a limit with no margin is not a sizing rule - it is a number with an inequality "
        "next to it (ch11)"
    )
    assert node.because.strip(), (
        "a margin nobody can argue with gets copied into the next model by somebody who does "
        "not know what it was for"
    )


@pytest.mark.problem
def test_it_typechecks(extended):
    problems, _ = check_units(extended)
    assert not problems, "\n".join(problems)


@pytest.mark.problem
def test_it_reports_a_verdict_and_a_probability(extended, scenario):
    report = evaluate(extended, scenario).ceilings[NAME]
    assert report["verdict"] in ("ok", "inside headroom", "over")
    assert report["allowed"] == pytest.approx(LIMIT * (1 - HEADROOM))
    assert 0.0 <= report["p_over_limit"] <= 1.0, (
        "a ceiling's real output is how often the model breaches it, not where the point "
        "estimate happens to sit"
    )


def test_the_expression_the_problem_names_is_real(base):
    """Scaffolding: the nodes the reader is asked to watch exist in the model as shipped."""
    for needed in ("raw_capacity", "installed_raw_capacity"):
        assert needed in base.nodes, f"{needed} is gone; problem 11.3 needs rewriting"
