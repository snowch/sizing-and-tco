"""The scripts, exercised the way CI and a workflow actually invoke them.

One of these exists because the same defect was fixed in three separate files before anybody
wrote it down, and the third time it took the Pages deploy out: a script handed a *relative*
``--out`` on the command line tried to print the resulting path relative to the repository root,
and ``Path.relative_to`` raises when one path is relative and the other is absolute.

Printing a path is never important enough to fail a build. These check that it cannot.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from bench.stamp import ROOT, shown

#: Scripts that take an output directory and are given a relative one by a workflow, and whether
#: each one can do its job in a checkout that has not been built yet. ``build-pdf.py`` assembles
#: what MyST parsed, so in a fresh clone it has nothing to assemble and says so — which is the
#: state CI is in when it runs the tests, because the book build comes after them.
TAKES_AN_OUT = [
    ("scripts/build-viewers.py", "--out", True),
    ("scripts/build-pdf.py", "--out", False),
]


@pytest.mark.parametrize(
    "path",
    [
        "bench/results",
        "_build/html/models/x.html",
        "./chapters/monte_carlo.md",
        "/tmp/somewhere/else",
        "../outside-the-repo",
        "",
    ],
)
def test_shown_never_raises(path):
    """Whatever the shape, a path can be printed."""
    assert isinstance(shown(path), str)


def test_shown_strips_the_root_when_it_can():
    assert shown(ROOT / "bench" / "results") == "bench/results"
    assert shown("bench/results") == "bench/results"


def test_shown_leaves_a_path_outside_the_repository_alone():
    assert shown("/tmp/elsewhere").startswith("/tmp")


@pytest.mark.parametrize(
    ("script", "flag", "self_sufficient"), TAKES_AN_OUT, ids=lambda v: Path(str(v)).name
)
def test_a_relative_out_does_not_blow_up(script, flag, self_sufficient):
    """Exactly what deploy.yml does: a repository-relative output directory.

    Run from the repository root with a relative path, because that is the invocation that
    failed. A script that only works with absolute paths works until somebody writes a workflow.

    A script that refuses because its inputs are not there has not failed this check — it has
    passed it, out loud. What fails it is a traceback, which is what printing a path used to
    produce.
    """
    relative = f"_build/test-out/{Path(script).stem}"
    extra = ["--no-myst", "--html-only"] if "pdf" in script else []
    completed = subprocess.run(
        [sys.executable, script, *extra, flag, relative + ("/book.pdf" if "pdf" in script else "")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert "relative_to" not in completed.stderr, (
        f"{script} cannot print a path it was given:\n{completed.stderr[-600:]}"
    )
    assert "Traceback" not in completed.stderr, (
        f"{script} raised where it should have reported:\n{completed.stderr[-600:]}"
    )
    if self_sufficient:
        assert completed.returncode == 0, completed.stderr[-600:]


def test_verify_setup_reports_rather_than_failing_on_a_missing_optional():
    """It is a report. A machine without Chromium is not a broken checkout."""
    completed = subprocess.run(
        [sys.executable, "scripts/verify-setup.py"], cwd=ROOT, capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "targets" in completed.stdout


def test_every_script_is_executable_and_parses():
    """A script with a syntax error or no shebang is one CI finds at the worst moment."""
    for script in sorted((ROOT / "scripts").glob("*.py")):
        source = script.read_text()
        assert source.startswith("#!/usr/bin/env python3"), f"{script.name} has no shebang"
        compile(source, str(script), "exec")
