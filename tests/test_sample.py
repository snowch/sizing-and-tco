"""The browser and the sampler agree about what every spread says.

ch01's widget draws a future in the reader's browser, which means a second implementation of the
percentile functions in :mod:`sizing.mc` and of the inverse normal CDF in :mod:`sizing.normal`.
A second implementation of anything is a liability unless something checks it, and this is that
something. It is the same arrangement as ``tests/test_viewer.py``, one layer down: that one
checks the evaluator, this one checks the sampler underneath it.

**What is checked.** Every percentile function, over the range and into both tails, against the
Python original. And every distribution declared by either reference model, so a shape nobody
thought to write a case for is still covered by the model that uses it.

**What is not, and why.** The random stream. numpy's PCG64 cannot be had in plain JavaScript
without porting PCG64 as well, so a seeded draw in the browser and a seeded draw in ``mc.py`` are
different draws from the same distributions. Nothing in the book rests on them being the same
draw: a stamped result is always computed by Python, and the widget says in as many words that
it is not rebuilding the figure above it. Pretending otherwise would be the kind of claim this
repository refuses everywhere else.

Marked ``node`` and skipped without a JavaScript engine, as the viewer test is.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import textwrap

import pytest

from bench.stamp import ROOT
from sizing import mc
from sizing.dsl import Input, discover
from sizing.normal import normal_ppf

pytestmark = pytest.mark.node

VIEWER = ROOT / "sizing" / "viewer"

HARNESS = textwrap.dedent(
    """
    import { at, normalPpf, stream } from "%(viewer)s/sample.js";
    import fs from "fs";
    const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
    const out = { normal: [], shapes: [], stream: null };
    for (const u of cases.percentiles) out.normal.push(normalPpf(u));
    for (const { spec, u } of cases.shapes) out.shapes.push(at(spec, u));
    // Every draw is a percentile strictly inside (0, 1), or `normalPpf` would throw on it.
    const next = stream(20260916);
    let lowest = 1, highest = 0;
    for (let i = 0; i < 20000; i++) {
      const u = next();
      lowest = Math.min(lowest, u);
      highest = Math.max(highest, u);
    }
    out.stream = { lowest, highest };
    console.log(JSON.stringify(out));
    """
)

#: Across the range and well into both tails, where a rational approximation is worst and where
#: the percentiles a sizing model actually reports tend to live.
PERCENTILES = [
    1e-9,
    1e-6,
    1e-4,
    0.001,
    0.005,
    0.01,
    0.02424,
    0.02425,
    0.02426,
    0.05,
    0.1,
    0.25,
    0.4,
    0.5,
    0.6,
    0.75,
    0.9,
    0.95,
    0.97574,
    0.97575,
    0.97576,
    0.99,
    0.995,
    0.999,
    1 - 1e-4,
    1 - 1e-6,
    1 - 1e-9,
]


def declared_distributions() -> list[dict]:
    """Every distribution either reference model declares, so no shape goes unchecked."""
    out = []
    for model in discover():
        for name in sorted(model.nodes):
            node = model.nodes[name]
            if isinstance(node, Input) and node.distribution:
                out.append(node.distribution)
    return out


def run_node(cases: dict, tmp_path) -> dict:
    node = shutil.which("node")
    if not node:  # pragma: no cover - the marker skips this, belt and braces
        pytest.skip("no node")
    script = tmp_path / "check.mjs"
    script.write_text(HARNESS % {"viewer": VIEWER.as_posix()})
    payload = tmp_path / "cases.json"
    payload.write_text(json.dumps(cases))
    run = subprocess.run(
        [node, str(script), str(payload)], capture_output=True, text=True, timeout=120
    )
    assert run.returncode == 0, run.stderr[-2000:]
    return json.loads(run.stdout)


def test_the_browser_and_the_sampler_agree(tmp_path):
    """Both implementations put the same value at the same percentile.

    Nine figures, which is what ``tests/test_mc.py`` already holds the Python one to against the
    standard library. A browser that agrees about the middle and drifts in the tail is a browser
    that draws the wrong extreme answers, on the pile where a reader is least able to check it.
    """
    shapes = []
    for spec in declared_distributions():
        for u in (0.02, 0.2, 0.5, 0.8, 0.98):
            shapes.append({"spec": spec, "u": u})
    assert shapes, "the reference models declare distributions to check"

    got = run_node({"percentiles": PERCENTILES, "shapes": shapes}, tmp_path)

    for u, mine in zip(PERCENTILES, got["normal"], strict=True):
        want = float(normal_ppf(u))
        assert math.isclose(mine, want, rel_tol=1e-9, abs_tol=1e-12), (
            f"normalPpf({u}) is {mine} in the browser and {want} in Python"
        )

    for case, mine in zip(shapes, got["shapes"], strict=True):
        name, parameters = mc.one_shape(case["spec"])
        want = float(mc.SHAPES[name](case["u"], **parameters))
        assert math.isclose(mine, want, rel_tol=1e-9, abs_tol=1e-12), (
            f"{name} at {case['u']} is {mine} in the browser and {want} in Python"
        )


def test_every_shape_the_models_use_is_covered(tmp_path):
    """A shape a model declares and this test never draws is a shape nobody checked."""
    named = {mc.one_shape(spec)[0] for spec in declared_distributions()}
    assert named, "the models declare shapes"
    missing = named - set(mc.SHAPES)
    assert not missing, f"a model declares a shape the sampler does not implement: {missing}"
    ported = (VIEWER / "sample.js").read_text()
    for shape in named:
        assert f"{shape}:" in ported, f"the browser has no {shape}"


def test_a_drawn_percentile_is_never_an_endpoint(tmp_path):
    """Zero and one are the two values the inverse normal CDF refuses.

    Python raises on them deliberately: an endpoint means a percentile was computed rather than
    drawn, and an infinity in a sum turns a model's output into nan several steps later. The
    browser's stream has to make the same promise, because the widget calls it in a loop with
    nothing between it and the tails.
    """
    got = run_node({"percentiles": [0.5], "shapes": []}, tmp_path)
    assert got["stream"]["lowest"] > 0.0, "a draw of zero would throw in the normal"
    assert got["stream"]["highest"] < 1.0, "a draw of one would throw in the normal"
