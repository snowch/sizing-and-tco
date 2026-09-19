"""Problem 1.2 - cost model or sizing model, graded against the rule the build enforces.

Not several different models: one model at six stages of being built, which is how the book
builds it. The kind changes partway along, and the reader who can say exactly where has understood the
distinction the rest of the book rests on.

The reader decides by reading the files. The test decides from the node types the loader
produced, which is the rule ``scripts/verify-models.py`` applies to every model here: a model
with a measured constant or a declared ceiling in it **is** a sizing model.
"""

from __future__ import annotations

import pytest

from sizing.dsl import load_model
from tests.what_one_number_hides.stubs import kind_of, what_decides_it

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


@pytest.fixture(scope="module", params=STAGES)
def model(request):
    return load_model(request.param)


@pytest.mark.problem
def test_the_kind_is_right(model):
    expected = "sizing" if deciders(model) else "cost"
    assert kind_of(model) == expected, (
        f"{model.name} is a {expected} model. What decides it: "
        f"{deciders(model) or 'nothing - no measured constant and no ceiling'}"
    )


@pytest.mark.problem
def test_the_nodes_that_decide_it_are_named(model):
    assert what_decides_it(model) == deciders(model)


def test_the_model_changes_kind_exactly_once():
    """Scaffolding: the problem is a real choice, and it has a single turning point.

    A stage list that was all one kind would make the problem one answer repeated; a list that
    changed back and forth would mean the stages were not subsets of one another, which
    ``bench/stages.py`` is supposed to guarantee.
    """
    kinds = ["sizing" if deciders(load_model(path)) else "cost" for path in STAGES]
    assert set(kinds) == {"cost", "sizing"}, f"only found {set(kinds)}"
    changes = [i for i in range(1, len(kinds)) if kinds[i] != kinds[i - 1]]
    assert len(changes) == 1, f"the kind changes {len(changes)} times, at stages {changes}"
    assert kinds[0] == "cost", "the model should start as a cost model and become a sizing one"
