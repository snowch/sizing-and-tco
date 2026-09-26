"""Problem 2.2 - a rate times an amount of time, and not a rate times a number.

The reader's artefact is a fragment of a model file, spliced into the observability model here
and made an output. The refusals are the toolkit's own: the dimensional pass for the unit, and
the verifier's rules for everything an added input has to declare. The model's own numbers are
the oracle, read at test time, so there is nothing to look up.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import check_units, point

MODEL = "models/observability/model.yaml"
SCENARIO = "models/observability/scenarios/reference.yaml"
FRAGMENT = "tests/what_a_workload_is/problem_2_daily_ingest.yaml"
#: The file the page shows under the problem, editable, and writes back before grading.
EDITABLE = (FRAGMENT,)

SECONDS_PER_DAY = 86_400
BYTES_PER_TB = 1e12


def _verifier():
    spec = importlib.util.spec_from_file_location("verify_models", "scripts/verify-models.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fragment() -> dict:
    """The nodes the fragment declares, by name."""
    declared = yaml.safe_load(Path(FRAGMENT).read_text()) or {}
    assert isinstance(declared, dict), "the fragment is a set of nodes, each under its own name"
    return declared


def spliced(tmp_path: Path, added: dict, outputs: tuple[str, ...]):
    """The observability model with ``added`` under ``nodes:``, loaded as the build loads it."""
    data = yaml.safe_load(Path(MODEL).read_text())
    data["nodes"].update(added)
    data["outputs"] = [*data["outputs"], *outputs]
    path = tmp_path / "model.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    return load_model(path)


@pytest.fixture(scope="module")
def base():
    return load_model(MODEL)


@pytest.fixture(scope="module")
def scenario():
    return load_scenario(SCENARIO)


@pytest.fixture
def extended(tmp_path, base):
    added = fragment()
    node = added.get("daily_ingest")
    assert isinstance(node, dict), f"{FRAGMENT} has no node called daily_ingest"
    formula = str(node.get("formula") or "").strip()
    assert formula, f"daily_ingest has no formula yet. Write one in {FRAGMENT}."
    clash = sorted(set(added) & set(base.nodes))
    assert not clash, (
        f"{', '.join(clash)} is already in the model. The fragment adds nodes; it does not "
        "replace them, so give yours a name of its own."
    )
    return spliced(tmp_path, added, ("daily_ingest",))


@pytest.mark.problem
def test_the_node_is_an_amount(extended):
    unit = extended.nodes["daily_ingest"].unit
    assert unit == "TB", (
        f"daily_ingest declares {unit!r}. The problem asks for the data that arrives in one "
        "day: an amount, in TB, and not a rate."
    )


@pytest.mark.problem
def test_it_typechecks(extended):
    problems, _ = check_units(extended)
    assert not problems, (
        "\n".join(problems)
        + "\n\nA rate multiplied by a pure number is still a rate. Something in the formula has "
        "to carry a duration."
    )


@pytest.mark.problem
def test_the_verifier_accepts_it(extended):
    """What the build holds every input in the book to, held to the ones you added."""
    problems: list[str] = []
    _verifier().check_model(extended, problems)
    assert not problems, "\n".join(problems)


@pytest.mark.problem
def test_it_is_one_day_of_metrics_and_logs(extended, scenario):
    waiting_on = extended.blocked().get("daily_ingest")
    assert not waiting_on, (
        f"daily_ingest has no value: it depends on {', '.join(waiting_on)}, which nobody has "
        "measured. The problem asks for metrics and logs only."
    )
    values = point(extended, scenario)
    # Derived from the model at test time: whatever the ingest rate currently is, a day of it is
    # this. Nothing here is stored, so changing the model changes what the problem wants.
    rate_mb_per_s = values["metrics_ingest"] + values["logs_ingest"]
    expected = rate_mb_per_s * 1e6 * SECONDS_PER_DAY / BYTES_PER_TB
    # Compared outside the assert, so that a failure cannot print the value it was compared with.
    one_day_of_it = values["daily_ingest"] == pytest.approx(expected, rel=1e-6)
    assert one_day_of_it, (
        f"daily_ingest is {values['daily_ingest']:,.3f} TB, which is not one day of metrics and "
        "logs arriving at known_ingest's rate. Check how long your duration node says it is, "
        "and which rate the formula starts from."
    )


def test_the_rate_the_problem_names_is_there_and_the_traces_are_not(base):
    """Scaffolding: the problem says known_ingest holds metrics and logs, and that traces are
    left out because they cannot be computed. Both have to stay true."""
    blocked = base.blocked()
    node = base.nodes.get("known_ingest")
    assert node is not None and node.unit == "MB/s" and "known_ingest" not in blocked, (
        "known_ingest is missing, blocked or no longer a rate; problem 2.2 needs rewriting"
    )
    assert "total_ingest" in blocked, (
        "the traces chain has a value now; problem 2.2 can ask for all three signals"
    )


def test_the_model_as_shipped_passes_the_verifier(base):
    """Scaffolding: every refusal the reader meets is about the nodes they added."""
    problems: list[str] = []
    _verifier().check_model(base, problems)
    assert not problems, "\n".join(problems)


def test_splicing_nothing_changes_nothing(base, tmp_path):
    """Scaffolding: the route the grader takes, through YAML and a file elsewhere, gives the
    model as the book loads it, measured constants and all."""
    again = spliced(tmp_path, {}, ())
    assert set(again.nodes) == set(base.nodes)
    assert again.blocked() == base.blocked()
    assert point(again) == point(base)
