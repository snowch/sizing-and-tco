"""Problem 11.3 - add a ceiling, and meet the three things declaring one commits you to.

The reader's artefact is a fragment of a model file, spliced into the web service model here.
The refusals are the toolkit's own: the loader and the dimensional pass for the unit, and the
verifier's rules for the margin and the reason. Nothing here says what any field should hold.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

from sizing.dsl import Ceiling, load_model
from sizing.evaluate import (
    ceiling_report,
    check_units,
    conversion_factors,
    evaluate,
    load_scenario,
    point,
)

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


def declared_margin(model, ceiling: Ceiling, scenario, where: Path) -> float:
    """The margin a ceiling declares, worked out by the model as an ordinary derived node.

    A margin may be a number, the name of a node that holds one, or an expression, as in the
    model file. Spliced in as a formula and evaluated at the scenario's point, all three
    are read the same way, and none of them through the report the test is checking."""
    data = yaml.safe_load(Path(model.path).read_text())
    data["nodes"]["declared_margin_probe"] = {
        "kind": "derived",
        "unit": "dimensionless",
        "formula": ceiling.headroom_text,
    }
    probe = where / "probe.yaml"
    probe.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    return point(load_model(probe), scenario)["declared_margin_probe"]


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
def test_it_reports_a_verdict_and_a_probability(extended, scenario, tmp_path):
    name, _ = fragment()
    node = extended.nodes[name]
    assert node.declares_headroom, (
        f"{name} declares no margin yet, so there is no allowed line to report against"
    )
    report = evaluate(extended, scenario).ceilings[name]
    assert report["verdict"] in ("ok", "inside headroom", "over")
    margin = declared_margin(extended, node, scenario, tmp_path)
    assert report["allowed"] == pytest.approx(report["limit"] * (1 - margin)), (
        "the allowed line is the limit less the margin you declared"
    )
    assert 0.0 <= report["p_over_limit"] <= 1.0, (
        "a ceiling's real output is how often the model breaches it, not where the point "
        "estimate happens to sit"
    )


def test_a_margin_is_read_in_every_form_the_model_file_uses(scenario, tmp_path):
    """Scaffolding: the web service declares margins by number and by a node's name, and the
    grader reads both the way the toolkit does."""
    base = load_model(MODEL)
    report = ceiling_report(base, point(base, scenario), {}, conversion_factors(base))
    forms = set()
    for ceiling in base.of_kind("ceiling"):
        if ceiling.name in report:
            margin = declared_margin(base, ceiling, scenario, tmp_path)
            assert margin == pytest.approx(report[ceiling.name]["headroom"]), ceiling.name
            forms.add(ceiling.headroom_text in base.nodes)
    assert forms == {True, False}, "the model no longer shows both forms of margin"


def test_the_expression_the_problem_names_is_real():
    """Scaffolding: the nodes the fragment watches exist in the model as shipped."""
    base = load_model(MODEL)
    for needed in ("concurrency", "host_count"):
        assert needed in base.nodes, f"{needed} is gone; problem 11.3 needs rewriting"
