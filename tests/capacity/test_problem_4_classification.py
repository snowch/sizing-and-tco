"""Problem 9.4 - the classification the whole book rests on, from the inside.

The reader is handed every node's kind and what it reads, and names what has to go. The test
takes those nodes out of the model, outputs included, and asks the model what it is now.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from sizing.dsl import Model, load_model, load_scenario
from sizing.evaluate import check_units, point
from tests.capacity.stubs import what_to_remove


@pytest.fixture(scope="module")
def base():
    return load_model("models/web_service/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/web_service/scenarios/reference.yaml")


def declared(model: Model) -> tuple[dict[str, str], dict[str, set[str]]]:
    """What the reader is handed: every node's kind, and the names each one reads."""
    kinds = {name: node.kind for name, node in model.nodes.items()}
    feeds = {name: set(node.depends_on()) for name, node in model.nodes.items()}
    return kinds, feeds


def without(model: Model, names: list[str]) -> Model:
    """The model with these nodes deleted, and the outputs among them dropped."""
    removed = set(names)
    unknown = sorted(removed - set(model.nodes))
    assert not unknown, f"the model has no node called {unknown[:5]}"
    orphaned = {
        name: sorted(removed & node.depends_on())
        for name, node in model.nodes.items()
        if name not in removed and removed & node.depends_on()
    }
    assert not orphaned, "these read something you deleted, so they cannot be worked out: " + (
        "; ".join(f"{name} reads {reads}" for name, reads in sorted(orphaned.items())[:5])
        + ". Everything downstream of a deleted node goes with it."
    )
    nodes = {name: node for name, node in model.nodes.items() if name not in removed}
    outputs = tuple(output for output in model.outputs if output not in removed)
    return replace(model, nodes=nodes, outputs=outputs)


def converted(model: Model) -> Model:
    return without(model, what_to_remove(*declared(model)))


@pytest.mark.problem
def test_it_classifies_as_a_definitional_model(base):
    after = converted(base)
    assert after.classification == "definitional", (
        f"still a {after.classification} model. A model is a conditional model if it has a "
        "measured node or a ceiling in it - both, here."
    )
    assert not after.of_kind("measured") and not after.of_kind("ceiling")


@pytest.mark.problem
def test_it_still_works(base, scenario):
    after = converted(base)
    assert not check_units(after)[0]
    values = point(after, scenario)
    assert set(after.outputs) & set(base.outputs), (
        "keep at least one of the original outputs working"
    )
    for output in after.outputs:
        assert output in values, f"{output} no longer evaluates"


@pytest.mark.problem
def test_you_said_what_was_lost():
    """The part that is not arithmetic.

    Not graded for content - nothing here can grade a sentence. Graded for existing, because a
    model you cannot say the limits of is a model you should not hand to anybody.
    """
    doc = what_to_remove.__doc__ or ""
    marker = "What it can no longer say:"
    said = doc.split(marker, 1)[1].strip() if marker in doc else ""
    assert len(said.split()) >= 4, (
        "finish the last line of the stub's docstring with one sentence naming what the "
        "definitional model can no longer tell anybody. If you cannot name it, you removed something that was "
        "doing no work."
    )


def test_the_web_service_model_is_conditional_to_begin_with(base):
    """Scaffolding: there is something to remove."""
    assert base.classification == "conditional"
    assert base.of_kind("measured") and base.of_kind("ceiling")


def test_an_output_survives_the_removal(base):
    """Scaffolding: at least one output reads no measured constant and no ceiling, however far
    back, so the problem's demand that one survive can be met."""
    deciding = {node.name for node in base.of_kind("measured") + base.of_kind("ceiling")}
    survivors = [o for o in base.outputs if o not in deciding and not base.ancestors(o) & deciding]
    assert survivors, "every output rests on a measured constant or a ceiling"


def test_deleting_nothing_leaves_the_model_as_it_was(base, scenario):
    """Scaffolding: the route the grader takes is faithful."""
    kinds, feeds = declared(base)
    assert set(kinds) == set(feeds) == set(base.nodes)
    assert point(without(base, []), scenario) == point(base, scenario)
