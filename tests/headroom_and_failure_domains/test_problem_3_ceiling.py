"""Problem 11.3 - add a ceiling, and meet the three things declaring one commits you to.

The reader's artefact is a fragment of a model file, spliced into the web service model here.
The refusals are the toolkit's own: the dimensional pass for the unit, and the verifier's rules
for the margin and the reason. Nothing here says what any field should hold.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

from sizing.dsl import Ceiling, load_model
from sizing.evaluate import check_units, evaluate, load_scenario

MODEL = "models/web_service/model.yaml"
SCENARIO = "models/web_service/scenarios/reference.yaml"
FRAGMENT = "tests/headroom_and_failure_domains/problem_3_ceiling.yaml"
#: The file the page shows under the problem, editable, and writes back before grading.
EDITABLE = (FRAGMENT,)


def _verifier():
    spec = importlib.util.spec_from_file_location("verify_models", "scripts/verify-models.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fragment() -> tuple[str, dict]:
    """The one node the fragment declares, by name."""
    declared = yaml.safe_load(Path(FRAGMENT).read_text())
    assert isinstance(declared, dict) and len(declared) == 1, "the fragment declares one node"
    ((name, spec),) = declared.items()
    return name, spec


@pytest.fixture
def extended(tmp_path):
    """The web service model with the fragment's node spliced in and made an output."""
    name, spec = fragment()
    data = yaml.safe_load(Path(MODEL).read_text())
    data["nodes"][name] = spec
    data["outputs"] = [*data["outputs"], name]
    path = tmp_path / "model.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    return load_model(path)


@pytest.fixture(scope="module")
def scenario():
    return load_scenario(SCENARIO)


@pytest.mark.problem
def test_the_ceiling_loads_and_is_a_ceiling(extended):
    name, _ = fragment()
    node = extended.nodes.get(name)
    assert isinstance(node, Ceiling), f"{name} is {type(node).__name__}, not a ceiling"


@pytest.mark.problem
def test_it_typechecks(extended):
    """The first refusal: a ceiling's unit is whatever its expression produces (ch02)."""
    problems, _ = check_units(extended)
    assert not problems, "\n".join(problems)


@pytest.mark.problem
def test_the_verifier_accepts_it(extended):
    """The second and third refusals: a limit with no margin is not a sizing rule, and a margin
    with no reason gets copied into the next model by somebody who does not know what it was
    for. Both are rules scripts/verify-models.py applies to every model in the book."""
    problems: list[str] = []
    _verifier().check_model(extended, problems)
    assert not problems, "\n".join(problems)


@pytest.mark.problem
def test_it_reports_a_verdict_and_a_probability(extended, scenario):
    name, _ = fragment()
    node = extended.nodes[name]
    report = evaluate(extended, scenario).ceilings[name]
    assert report["verdict"] in ("ok", "inside headroom", "over")
    assert report["allowed"] == pytest.approx(report["limit"] * (1 - float(node.headroom_text))), (
        "the allowed line is the limit less the margin you declared"
    )
    assert 0.0 <= report["p_over_limit"] <= 1.0, (
        "a ceiling's real output is how often the model breaches it, not where the point "
        "estimate happens to sit"
    )


def test_the_expression_the_problem_names_is_real():
    """Scaffolding: the nodes the fragment watches exist in the model as shipped."""
    base = load_model(MODEL)
    for needed in ("concurrency", "host_count"):
        assert needed in base.nodes, f"{needed} is gone; problem 11.3 needs rewriting"
