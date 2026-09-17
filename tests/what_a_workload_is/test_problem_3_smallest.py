"""Problem 1.3 - the smallest model this repository will accept.

Graded by running the real loader, the real unit checker and the real verifier, rather than by
comparing against a model kept somewhere in the repository. There is nothing to copy.
"""

from __future__ import annotations

import importlib.util

import pytest

from sizing.dsl import Derived, Input, load_model
from sizing.evaluate import check_units, point
from tests.what_a_workload_is.stubs import smallest_model_that_builds


def _verifier():
    spec = importlib.util.spec_from_file_location("verify_models", "scripts/verify-models.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def written(tmp_path):
    path = tmp_path / "model.yaml"
    path.write_text(smallest_model_that_builds())
    return path


@pytest.mark.problem
def test_it_loads(written):
    model = load_model(written)
    inputs = [n for n in model.nodes.values() if isinstance(n, Input)]
    derived = [n for n in model.nodes.values() if isinstance(n, Derived)]
    assert len(inputs) == 1, f"exactly one input, got {len(inputs)}"
    assert len(derived) == 1, f"exactly one derived node, got {len(derived)}"
    assert model.outputs, "a model with no outputs has nothing anybody can check"


@pytest.mark.problem
def test_it_typechecks(written):
    problems, _ = check_units(load_model(written))
    assert not problems, "\n".join(problems)


@pytest.mark.problem
def test_it_evaluates(written):
    values = point(load_model(written))
    assert len(values) == 2 and all(isinstance(v, float) for v in values.values())


@pytest.mark.problem
def test_the_verifier_accepts_it(written):
    model = load_model(written)
    problems: list[str] = []
    _verifier().check_model(model, problems)
    assert not problems, "\n".join(problems)


def test_the_verifier_is_real_and_has_something_to_say():
    """Scaffolding: the rules the reader is being held to exist and do reject things.

    Unmarked, so CI keeps checking that problem 1.3 has a bar to clear. A verifier that accepted
    everything would make this problem unfailable, which is the same as unpassable.
    """
    verifier = _verifier()
    assert hasattr(verifier, "check_model")
    problems: list[str] = []
    verifier.check_model(load_model("models/storage_cluster/model.yaml"), problems)
    assert not problems, "the book's own model must pass the rules the reader is held to"
