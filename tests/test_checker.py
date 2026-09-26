"""Appendix H's model checker, and the desk command it stands beside.

The page once said it ran the toolkit over a pasted file. It ran a YAML parser and listed the
nodes, said "Model parsed successfully" about files the build refuses, and shipped a starter
model in a shape ``load_model`` rejects. These hold the page and the desk to one verdict: the
starter it ships passes, the files the review wrote fail, and the browser's call gives the
answer ``python3 scripts/verify-models.py <file>`` gives.
"""

from __future__ import annotations

import html
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from sizing.playground.driver import check

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "sizing" / "viewer" / "checker.html"


def _verify_models():
    """`scripts/verify-models.py` is a script, not a module, and its name has a dash in it."""
    spec = importlib.util.spec_from_file_location(
        "verify_models", ROOT / "scripts/verify-models.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def starter() -> str:
    """The model file the checker page opens with, as a reader would copy it."""
    found = re.search(
        r'<textarea id="model-text"[^>]*>(.*?)</textarea>', TEMPLATE.read_text(), re.S
    )
    assert found, "the checker page has no starter model"
    return html.unescape(found[1])


#: Files the toolkit refuses, one fault each. The first is the page's old starter model.
REFUSED = {
    "a separate inputs section": """
inputs:
  requests_per_second: {kind: input, unit: 1/s, range: [100, 10000]}
nodes:
  daily_requests: {kind: derived, unit: 1/d, formula: requests_per_second * 86400}
""",
    "a unit its formula does not produce": """
model: wrong_unit
nodes:
  rate:
    kind: input
    decided: outside
    unit: request/second
    value: 10
    provenance: {kind: assumption, source: "a guess"}
  twice:
    kind: derived
    unit: TB
    formula: rate * 2
outputs: [twice]
""",
    "no provenance": """
model: no_provenance
nodes:
  rate: {kind: input, decided: outside, unit: request/second, value: 10}
  twice: {kind: derived, unit: request/second, formula: rate * 2}
outputs: [twice]
""",
}


def test_the_starter_model_passes_the_checks_the_build_runs(tmp_path):
    path = tmp_path / "model.yaml"
    path.write_text(starter())
    model, problems = _verify_models().check_file(path)
    assert model is not None and not problems, (
        "The checker page opens with a model file the toolkit refuses, so a reader who copies "
        f"its shape writes a file that fails: {problems}"
    )


@pytest.mark.parametrize("fault", sorted(REFUSED))
def test_the_desk_command_refuses_what_the_build_refuses(tmp_path, fault):
    path = tmp_path / "model.yaml"
    path.write_text(REFUSED[fault])
    run = subprocess.run(
        [sys.executable, "scripts/verify-models.py", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 1, f"a file with {fault} passed:\n{run.stdout}{run.stderr}"
    assert "Traceback" not in run.stderr, f"a file with {fault} raised instead of failing"


@pytest.mark.parametrize("fault", sorted(REFUSED))
def test_the_page_refuses_what_the_desk_refuses(fault):
    report = json.loads(check(REFUSED[fault], root=str(ROOT)))
    assert report["problems"], f"the checker passed a file with {fault}"
    assert not any("/tmp" in problem for problem in report["problems"]), (
        "the checker names a temporary file the reader never made"
    )


def test_the_page_and_the_desk_say_the_same_about_one_file(tmp_path):
    path = tmp_path / "model.yaml"
    path.write_text(starter())
    verify = _verify_models()
    model, _ = verify.check_file(path)
    report = json.loads(check(starter(), root=str(ROOT)))
    assert report["says"] == verify.what_it_says(model)
    assert [n["name"] for n in report["nodes"]] == list(model.order)


def test_the_assembled_page_carries_everything_it_runs():
    """One file, like the viewers: no placeholder left, and nothing fetched but the runtime.

    The old page loaded its YAML parser from a host the offline worker does not keep, so the
    installed book's checker failed with no network. This one needs only the runtime, which the
    worker keeps once fetched.
    """
    spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts/build-site.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    page = module.checker_page()
    for placeholder in ("__CSS__", "__FRAME__", "__BOOT__", "__TOOLKIT__"):
        assert placeholder not in page, f"the checker page still holds {placeholder}"
    assert "<script src=" not in page, "the checker page loads a script from elsewhere"
    assert "shareToolkit(" in page and "scripts/verify-models.py" in page
