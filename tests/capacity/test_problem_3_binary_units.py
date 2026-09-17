"""Problem 9.3 - TB against TiB, which is ten per cent and a lot of arguments."""

from __future__ import annotations

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import check_units, point
from tests.capacity.stubs import in_binary_units

#: 2^40 over 10^12. The number at the bottom of the difference.
TIB_PER_TB = 1_000_000_000_000 / 2**40


@pytest.fixture(scope="module")
def base():
    return load_model("models/storage_cluster/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/storage_cluster/scenarios/reference.yaml")


@pytest.mark.problem
def test_every_terabyte_node_changed_unit(base):
    converted = in_binary_units(base)
    was = {n for n, node in base.nodes.items() if node.unit == "TB"}
    assert was, "the model has no TB nodes; problem 1.2 needs rewriting"
    for name in was:
        assert converted.nodes[name].unit == "TiB", (
            f"{name} is still in {converted.nodes[name].unit}"
        )


@pytest.mark.problem
def test_nothing_else_changed(base):
    converted = in_binary_units(base)
    for name, node in base.nodes.items():
        after = converted.nodes[name]
        assert getattr(after, "formula_text", "") == getattr(node, "formula_text", ""), (
            f"{name}: the formula changed. The build converts; doing it by hand is how two "
            "copies of a model start to disagree."
        )
        if node.kind == "input":
            assert after.value == node.value and after.distribution == node.distribution, (
                f"{name}: an input value or distribution changed"
            )


@pytest.mark.problem
def test_it_still_typechecks(base):
    problems, _ = check_units(in_binary_units(base))
    assert not problems, "\n".join(problems)


@pytest.mark.problem
def test_the_numbers_are_smaller_by_exactly_the_ratio(base, scenario):
    before = point(base, scenario)
    after = point(in_binary_units(base), scenario)
    changed = [n for n, node in base.nodes.items() if node.unit == "TB" and node.kind != "input"]
    for name in changed:
        assert after[name] == pytest.approx(before[name] * TIB_PER_TB, rel=1e-9), (
            f"{name}: {before[name]:,.1f} TB should read {before[name] * TIB_PER_TB:,.1f} TiB. "
            "The same bytes counted in bigger units is a smaller number."
        )


def test_the_two_terabytes_really_do_differ():
    """Scaffolding: the problem is about something.

    If this ever fails, somebody has redefined a unit and the chapter needs rewriting rather than
    the test.
    """
    assert 0.9 < TIB_PER_TB < 0.92, TIB_PER_TB
