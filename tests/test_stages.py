"""The model the book builds is the model the repository has.

The book introduces its running example a few nodes at a time, and a reader who follows it is
being told a story about how the file came to look the way it does. That story is checkable, and
these tests check it, because the alternative is a chapter that goes on describing a model
somebody edited last month.

Every staged model is held to this, not only the one the chapters are currently about: a model
being built beside the old one has to pass here before a single chapter points at it.

The load-bearing one is `test_every_node_is_introduced_by_some_chapter`. A node nobody introduces
is a node the reader meets fully formed in a figure, and the book never says where it came from.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

from bench.outline import CHAPTERS, RUNNING_EXAMPLE
from bench.stages import (
    all_stages,
    build,
    model_path,
    nodes_by,
    out_dir,
    staged_models,
    stages,
    write_all,
)
from sizing.dsl import load_model

ROOT = Path(__file__).resolve().parent.parent


def _verify_models():
    """`scripts/verify-models.py` is a script, not a module, and its name has a dash in it."""
    spec = importlib.util.spec_from_file_location(
        "verify_models", ROOT / "scripts/verify-models.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODELS = staged_models()
STAGES = all_stages()


def real(model: str) -> dict:
    return yaml.safe_load(model_path(model).read_text())


@pytest.fixture(scope="module", autouse=True)
def built():
    """Every test here reads the built files, so build them once."""
    return write_all()


def test_the_running_example_is_a_staged_model():
    assert RUNNING_EXAMPLE in MODELS, (
        f"bench.outline.RUNNING_EXAMPLE names {RUNNING_EXAMPLE!r}, which carries no "
        f"build-order.yaml. The chapters cannot build a model that has no stages."
    )


# -- coverage: the book accounts for the whole model ----------------------------------------------


@pytest.mark.parametrize("model", MODELS)
def test_every_node_is_introduced_by_some_chapter(model):
    named = [name for stage in stages(model) for name in stage.introduces]
    missing = sorted(set(real(model)["nodes"]) - set(named))
    assert not missing, (
        f"{len(missing)} node(s) in {model} that no chapter introduces: {missing}. "
        "A reader meets them fully formed in a figure and is never told where they came from. "
        f"Add each one to the stage of models/{model}/build-order.yaml whose chapter earns it."
    )


@pytest.mark.parametrize("model", MODELS)
def test_no_node_is_introduced_twice(model):
    named = [name for stage in stages(model) for name in stage.introduces]
    twice = sorted({n for n in named if named.count(n) > 1})
    assert not twice, f"{model}: introduced by more than one chapter: {twice}"


@pytest.mark.parametrize("model", MODELS)
def test_no_stage_introduces_a_node_the_model_does_not_have(model):
    named = {name for stage in stages(model) for name in stage.introduces}
    extra = sorted(named - set(real(model)["nodes"]))
    assert not extra, f"{model}'s build-order.yaml names nodes the model does not have: {extra}"


@pytest.mark.parametrize("model", MODELS)
def test_the_last_stage_is_the_whole_model(model):
    last = stages(model)[-1]
    assert set(nodes_by(model, last.index)) == set(real(model)["nodes"])


# -- the story: forwards only, and in reading order -----------------------------------------------


@pytest.mark.parametrize(
    "stage", [s for s in STAGES if s.index > 1], ids=lambda s: f"{s.model}:{s.stage}"
)
def test_a_stage_never_takes_a_node_away(stage):
    """A model the reader watched being built does not lose parts of itself."""
    before = set(nodes_by(stage.model, stage.index - 1))
    after = set(nodes_by(stage.model, stage.index))
    assert before <= after, f"{stage.name} drops {sorted(before - after)}"


@pytest.mark.parametrize("model", MODELS)
def test_the_stages_run_in_the_book_s_own_order(model):
    """A node cannot arrive in ch09 and be shown in ch03."""
    position = {chapter.slug: i for i, chapter in enumerate(CHAPTERS)}
    for stage in stages(model):
        assert stage.chapter in position, (
            f"{model}: stage {stage.stage!r} names chapter {stage.chapter!r}, which is not in "
            "the outline"
        )
    order = [position[stage.chapter] for stage in stages(model)]
    assert order == sorted(order), (
        f"{model}: stages are out of reading order: {[(s.stage, s.chapter) for s in stages(model)]}"
    )


# -- every stage is a real model ------------------------------------------------------------------


@pytest.mark.parametrize("stage", STAGES, ids=lambda s: f"{s.model}:{s.stage}")
def test_a_stage_obeys_every_rule_the_finished_model_obeys(stage):
    problems: list[str] = []
    _verify_models().check_model(load_model(stage.path), problems)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("stage", STAGES, ids=lambda s: f"{s.model}:{s.stage}")
def test_a_stage_is_the_kind_of_model_the_book_says_it_is(stage):
    """The moment a cost model becomes a sizing model is the book's thesis, so it is pinned here.

    Not by asserting it: by asking the loader, which decides from the file. If somebody moves the
    measured constant or the ceiling to a different chapter, this fails and the chapter that
    claims the change of kind is the one that has to move.
    """
    model = load_model(stage.path)
    got = "sizing" if model.is_sizing_model else "cost"
    assert got == stage.classification, (
        f"stage {stage.name} ({stage.chapter}) is declared a {stage.classification} model and "
        f"the build makes it a {got} one"
    )


@pytest.mark.parametrize("model", MODELS)
def test_the_change_of_kind_happens_exactly_once(model):
    kinds = [stage.classification for stage in stages(model)]
    assert kinds == sorted(kinds, key=["cost", "sizing"].index), (
        f"{model}: a model does not go back to being a cost model: {kinds}"
    )
    assert "cost" in kinds and "sizing" in kinds, (
        f"{model}: the book's thesis is that a model changes kind when it gains a measured "
        f"constant or a ceiling. These stages never show that happening: {kinds}"
    )


# -- the one edit a stage may make ----------------------------------------------------------------


@pytest.mark.parametrize("stage", STAGES, ids=lambda s: f"{s.model}:{s.stage}")
def test_a_stage_only_holds_back_uncertainty_that_is_really_coming(stage):
    """`certain_for_now` says a shape arrives later. It had better arrive."""
    nodes = real(stage.model)["nodes"]
    for name in stage.certain_for_now:
        assert name in nodes, f"{stage.name}: {name!r} is not a node"
        assert "distribution" in nodes[name], (
            f"{stage.name} holds back the shape of {name!r}, but the finished model never gives "
            "it one, so the stage is not showing an earlier version of anything"
        )


@pytest.mark.parametrize("stage", STAGES, ids=lambda s: f"{s.model}:{s.stage}")
def test_a_stage_changes_nothing_else_about_a_node(stage):
    """Everything except a held-back distribution is copied from the real model verbatim."""
    nodes = real(stage.model)["nodes"]
    for name, spec in build(stage)["nodes"].items():
        if name in stage.certain_for_now:
            continue
        assert spec == nodes[name], (
            f"{stage.name} shows {name!r} differently from models/{stage.model}/model.yaml. A "
            "stage selects nodes; it does not rewrite them."
        )


@pytest.mark.parametrize("model", MODELS)
def test_the_last_stage_is_not_a_second_copy_of_the_model(model):
    """The stage with every node in it is the model, and there is one of those.

    It used to be written out and stamped like the rest, which put a byte-identical copy of the
    model file in the repository and a 223K copy of its reference result beside the original --
    both regenerated on every build.
    """
    finished = [stage for stage in stages(model) if stage.is_the_finished_model]
    assert len(finished) == 1, (
        f"{model}: {len(finished)} stage(s) hold the whole model; expected exactly 1"
    )
    assert finished[0] is stages(model)[-1] or finished[0] == stages(model)[-1], (
        f"{model}: the stage holding the whole model is not the last one"
    )
    assert finished[0].path == model_path(model), (
        f"{model}: the finished stage should point at the model itself"
    )
    assert not (out_dir(model) / f"{finished[0].index:02d}-{finished[0].stage}").exists(), (
        f"{model}: the finished stage has been written out as a second copy of the model"
    )
