"""Problem 1.3 - cost model or sizing model, read from the stage text in the chapter.

Six stages of the web service model appear in the chapter. The reader reads each one and decides
whether it is a cost or sizing model by looking for measured constants and ceilings.

The kind changes partway along, and the reader who can say exactly where has understood the
distinction the rest of the book rests on.
"""

from __future__ import annotations

import pytest

from sizing.dsl import load_model
from tests.point_estimates.stubs import nodes_that_decide_it, stages_and_kinds

#: The web service model as ch02 to ch07 leave it, in order. Derived files, checked by
#: ``python3 -m bench.stages --check``, so they cannot drift from the finished model.
STAGES = (
    "models/web_service/stages/01-demand/model.yaml",
    "models/web_service/stages/02-provenance/model.yaml",
    "models/web_service/stages/03-uncertainty/model.yaml",
    "models/web_service/stages/04-littles_law/model.yaml",
    "models/web_service/stages/05-queueing/model.yaml",
    "models/web_service/stages/06-scaling/model.yaml",
)


def deciders(model) -> list[str]:
    """Every node that makes a model a sizing model, by the rule the build applies."""
    return sorted(
        name for name, node in model.nodes.items() if type(node).__name__ in ("Measured", "Ceiling")
    )


def expected_kinds():
    """The correct classifications: cost or sizing for each stage."""
    return ["sizing" if deciders(load_model(path)) else "cost" for path in STAGES]


def expected_change():
    """The stage number (1-6) where the model changes from cost to sizing."""
    kinds = expected_kinds()
    for i in range(1, len(kinds)):
        if kinds[i] != kinds[i - 1]:
            return i + 1  # stage numbers are 1-indexed
    raise AssertionError("no kind change found")


@pytest.mark.problem
def test_the_classifications_are_right():
    kinds, change = stages_and_kinds()
    expected = expected_kinds()
    assert len(kinds) == 6, f"you gave {len(kinds)} classifications, need 6"
    assert kinds == expected, (
        f"you classified: {kinds}. The six stages are: {expected}. "
        f"Look for measured constants and ceilings."
    )
    assert change == expected_change(), (
        f"you said the kind changes at stage {change}. It actually changes at stage {expected_change()}."
    )


@pytest.mark.problem
def test_the_nodes_are_named():
    _kinds, _change = stages_and_kinds()
    answer = nodes_that_decide_it()
    # Find which stage it changes at and get the deciders at that stage
    change_stage = expected_change()
    model = load_model(STAGES[change_stage - 1])
    expected = deciders(model)
    assert answer == expected, (
        f"you named: {answer}. At stage {change_stage}, the nodes that make it a sizing model are: {expected}."
    )


def test_the_model_changes_kind_exactly_once():
    """Scaffolding: the problem is a real choice, and it has a single turning point."""
    kinds = expected_kinds()
    assert set(kinds) == {"cost", "sizing"}, f"only found {set(kinds)}"
    changes = [i for i in range(1, len(kinds)) if kinds[i] != kinds[i - 1]]
    assert len(changes) == 1, f"the kind changes {len(changes)} times, at stages {changes}"
    assert kinds[0] == "cost", "the model should start as a cost model and become a sizing one"
