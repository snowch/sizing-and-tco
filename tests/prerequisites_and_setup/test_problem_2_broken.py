"""Problem 0.2 - a model that loads and is still wrong.

The error has to survive loading and be caught by the dimensional pass. That is the whole
distinction: a typo fails immediately and teaches nothing, while a unit error is confidently
wrong and is the failure mode this toolkit exists for.
"""

from __future__ import annotations

import pytest

from sizing.dsl import load_model
from sizing.evaluate import check_units
from tests.prerequisites_and_setup.stubs import a_model_that_does_not_typecheck


@pytest.fixture
def written(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text(a_model_that_does_not_typecheck())
    return path


@pytest.mark.problem
def test_it_loads_before_it_fails(written):
    """If it fails at load, the error was a typo and not a unit error."""
    load_model(written)


@pytest.mark.problem
def test_the_dimensional_pass_refuses_it(written):
    problems, _ = check_units(load_model(written))
    assert problems, (
        "the model typechecks, so the error is not a dimensional one. A node has to declare a "
        "unit its own formula cannot produce - check that you have not simply made the arithmetic "
        "wrong, which the build has no way to notice."
    )


@pytest.mark.problem
def test_the_message_names_the_node(written):
    model = load_model(written)
    problems, _ = check_units(model)
    assert any(name in line for line in problems for name in model.nodes), (
        f"a unit error has to say which node: {problems}"
    )


def test_the_books_models_all_typecheck():
    """Scaffolding: the checker the reader is trying to trip is not tripping on everything."""
    from sizing.dsl import discover

    for model in discover():
        assert not check_units(model)[0], f"{model.name} does not typecheck"
