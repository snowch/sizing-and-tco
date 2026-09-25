"""ch01's draw-one-future page shows the model the book stamped, and nothing else.

The page is a third evaluator's worth of risk: it carries a trimmed copy of one model's graph and
works it out in the browser, a future at a time, so that a reader can watch a range being made
instead of being told one exists. Three things have to hold, and none of them holds by itself.

**It draws the right inputs.** Every uncertain input the answer depends on, and only those. An
input that cannot reach the answer would jump about under a reader's eye and change nothing, on a
page whose whole subject is what moves this number.

**It gets the same answers the build would.** Same graph, same unit conversions, same arithmetic
— checked against Python over a grid of draws rather than assumed from the fact that both read the
same export.

**It is the page the chapter points at.** A `/futures/...` URL that nothing builds is a hole in
the chapter, and a page nothing embeds is dead weight in the deploy.

The sampler underneath is checked separately, in ``tests/test_sample.py``. The parts of this that
need a JavaScript engine are marked ``node`` and skipped without one, as the viewer's are.
"""

from __future__ import annotations

import json
import math
import random
import re
import shutil
import subprocess
import textwrap
from dataclasses import replace
from importlib import util
from pathlib import Path

import pytest

from bench.stamp import ROOT, load_result
from sizing import mc

VIEWER = ROOT / "sizing" / "viewer"
CHAPTERS = ROOT / "chapters"


def builder():
    """``scripts/build-futures.py``, imported so the tests can ask what it builds."""
    spec = util.spec_from_file_location("build_futures", ROOT / "scripts" / "build-futures.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payload_for(slug: str) -> dict:
    """The page's own payload, built the way the deploy builds it, without writing a page."""
    module = builder()
    spec = module.PAGES[slug]
    result = load_result(spec["result"])["summary"]
    keep = module.ancestors(result, spec["answer"])
    trimmed = module.trim(result, keep)
    trimmed["spreads"] = {
        name: result["nodes"][name]["distribution"]
        for name in result["order"]
        if name in keep
        and result["nodes"][name]["kind"] == "input"
        and result["nodes"][name].get("distribution")
    }
    trimmed["answer"] = spec["answer"]
    return trimmed


SLUGS = sorted(builder().PAGES)


@pytest.mark.parametrize("slug", SLUGS)
def test_the_page_draws_exactly_what_the_answer_depends_on(slug):
    """Every uncertain input in the chain is shown, and nothing outside the chain is carried.

    The builder asserts the first half so that a model change fails the build rather than the
    deploy. This is the half a build cannot check: that the page is not quietly carrying a node
    the answer never reads, which is how a payload grows a megabyte one release at a time.
    """
    module = builder()
    page = payload_for(slug)
    spec = module.PAGES[slug]
    assert set(spec["order"]) == set(page["spreads"]), (
        f"{slug}: the page lists {sorted(spec['order'])} and the answer draws "
        f"{sorted(page['spreads'])}"
    )
    result = load_result(spec["result"])["summary"]
    reach = module.ancestors(result, spec["answer"])
    assert set(page["nodes"]) == reach, "the page carries a node the answer cannot reach"


@pytest.mark.parametrize("slug", SLUGS)
def test_a_bar_of_the_pile_covers_a_whole_number_of_the_answer(slug):
    """The answer is a count, so bins of eight beside bins of nine draw a sawtooth.

    ``hosts_recommended`` comes out of a ``ceil``, so it takes whole values only. Divide its range
    into forty-six equal bins and some catch eight of those values and some nine — a comb that
    looks like structure in the model and is an artefact of the axis. The band is rounded up to a
    whole number of bins so that every bar covers the same count of possible answers.
    """
    module = builder()
    spec = module.PAGES[slug]
    payload = load_result(spec["result"])["summary"]
    summary = payload["nodes"][spec["answer"]]["summary"]
    step = max(1, round(summary["p95"] * spec["reach"] / spec["bars"]))
    bins = math.ceil(summary["p95"] * spec["reach"] / step)
    top = step * bins
    assert top % bins == 0, "a bar covers a fraction of an answer"
    assert top > summary["p95"], "the pile's right-hand edge is inside the stamped 95th percentile"
    assert abs(bins - spec["bars"]) <= spec["bars"] // 4, (
        f"{slug}: rounding the bin width left {bins} bars where the page asked for {spec['bars']}"
    )


def test_every_futures_page_is_embedded_by_a_chapter():
    """A `/futures/...` URL nothing builds is a hole in a page; a page nothing embeds is ballast.

    Checked both ways because the two lists are maintained in different files and drift
    silently.
    """
    embedded = {
        match
        for path in CHAPTERS.glob("*.md")
        for match in re.findall(r"\{iframe\}\s+/futures/([a-z0-9-]+)\.html", path.read_text())
    }
    assert set(builder().PAGES) == embedded, (
        f"the build ships {sorted(builder().PAGES)} and the chapters embed {sorted(embedded)}"
    )


# -- the browser and the build ----------------------------------------------------------------

HARNESS = textwrap.dedent(
    """
    import { evaluatePoint } from "%(viewer)s/evaluate.js";
    import { at } from "%(viewer)s/sample.js";
    import fs from "fs";
    const { payload, draws } = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
    const out = [];
    for (const draw of draws) {
      const overrides = {};
      for (const [name, u] of Object.entries(draw)) overrides[name] = at(payload.spreads[name], u);
      const { values } = evaluatePoint(payload, overrides);
      // `undefined` would vanish from the JSON; null arrives and fails where it can be read.
      out.push({ overrides, answer: values[payload.answer] ?? null });
    }
    console.log(JSON.stringify(out));
    """
)


def percentile_grid(names: list[str]) -> list[dict[str, float]]:
    """Draws to check at: both edges, the middle, and a spread of mixed ones.

    Deterministic, because a test that fails one run in twenty is a test people learn to re-run.
    The corners matter on this model in particular: the answer is the largest of three chains, and
    which chain wins changes inside the range.
    """
    draws = [dict.fromkeys(names, edge) for edge in (0.001, 0.25, 0.5, 0.75, 0.999)]
    rng = random.Random(20260922)
    for _ in range(40):
        draws.append({name: rng.uniform(0.001, 0.999) for name in names})
    return draws


@pytest.mark.node
@pytest.mark.parametrize("slug", SLUGS)
def test_the_browser_and_the_build_agree_about_every_future(slug):
    """What the reader's press computes is what this model computes.

    ``tests/test_viewer.py`` makes this promise for the full export. It does not cover this page,
    which carries a *trimmed* graph: a node dropped from the wrong end of it, or a unit conversion
    left behind with it, would give a reader a pile of plausible and wrong answers with nothing on
    the page to give it away.
    """
    from sizing.dsl import load_model, scenarios_for
    from sizing.evaluate import conversion_factors, point

    if shutil.which("node") is None:  # pragma: no cover - the marker skips this
        pytest.skip("no node")

    module = builder()
    spec = module.PAGES[slug]
    page = payload_for(slug)
    produced = load_result(spec["result"])["produced_by"]
    model = load_model(ROOT / produced["model_file"])
    scenario = next(s for s in scenarios_for(model) if s.name == produced["scenario"])
    factors = conversion_factors(model)

    directory = Path(__import__("tempfile").mkdtemp())
    script = directory / "check.mjs"
    script.write_text(HARNESS % {"viewer": VIEWER.as_posix()})
    cases = directory / "cases.json"
    draws = percentile_grid(sorted(page["spreads"]))
    cases.write_text(json.dumps({"payload": page, "draws": draws}))
    run = subprocess.run(
        ["node", str(script), str(cases)], capture_output=True, text=True, timeout=120
    )
    assert run.returncode == 0, run.stderr[-2000:]
    got = json.loads(run.stdout)

    assert len(got) == len(draws)
    for drawn in got:
        assert drawn["answer"] is not None, (
            f"{slug}: the page computed nothing for {sorted(drawn['overrides'])} — a node the "
            "answer reads is missing from the trimmed graph"
        )
        probed = replace(scenario, overrides={**scenario.overrides, **drawn["overrides"]})
        want = point(model, probed, factors)[spec["answer"]]
        assert math.isclose(drawn["answer"], want, rel_tol=1e-9, abs_tol=1e-12), (
            f"{slug}: the page says {drawn['answer']} and the build says {want} for "
            f"{ {k: round(v, 6) for k, v in drawn['overrides'].items()} }"
        )


@pytest.mark.node
@pytest.mark.parametrize("slug", SLUGS)
def test_the_page_draws_from_the_spreads_the_model_declares(slug):
    """Every shape on the page is one the sampler implements and the model file wrote down."""
    page = payload_for(slug)
    for name, distribution in page["spreads"].items():
        shape, _ = mc.one_shape(distribution)
        assert f"{shape}:" in (VIEWER / "sample.js").read_text(), (
            f"{name} is a {shape} and the browser has no {shape}"
        )
