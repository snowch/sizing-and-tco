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
import math
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


# -- resampling in the browser --------------------------------------------------------------
#
# The viewer's Run button calls ``sizing.playground.driver.resample`` under Pyodide: the real
# sampler, with the inputs a reader has moved held at their values. Two things make that honest,
# and both are checked here rather than trusted. With nothing held it must give back exactly
# what the build stamped -- same code, same seed -- because that is what the page checks in front
# of the reader before it shows a resampled interval. And holding an input must take it out of
# the draw rather than fail, including an input a correlation names, which is what happened the
# first time anybody pinned the growth rate.


def _texts(result_name: str) -> tuple[str, str]:
    produced = load_result(result_name)["produced_by"]
    model_path = ROOT / produced["model_file"]
    scenario_path = model_path.parent / "scenarios" / f"{produced['scenario']}.yaml"
    return model_path.read_text(), scenario_path.read_text()


@pytest.mark.parametrize("result_name", model_results())
def test_a_resample_with_nothing_held_reproduces_the_stamp(result_name):
    from sizing.playground.driver import resample

    stamped = load_result(result_name)["summary"]
    fresh = json.loads(resample(*_texts(result_name)))

    # To a part in a billion, not to the bit: the same seed gives the same draws on every
    # machine, but a mean or a percentile over a hundred thousand of them is a reduction, and
    # two CPUs sum in different orders. CI found a one-ulp difference in a standard deviation
    # on its first run. The browser's own check uses the same tolerance.
    def close(a, b):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)

    for name, node in stamped["nodes"].items():
        got = fresh["nodes"][name]
        if "point" in node:
            assert close(got["point"], node["point"]), f"{name}: point differs"
        if "summary" in node:
            for key, want in node["summary"].items():
                assert close(got["summary"][key], want), (
                    f"{name}.{key}: the resampled interval is not the stamped one ({got['summary'][key]} "
                    f"vs {want}). Same file, same seed, same sampler -- if these differ beyond "
                    "rounding the page cannot claim to be running the build."
                )


def test_holding_an_input_takes_it_out_of_the_draw():
    from sizing.playground.driver import resample

    model, scenario = _texts("storage_cluster-reference")
    # annual_growth is named in a declared correlation; drive_price is one side of a pair.
    for name, value in (("annual_growth", 1.6), ("drive_price", 10.0)):
        fresh = json.loads(resample(model, scenario, {name: value}))
        held = fresh["nodes"][name]
        assert held["point"] == value
        assert "summary" not in held, f"{name} was held, so it has no spread to summarise"
        assert fresh["scenario"]["overrides"][name] == value
        assert "summary" in fresh["nodes"]["tco"], "the rest of the model still samples"


def test_the_page_carries_every_stamp_a_measured_constant_reads():
    from sizing.dsl import Measured, load_model
    from sizing.playground.toolkit import results_for

    for result_name in model_results():
        produced = load_result(result_name)["produced_by"]
        model = load_model(ROOT / produced["model_file"])
        carried = results_for(model)
        for node in model.nodes.values():
            if isinstance(node, Measured) and node.is_measured:
                assert f"{node.result}.json" in carried, (
                    f"{result_name}: {node.name} reads {node.result} and the page does not carry it, "
                    "so the model could not load in a browser"
                )
