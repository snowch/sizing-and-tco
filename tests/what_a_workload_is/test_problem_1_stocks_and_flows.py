"""Problem 2.1 - levels against rates, graded against the units rather than a list.

The oracle is the model's own declared units, which the reader is not looking at when they answer:
they are handed names and the words the file puts beside them, and no unit. Two independent routes
to the same classification, and a disagreement means one of them is wrong.
"""

from __future__ import annotations

import pytest
from pint.util import to_units_container

from sizing.dsl import load_model
from sizing.evaluate import check_units
from sizing.units import parse as parse_unit
from tests.what_a_workload_is.stubs import stocks_and_flows

MODEL = "models/observability/model.yaml"
#: How many disagreements a failure lists. Enough to see a pattern, few enough to read.
SHOWN = 12


@pytest.fixture(scope="module")
def model():
    return load_model(MODEL)


@pytest.fixture(scope="module")
def in_words(model) -> dict[str, str]:
    """What the reader is handed: every node, as the file describes it and never as a unit."""
    return {
        name: node.label or node.note or name.replace("_", " ")
        for name, node in model.nodes.items()
    }


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
def test_every_node_is_classified(model, in_words):
    answer = stocks_and_flows(in_words)
    missing = set(model.nodes) - set(answer)
    assert not missing, f"no classification for {sorted(missing)[:5]}"
    assert set(answer.values()) <= {"stock", "flow", "neither"}


@pytest.mark.problem
def test_the_classification_agrees_with_the_units(model, in_words):
    answer = stocks_and_flows(in_words)
    wrong = sorted(
        name for name, node in model.nodes.items() if answer.get(name) != by_dimension(node.unit)
    )
    shown = wrong[:SHOWN]
    assert not wrong, (
        f"{len(wrong)} of your answers disagree with the unit the model declares:\n  "
        + "\n  ".join(
            f"{name}: you said {answer.get(name)}; its unit is {model.nodes[name].unit!r}"
            for name in shown
        )
        + (f"\n  and {len(wrong) - len(shown)} more" if len(wrong) > len(shown) else "")
        + "\nEvery unit in this model typechecks, so read each one against the rule under "
        "'Four kinds of quantity' and find what your reading of the node missed."
    )


def test_the_model_has_all_three_kinds(model):
    """Scaffolding: the problem is not three copies of one answer."""
    found = {by_dimension(node.unit) for node in model.nodes.values()}
    assert found == {"stock", "flow", "neither"}, f"only found {found}"


def test_every_node_is_described_in_words(model, in_words):
    """Scaffolding: the reader has something other than a unit to go on for every node."""
    assert set(in_words) == set(model.nodes)
    assert all(words.strip() for words in in_words.values())


def test_every_unit_the_reader_is_graded_against_typechecks(model):
    """Scaffolding: the failure message tells the reader every unit typechecks. It has to."""
    problems, _ = check_units(model)
    assert not problems, "\n".join(problems)
