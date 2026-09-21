"""Problem 2.1 - levels against rates, graded against the units rather than a list.

The oracle is the model's own declared units, which the reader is not looking at when they answer:
they are reading names and notes. Two independent routes to the same classification, and a
disagreement means one of them is wrong.
"""

from __future__ import annotations

import pytest
from pint.util import to_units_container

from sizing.dsl import load_model
from sizing.units import parse as parse_unit
from tests.what_a_workload_is.stubs import stocks_and_flows

MODEL = "models/observability/model.yaml"


@pytest.fixture(scope="module")
def model():
    return load_model(MODEL)


def by_dimension(unit: str) -> str:
    """What a unit says a quantity is, independently of what anybody called it."""
    parsed = parse_unit(unit)
    time = parsed.dimensionality.get("[time]", 0)
    if time < 0:
        return "flow"
    if time > 0:
        return "neither"  # a duration is not a level
    # A level is an amount of something: bytes, hosts, dollars, series. Bytes carry no
    # dimension of their own in the registry, so this reads the unit's parts rather than its
    # dimensions. A bare number is neither, and so is anything per something else.
    parts = to_units_container(parsed)
    return "stock" if parts and all(power > 0 for power in parts.values()) else "neither"


@pytest.mark.problem
def test_every_node_is_classified(model):
    answer = stocks_and_flows(model)
    missing = set(model.nodes) - set(answer)
    assert not missing, f"no classification for {sorted(missing)[:5]}"
    assert set(answer.values()) <= {"stock", "flow", "neither"}


@pytest.mark.problem
def test_the_classification_agrees_with_the_units(model):
    answer = stocks_and_flows(model)
    wrong = {
        name: (answer[name], by_dimension(node.unit))
        for name, node in model.nodes.items()
        if answer.get(name) != by_dimension(node.unit)
    }
    assert not wrong, (
        "these disagree with what the model's own units say they are:\n  "
        + "\n  ".join(
            f"{name}: you said {mine}, the unit {model.nodes[name].unit!r} says {theirs}"
            for name, (mine, theirs) in sorted(wrong.items())[:8]
        )
        + "\nOne of the two readings is wrong. Work out which before changing your answer."
    )


def test_the_model_has_all_three_kinds(model):
    """Scaffolding: the problem is not three copies of one answer."""
    found = {by_dimension(node.unit) for node in model.nodes.values()}
    assert found == {"stock", "flow", "neither"}, f"only found {found}"
