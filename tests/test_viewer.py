"""The browser and the build agree about what every model says.

The published page carries a second implementation of the model evaluator, in JavaScript, so that
moving a slider recomputes the graph with no server. A second implementation of anything is a
liability unless something checks it, and this is that something.

Every exported model carries ``viewer_expectations``: a set of slider positions, and the value
Python computed for **every node** at each of them. This test runs the JavaScript over exactly
those and fails on any disagreement. Not just the outputs — a browser that agrees about the total
and disagrees about an intermediate node is still showing a wrong number, on the panel where it is
least likely to be noticed.

Marked ``node`` and skipped where no node binary exists, because the check needs a JavaScript
engine and a contributor without one should not see a red suite they cannot act on. CI has one.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap

import pytest

from bench.stamp import RESULTS_DIR, ROOT, load_result

pytestmark = pytest.mark.node

HARNESS = textwrap.dedent(
    """
    import { evaluatePoint } from "%(viewer)s/evaluate.js";
    import fs from "fs";
    const payload = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
    const problems = [];
    let checked = 0;
    for (const probe of payload.viewer_expectations) {
      const { values } = evaluatePoint(payload, probe.overrides);
      for (const [name, want] of Object.entries(probe.values)) {
        checked += 1;
        const got = values[name];
        if (got === undefined || !Number.isFinite(got) ||
            Math.abs(got - want) > 1e-9 * Math.max(1, Math.abs(want))) {
          problems.push(`${name}: python ${want}, javascript ${got}`);
        }
      }
    }
    console.log(JSON.stringify({ checked, problems }));
    """
)


def model_results() -> list[str]:
    return sorted(
        path.stem
        for path in RESULTS_DIR.glob("*.json")
        if json.loads(path.read_text()).get("kind") == "model"
    )


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("no node binary; the browser evaluator cannot be checked here")
    directory = tmp_path_factory.mktemp("viewer")
    script = directory / "check.mjs"
    script.write_text(HARNESS % {"viewer": (ROOT / "sizing" / "viewer").as_uri()})
    return script


@pytest.mark.parametrize("result_name", model_results())
def test_the_browser_agrees_with_the_build(harness, tmp_path, result_name):
    payload = tmp_path / f"{result_name}.json"
    payload.write_text(json.dumps(load_result(result_name)["summary"]))
    completed = subprocess.run(
        ["node", str(harness), str(payload)],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    report = json.loads(completed.stdout.strip().splitlines()[-1])
    assert report["checked"] > 0, "the export carried no expectations to check against"
    assert not report["problems"], (
        f"{result_name}: the page would show different numbers from the build.\n  "
        + "\n  ".join(report["problems"][:10])
    )


@pytest.mark.parametrize("result_name", model_results())
def test_every_export_carries_expectations_for_every_node(result_name):
    payload = load_result(result_name)["summary"]
    probes = payload["viewer_expectations"]
    assert probes, "an export with no expectations leaves the browser evaluator unchecked"
    computable = {name for name in payload["order"] if not payload["nodes"][name].get("blocked_by")}
    for probe in probes:
        missing = computable - set(probe["values"])
        assert not missing, f"no expectation recorded for {sorted(missing)[:5]}"
