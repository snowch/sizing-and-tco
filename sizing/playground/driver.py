"""What the browser calls. The real toolkit, in front of a reader who has just been shown a file.

Three calls. ``check`` is the playground's: load a file, check its units, evaluate its point.
``resample`` is the viewer's: the same sampler that stamped the book's intervals, run again with
the inputs a reader has fixed, so that "suppose you knew growth was 1.6" gets the interval that
is left rather than a point value and a note saying the distributions belong to the scenario.
``grade`` is a problem's: pytest itself, run over the chapter's own test file against the stubs
file as the reader has it, so that the verdict under a problem in the page is the verdict the
same test gives at a desk.

ch02 ends by telling a reader they have a file that runs, and that a rate multiplied by a number
is refused rather than accepted. Until now both were claims: running the file needed a checkout,
a pip install and three make targets, in a chapter whose whole argument is not to take a number
on trust.

Nothing here reimplements anything. It loads the model with ``sizing.dsl.load_model``,
checks it with ``sizing.evaluate.check_units`` and evaluates it with
``sizing.evaluate.point`` — the calls the build makes — so a verdict in the browser is
the build's verdict, not a second opinion about it.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import traceback
from dataclasses import replace
from pathlib import Path


def check(text: str) -> dict:
    """Load a model file as written and report what the build would say about it."""
    from sizing.dsl import load_model
    from sizing.evaluate import check_units, point

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "model.yaml"
        path.write_text(text)
        try:
            model = load_model(path)
        except Exception as error:  # a malformed file is the commonest thing a reader will make
            return {
                "stage": "load",
                "ok": False,
                "problems": [f"{type(error).__name__}: {error}"],
                "detail": traceback.format_exc(limit=1),
            }

    problems, factors = check_units(model)
    if problems:
        return {"stage": "units", "ok": False, "problems": problems}

    # Only once the units are sound: a value computed from a formula that does not typecheck is
    # a number nobody should be shown, which is the whole argument of the chapter this page
    # belongs to.
    try:
        values = point(model, factors=factors)
    except Exception as error:
        return {
            "stage": "evaluate",
            "ok": False,
            "problems": [f"{type(error).__name__}: {error}"],
        }

    nodes = [
        {
            "name": name,
            "kind": node.kind,
            "unit": node.unit,
            "label": node.label,
            "formula": getattr(node, "formula_text", None),
            "value": values.get(name),
        }
        for name, node in model.nodes.items()
    ]
    return {
        "stage": "ok",
        "ok": True,
        "problems": [],
        "nodes": nodes,
        "order": list(model.order),
        "outputs": list(model.outputs),
        "classification": model.classification,
        "factors": {name: value for name, value in factors.items() if value != 1.0},
    }


def resample(model_text: str, scenario_text: str, fixed: dict | None = None) -> str:
    """Sample the model again with some inputs held at a value, and return what the page needs.

    ``fixed`` maps input names to values. A fixed input is a scenario override: the sampler does
    not draw it, so the interval that comes out is the doubt left in everything else -- which is
    ch19's question asked by dragging a slider. With nothing fixed this is exactly the run that
    stamped the result the page was built from, seed and all, and the page checks that it is.

    Returns JSON text rather than a Python object: the payload is a few hundred kilobytes of
    nested floats, and a string crosses into JavaScript in one piece.
    """
    from sizing.dsl import load_model, load_scenario
    from sizing.export import export_payload

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "scenarios").mkdir()
        (root / "model.yaml").write_text(model_text)
        (root / "scenarios" / "scenario.yaml").write_text(scenario_text)
        model = load_model(root / "model.yaml")
        scenario = load_scenario(root / "scenarios" / "scenario.yaml")
        scenario = replace(
            scenario,
            overrides={**scenario.overrides, **{k: float(v) for k, v in (fixed or {}).items()}},
        )
        payload = export_payload(model, scenario)
    return json.dumps(payload)


#: How much of a failure's text a verdict carries. The first lines are the assertion and its
#: message, which is what a reader needs; a numpy array printed after them is not, and the
#: terminal output carries the whole of it anyway.
DETAIL = 4000


class _Verdicts:
    """A pytest plugin that keeps what happened to each test, in the order it happened."""

    def __init__(self) -> None:
        self.tests: dict[str, dict] = {}
        self.problems: list[dict] = []

    def _entry(self, nodeid: str) -> dict:
        name = nodeid.split("::", 1)[1] if "::" in nodeid else nodeid
        return self.tests.setdefault(nodeid, {"name": name, "outcome": "passed", "message": ""})

    def pytest_runtest_logreport(self, report) -> None:
        entry = self._entry(report.nodeid)
        entry["problem"] = "problem" in report.keywords
        if report.when == "call":
            entry["outcome"] = report.outcome
            if report.outcome != "passed":
                entry["message"] = _message(report)
        elif report.failed:
            # Set-up or tear-down: a fixture raised, so the test never ran.
            entry["outcome"] = "error"
            entry["message"] = _message(report)
        elif report.skipped:
            entry["outcome"] = "skipped"
            entry["message"] = _message(report)
        printed = report.capstdout
        if printed:
            entry["output"] = printed

    def pytest_collectreport(self, report) -> None:
        if report.failed:
            # The file could not be imported at all, which is what a syntax error in the stubs
            # looks like: no test ran, and this is the only place it is said.
            self.problems.append({"where": report.nodeid, "message": _message(report)})


def _message(report) -> str:
    """What went wrong, as pytest says it.

    For a test, the exception and its message. For a file that would not import, pytest's own
    report is mostly the frames it went through to find that out; the lines it marks are the
    reader's file, the line, and the error, which is all a reader needs.
    """
    crash = getattr(report.longrepr, "reprcrash", None)
    if crash is not None and crash.message:
        return crash.message[:DETAIL]
    text = str(report.longrepr)
    marked = [line[4:] for line in text.splitlines() if line.startswith("E   ") or line == "E"]
    return ("\n".join(marked) if marked else text)[-DETAIL:]


def grade(stubs: str, test: str, root: str = "/", files: dict[str, str] | str | None = None) -> str:
    """Run one problem's tests against the stubs file as the reader has it, and say what happened.

    ``test`` is the test file's path under ``root``, ``tests/capacity/test_problem_1_raw.py``,
    and the stubs file it grades is the one beside it. ``root`` is where the page laid the
    chapter's files out, so the tests find ``models/web_service/model.yaml`` at the path they
    name. Nothing here re-implements a runner: pytest runs in this process, over the same file
    the reader would run at a desk, with a plugin that keeps each test's outcome and message.

    ``files`` are the files the reader edits whole, path under ``root`` to text, as JSON text or
    a dict; a problem whose artefact is a model fragment or a fixture hands them over here, and
    they are written where the test will read them.

    Returns JSON text, one entry per test, plus the terminal output for a reader who wants all of
    it. Each entry says whether it is the reader's test or the book's own scaffolding, under
    ``problem``, because only the first kind is theirs to pass and the page counts only those.
    A test file that cannot be imported, a syntax error in the stubs being the usual reason, is
    reported under ``problems`` rather than as a test.
    """
    import pytest

    base = Path(root)
    target = base / test
    (target.parent / "stubs.py").write_text(stubs)
    edited = json.loads(files) if isinstance(files, str) else (files or {})
    for path, text in edited.items():
        if ".." in Path(path).parts:
            raise ValueError(f"an edited file stays under the root: {path!r}")
        where = base / path
        where.parent.mkdir(parents=True, exist_ok=True)
        where.write_text(text)
    # A compiled copy of the previous stubs would be read in place of the new ones: the check
    # that guards a .pyc is the source's size and its mtime to the second, and an edit that
    # changes one character between two presses of Check defeats both. So nothing under the
    # tests is ever compiled to disk, and whatever was is removed.
    sys.dont_write_bytecode = True
    shutil.rmtree(target.parent / "__pycache__", ignore_errors=True)
    for name in [m for m in sys.modules if m == "tests" or m.startswith("tests.")]:
        del sys.modules[name]
    # The same run everywhere: no plugin a machine happens to have installed, no cache directory,
    # no fault handler wired to a terminal there is not, and no colour for the same reason.
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.chdir(base)
    verdicts = _Verdicts()
    terminal = io.StringIO()
    with contextlib.redirect_stdout(terminal), contextlib.redirect_stderr(terminal):
        code = pytest.main(
            [
                str(target),
                "-q",
                "--color=no",
                "--tb=short",
                "--capture=sys",
                "-p",
                "no:cacheprovider",
                "-p",
                "no:faulthandler",
                "-o",
                "markers=problem: a chapter problem for the reader to solve",
                f"--rootdir={base}",
            ],
            plugins=[verdicts],
        )
    tests = list(verdicts.tests.values())
    return json.dumps(
        {
            "test": test,
            "exit": int(code),
            "tests": tests,
            "problems": verdicts.problems,
            "output": terminal.getvalue(),
        }
    )
