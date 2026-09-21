"""The problems are checkable in the page, and what the page ships is enough to check them.

Under a chapter's problems the page shows the stubs file's pieces, editable, and a Check that
runs the chapter's own test file under Pyodide over exactly the files
``sizing.playground.toolkit.problem_files`` lists. Nothing here starts a browser. A subprocess
with the same files laid out the same way, calling the same ``grade``, is the same run: the
chapter's tests have to be *answerable* there, which means they fail the way an unsolved problem
fails, by raising ``NotImplementedError`` from the stub, and never for want of a file.

One process per chapter, so a missing file names its chapter. Slow for a unit test, and worth
it: the alternative is a reader pressing Check and being told the test could not import.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from bench.stamp import ROOT
from sizing.playground.toolkit import (
    problem_chapters,
    problem_files,
    problem_pieces,
    sources,
)

#: What a test says when a file the page did not ship is missing. Any of these under a problem
#: in the page is a defect of the shipping, not of the reader's answer.
UNSHIPPED = ("ModuleNotFoundError", "ImportError", "FileNotFoundError", "No such file")


def lay_out(slug: str, root: Path) -> None:
    """The chapter's files and the toolkit's modules, where the page's boot writes them."""
    for path, text in problem_files(slug).items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    for name, text in sources().items():
        target = root / "sizing" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)


SCRIPT = """
import json, sys
sys.path.insert(0, sys.argv[1])
from sizing.playground.driver import grade
root, tests = sys.argv[1], sys.argv[2:]
out = []
for test in tests:
    stubs = open(root + "/" + test.rsplit("/", 1)[0] + "/stubs.py").read()
    out.append(json.loads(grade(stubs, test, root)))
json.dump(out, sys.stdout)
"""


@pytest.mark.parametrize("slug", problem_chapters())
def test_what_a_chapter_ships_is_enough_to_run_every_one_of_its_problems(slug, tmp_path):
    lay_out(slug, tmp_path)
    tests = [block["test"] for block in problem_pieces(slug)]
    run = subprocess.run(
        [sys.executable, "-c", SCRIPT, str(tmp_path), *tests],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=600,
    )
    assert run.returncode == 0, run.stderr[-3000:]
    reports = json.loads(run.stdout)
    assert [r["test"] for r in reports] == tests
    for report in reports:
        assert not report["problems"], (
            f"{report['test']} could not be collected over what the page ships:\n"
            + "\n".join(p["message"] for p in report["problems"])
        )
        assert report["tests"], f"{report['test']} collected no tests"
        for entry in report["tests"]:
            for word in UNSHIPPED:
                assert word not in entry["message"], (
                    f"{report['test']}::{entry['name']} wants something the page does not ship:\n"
                    f"{entry['message']}"
                )
            if not entry["problem"]:
                # Scaffolding: what CI runs natively has to pass in the browser's layout too.
                assert entry["outcome"] == "passed", (
                    f"{report['test']}::{entry['name']} is scaffolding and does not pass over "
                    f"what the page ships:\n{entry['message']}"
                )


def test_every_problem_test_grades_a_piece_of_the_stubs_file_or_a_file():
    """A test with no piece and no file would be shown as a Check with nothing to edit above it."""
    for slug in problem_chapters():
        for block in problem_pieces(slug):
            assert block["pieces"] or block["files"], (
                f"{block['test']} imports nothing from {block['stubs']} and names no EDITABLE file"
            )
            for entry in block["files"]:
                path = ROOT / entry["path"]
                assert path.is_file() and entry["path"].startswith(f"tests/{slug}/"), entry["path"]
                assert entry["text"] == path.read_text(), (
                    f"{entry['path']}: the page's copy differs"
                )
            whole = (ROOT / block["stubs"]).read_text()
            for piece in block["pieces"]:
                text = whole[piece["start"] : piece["end"]]
                assert text.startswith(("def ", "async def ", "class ", "@")), (
                    f"{block['test']}: the piece for {piece['name']} does not start at its "
                    f"definition: {text[:40]!r}"
                )
                assert piece["name"] in text.split("\n", 1)[0] or text.startswith("@")
                assert not text.endswith("\n")


def test_a_chapter_ships_its_own_tests_and_nothing_compiled():
    """The page writes the repository's test package for the chapter, as it is, and no more."""
    for slug in problem_chapters():
        files = problem_files(slug)
        assert "tests/__init__.py" in files
        assert f"tests/{slug}/__init__.py" in files
        assert f"tests/{slug}/stubs.py" in files
        assert not [name for name in files if "__pycache__" in name or name.endswith(".pyc")]
        assert not [
            name
            for name in files
            if name.startswith("tests/") and f"/{slug}/" not in name and name != "tests/__init__.py"
        ], f"{slug} ships another chapter's tests"
        for name, text in files.items():
            assert (ROOT / name).read_text() == text, f"{slug}: {name} is not the repository's"


def test_a_chapter_that_stamps_ships_what_the_stamp_hashes():
    """A reader's ``build_result`` hashes ``bench.stamp.CORE_SOURCES``. A page that ships stamp.py
    without them fails every correct answer with a missing file, and the unsolved stub never gets
    far enough for the check above to notice."""
    from bench.stamp import CORE_SOURCES

    for slug in problem_chapters():
        shipped = problem_files(slug)
        if "bench/stamp.py" in shipped:
            missing = set(CORE_SOURCES) - set(shipped)
            assert not missing, f"{slug} ships bench/stamp.py without {sorted(missing)}"


def test_the_shipped_files_leave_the_work_to_the_reader():
    """The files a reader edits whole ship with the work left in them. Checked here rather than in
    the problem's own test file, which the page runs over the reader's copy."""
    import yaml

    ((name, ceiling),) = yaml.safe_load(
        (ROOT / "tests/headroom_and_failure_domains/problem_3_ceiling.yaml").read_text()
    ).items()
    assert name == "connections_per_host" and ceiling["kind"] == "ceiling"
    assert ceiling["of"] and ceiling["limit"]
    assert all(ceiling.get(field) in (None, "") for field in ("unit", "headroom", "because"))

    entries = yaml.safe_load(
        (ROOT / "tests/correlation_and_convergence/problem_2_correlation.yaml").read_text()
    )
    entry = next(
        e for e in entries if {e.get("a"), e.get("b")} == {"host_price", "network_price_per_host"}
    )
    assert entry.get("rho") in (None, "") and not str(entry.get("because") or "").strip()

    from sizing.dsl import load_model

    shipped = load_model(ROOT / "tests/the_missing_node/fixtures/model.yaml")
    copy = load_model(ROOT / "tests/the_missing_node/fixtures/repaired.yaml")
    assert set(copy.nodes) == set(shipped.nodes), "the copy the reader repairs is already repaired"
