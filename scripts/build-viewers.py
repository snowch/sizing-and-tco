#!/usr/bin/env python3
"""Assemble one self-contained interactive page per model and scenario.

    python3 scripts/build-viewers.py                 # into _build/viewers/
    python3 scripts/build-viewers.py --out DIR       # somewhere else

Everything is inlined — the payload, the evaluator, the app, the stylesheet — so each page is one
file that opens from a local disk, from GitHub Pages, or from anywhere else, with no server, no
bundler and no network. A book outlives its toolchain; a single HTML file outlives both.

The pages are built from the **stamped model results**, not by re-running the models. That is
deliberate: the figures in the chapters and the numbers on these pages come from the same file, so
the book and the browser cannot disagree about what a model says.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.stamp import RESULTS_DIR, load_result, shown  # noqa: E402
from bench.tables import REPOSITORY  # noqa: E402
from bench.theme import FRAME, both_ways  # noqa: E402
from sizing.dsl import load_model  # noqa: E402
from sizing.playground.toolkit import BOOT, PYODIDE, results_for, sources, wheels  # noqa: E402

VIEWER = ROOT / "sizing" / "viewer"
DEFAULT_OUT = ROOT / "_build" / "viewers"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — {scenario}</title>
<style>{css}</style>
{theme}
</head>
<body>
<header>
  <h1>{title} <span class="kind">{classification} model</span></h1>
  <p>{scenario_title} · {samples} samples · seed {seed} · generated {generated} ·
  <a href="{stamp}">the stamped result</a></p>
</header>
<main>
  <section id="controls">
    <h2><button id="toggle-controls" class="toggle-panel" aria-expanded="false">▶</button> Inputs</h2>
    <div id="controls-content">
      <p class="note">Every slider comes from a range the model file declares. Moving one recomputes
      the whole graph immediately.</p>
      <!-- The control and its outcome sit above the sliders: on a model with twenty inputs the
           reader presses a button at the top and reads the answer where they pressed it. -->
      <div id="banner" class="banner" style="display:none"></div>
      <div id="stale" class="stale" style="display:none">
        These are point values for the settings you have chosen. The distributions and the
        probabilities below still belong to the scenario.
        <button id="resample" class="primary">Resample with these fixed</button>
        <span class="note">Runs the book's own sampler in this tab — the same code and seed that
        stamped the intervals — with the inputs you have moved held at their values. The first
        press fetches a Python runtime, about ten megabytes, once; nothing is sent anywhere.</span>
      </div>
      <button id="reset">Back to the scenario</button>
      <div id="sliders"></div>
      <h2>Outputs</h2>
      <div id="outputs"></div>
    </div>
  </section>
  <section id="canvas">
    <p class="note narrow-note" id="narrow-note"></p>
    <div class="legend">
      <span><i style="background:var(--input);border:1px solid var(--input-edge)"></i>input</span>
      <span><i class="decision" style="background:var(--input);border:1px solid var(--input-edge)"></i>you decide</span>
      <span><i style="background:var(--derived);border:1px solid var(--derived-edge)"></i>derived</span>
      <span><i style="background:var(--measured);border:1px solid var(--measured-edge)"></i>measured</span>
      <span><i style="background:var(--ceiling);border:1px solid var(--ceiling-edge)"></i>ceiling</span>
      <span><i style="background:var(--bg);border:1px dashed var(--ceiling-edge)"></i>not yet measured</span>
    </div>
    <p class="note" id="focus-note"></p>
    <svg id="graph" xmlns="http://www.w3.org/2000/svg"></svg>
  </section>
  <section id="detail">
    <h2><button id="toggle-detail" class="toggle-panel" aria-expanded="false">▶</button> Details</h2>
    <div id="detail-content">
      <div id="detail-body"></div>
    </div>
  </section>
</main>
<script>window.__MODEL__ = {payload};</script>
<script>window.__TOOLKIT__ = {toolkit};</script>
<script type="module">
{boot}
{evaluate_js}
{app_js}
</script>
</body>
</html>
"""


def build(result_name: str, out_dir: Path) -> Path:
    payload = load_result(result_name)["summary"]
    evaluate_js = (VIEWER / "evaluate.js").read_text()
    app_js = (VIEWER / "app.js").read_text()

    # Both files are ES modules that would normally import each other. Inlined into one script
    # block there is nothing to import from, so the import line comes out and the export keywords
    # with it — a dozen characters of surgery that saves shipping a bundler with a book.
    evaluate_js = evaluate_js.replace("export function", "function")
    app_js = app_js.replace('import { evaluatePoint, ceilingState } from "./evaluate.js";', "")

    # What a resample needs: the file the stamp was made from, its scenario, and the stamped
    # results its measured constants read. All read at build time, when verify-numbers has
    # already established that the file and the stamp agree.
    produced = load_result(result_name)["produced_by"]
    model_path = ROOT / produced["model_file"]
    scenario_path = model_path.parent / "scenarios" / f"{produced['scenario']}.yaml"
    toolkit = {
        "pyodide": PYODIDE,
        "modules": sources(),
        "results": results_for(load_model(model_path)),
        "model": model_path.read_text(),
        "scenario": scenario_path.read_text(),
        "wheels": wheels(),
    }

    page = PAGE.format(
        title=html.escape(payload["title"]),
        toolkit=json.dumps(toolkit),
        boot=BOOT,
        scenario=html.escape(payload["scenario"]["name"]),
        scenario_title=html.escape(payload["scenario"]["title"]),
        classification=payload["classification"],
        samples=f"{payload['scenario']['samples']:,}",
        seed=payload["scenario"]["seed"],
        generated=payload["generated_at"][:10],
        # The chapters send a reader here rather than to the JSON, because a page with sliders is
        # checkable and two hundred kilobytes of JSON is not. The file is still the evidence, so
        # it is one click from here for anybody who wants it.
        stamp=f"{REPOSITORY}/bench/results/{result_name}.json",
        css=both_ways((VIEWER / "style.css").read_text()),
        theme=FRAME,
        payload=json.dumps(payload, separators=(",", ":")),
        evaluate_js=evaluate_js,
        app_js=app_js,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{result_name}.html"
    path.write_text(page)
    return path


def model_results() -> list[str]:
    return sorted(
        path.stem
        for path in RESULTS_DIR.glob("*.json")
        if json.loads(path.read_text()).get("kind") == "model"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    # Relative to the repository, not to wherever the shell happens to be. A workflow passing
    # `--out _build/html/models` means the one inside the checkout.
    out = args.out if args.out.is_absolute() else ROOT / args.out

    names = model_results()
    if not names:
        print("build-viewers: no model results — run `python3 -m bench.run_models` first")
        return 1
    for name in names:
        path = build(name, out)
        print(f"  wrote {shown(path)} ({path.stat().st_size / 1024:.0f} KB)")
    print(f"\nbuild-viewers: OK ({len(names)} page(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
