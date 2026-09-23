#!/usr/bin/env python3
"""The model file from ch02, runnable in a browser.

    python3 scripts/build-playground.py                # into _build/playground/
    python3 scripts/build-playground.py --out DIR

ch02 ends by telling a reader they have a file that runs, and that multiplying a rate by a plain
number is refused here where a spreadsheet would accept it. Both were claims a reader could not
check without a checkout, in a chapter arguing that numbers should not be taken on trust.

This page runs the **real toolkit**, unmodified, under Pyodide: `sizing.dsl.load_model` and
`sizing.evaluate.check_units`, the same two calls `make check` makes. Not a JavaScript
reimplementation — PLAN.md refuses a second answer nobody has verified, and the way to obey that
is to ship the first one.

The page carries fixtures whose verdicts were computed by this build, and re-runs them in the
browser on load. If the browser and the build ever disagree, the page says so at the top, in
front of the reader, rather than quietly teaching something the repository does not do.

Not one of `bench/figures.py`'s figures, and no published number is computed here: a reader is
running *their own* edit of a small file. Invariant 1 is about what the book asserts, and this
page asserts nothing.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.stages import label_of, stages  # noqa: E402
from bench.stamp import shown  # noqa: E402
from bench.theme import FRAME, both_ways  # noqa: E402
from sizing.dsl import load_model  # noqa: E402
from sizing.playground.driver import check  # noqa: E402
from sizing.playground.toolkit import BOOT, PYODIDE, results_for, sources, wheels  # noqa: E402

DEFAULT_OUT = ROOT / "_build" / "playground"


def fixtures(path: Path) -> list[dict]:
    """Models whose verdict this build computed, for the browser to agree with.

    The first is the file the chapter leaves the reader with. The second is the mistake ch02 says
    a spreadsheet accepts, which is the one a reader is most likely to make on purpose, and every
    stage can make it because every stage has a derived node.
    """
    good = path.read_text()
    broken = _break_a_formula(good)
    cases = [
        ("the file as this chapter leaves it", good),
        ("a formula whose units do not work out", broken),
        ("a file that is not valid YAML", "nodes:\n  x: {kind: input, unit: TB\n"),
    ]
    out = []
    for title, text in cases:
        verdict = check(text)
        out.append(
            {
                "title": title,
                "text": text,
                "stage": verdict["stage"],
                "problems": verdict["problems"],
            }
        )
    return out


def _break_a_formula(text: str) -> str:
    """The same file with one derived node given a formula that cannot produce its unit.

    Done by editing the text rather than the parsed document, because what the fixture has to
    exercise is the path a reader takes: they retype a line, and the build refuses.
    """
    document = yaml.safe_load(text)
    for spec in document["nodes"].values():
        if spec.get("kind") == "derived":
            inputs = [n for n, s in document["nodes"].items() if s.get("kind") == "input"]
            replacement = f"formula: {inputs[0]} * {inputs[-1]}" if len(inputs) > 1 else None
            if replacement is None:
                continue
            original = f"formula: {spec['formula']}"
            if original in text and replacement != original:
                broken = text.replace(original, replacement, 1)
                if check(broken)["stage"] == "units":
                    return broken
    raise AssertionError("no single-line edit to this stage produces a unit error")


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &mdash; Sizing and TCO</title>
<style>{css}</style>
{theme}
</head>
<body>
<header>
  <h1>Run the model &mdash; {title}</h1>
  <p>The model file as this chapter leaves it, and the toolkit that reads it.</p>
</header>

<div id="agreement" class="pending">Press <b>Run</b> to start. The first press fetches a
Python runtime of about ten megabytes and takes a few seconds; after that a check takes
milliseconds. Nothing is sent anywhere &mdash; it all runs in this tab.</div>

<main>
  <section>
    <div class="bar">
      <button id="run">Run</button>
      <button id="reset">Back to the file</button>
      <span id="timing"></span>
    </div>
    <textarea id="source" spellcheck="false">{model}</textarea>
  </section>
  <section>
    <div id="verdict" class="verdict"></div>
    <div id="detail"></div>
  </section>
</main>

<footer>
  <p>This runs <code>sizing.dsl.load_model</code>, <code>sizing.evaluate.check_units</code> and
  <code>sizing.evaluate.point</code> &mdash; the calls <code>make check</code> makes, not a second
  implementation of them. The fixtures above were checked by the build; the page re-runs them here
  so that a browser which disagrees says so rather than teaching you something this repository
  does not do.</p>
  <p>Built from <code>{stage}</code>.</p>
</footer>

<script type="module">
{boot}
const FIXTURES = {fixtures};
const MODULES = {modules};
const RESULTS = {results};
const WHEELS = {wheels};
const START = {model_json};

const $ = (id) => document.getElementById(id);
const fmt = (v) => v === null || v === undefined
  ? "\u2014"
  : v.toLocaleString(undefined, {{ maximumFractionDigits: Math.abs(v) >= 100 ? 0 : 2 }});
const show = (el, text, cls) => {{ el.textContent = text; if (cls) el.className = cls; }};

let pyodide = null;

let booting = null;

async function boot() {{
  const began = performance.now();
  try {{
    pyodide = await bootToolkit({{
      pyodideUrl: "{pyodide}", modules: MODULES, results: RESULTS, wheels: WHEELS,
      status: (text) => show($("agreement"), text, "pending"),
    }});
  }} catch (error) {{
    show($("agreement"),
      "Python did not start, so this page cannot check anything: " + error +
      " \\u2014 everything the page would have told you is in ch02 and in `make check`.",
      "bad");
    return;
  }}

  const ready = Math.round(performance.now() - began);
  $("timing").textContent = "Python ready in " + (ready / 1000).toFixed(1) + "s";

  // Before the reader is invited to trust a verdict, the page checks that it agrees with the
  // build about every fixture. A disagreement is reported, not hidden.
  const disagreed = [];
  for (const fixture of FIXTURES) {{
    const got = await verdict(fixture.text);
    if (got.stage !== fixture.stage) {{
      disagreed.push(fixture.title + ": the build says " + fixture.stage + ", this browser says "
        + got.stage);
    }}
  }}
  if (disagreed.length) {{
    show($("agreement"),
      "This browser does not agree with the build: " + disagreed.join("; ") +
      ". Trust `make check`, not this page.", "bad");
  }} else {{
    show($("agreement"),
      "This browser agrees with the build on all " + FIXTURES.length +
      " checked files, including the one ch02 says a spreadsheet would accept.", "good");
  }}
}}

async function verdict(text) {{
  pyodide.globals.set("_source", text);
  return (await pyodide.runPythonAsync("check(_source)")).toJs(
    {{ dict_converter: Object.fromEntries }});
}}

function report(result) {{
  const v = $("verdict"), d = $("detail");
  d.innerHTML = "";
  if (result.stage === "ok") {{
    show(v, "It runs.", "verdict good");

    // The outputs first and large: a reader who has just written this file wants the number it
    // produces, not a confirmation that its units are consistent.
    const outputs = document.createElement("div");
    outputs.className = "outputs";
    outputs.innerHTML = result.outputs.map((name) => {{
      const node = result.nodes.find((n) => n.name === name) || {{}};
      return `<div class="output"><div class="figure">${{fmt(node.value)}}</div>` +
             `<div class="unit">${{node.unit || ""}}</div>` +
             `<div class="what">${{node.label || name}}</div></div>`;
    }}).join("");
    d.appendChild(outputs);

    const table = document.createElement("table");
    table.innerHTML = "<tr><th>Node</th><th>Kind</th><th>Value</th><th>Unit</th>" +
      "<th>Formula</th></tr>" +
      result.nodes.map((n) =>
        `<tr><td>${{n.label || n.name}}</td><td>${{n.kind}}</td>` +
        `<td class="num">${{fmt(n.value)}}</td><td>${{n.unit}}</td>` +
        `<td>${{n.formula ? "<code>" + n.formula + "</code>" : ""}}</td></tr>`).join("");
    d.appendChild(table);
    const note = document.createElement("p");
    note.textContent = "The build classifies this as a " + result.classification +
      " model. It works that out from the file: a measured constant or a declared ceiling makes " +
      "it a conditional model, and this one has " +
      (result.classification === "conditional" ? "at least one of them." : "neither yet.");
    d.appendChild(note);
  }} else {{
    show(v, {{
      load: "It does not load.",
      units: "It loads, and the units do not work out.",
      evaluate: "The units are sound and it will not evaluate.",
    }}[result.stage] || "It does not run.", "verdict bad");
    const list = document.createElement("ul");
    for (const problem of result.problems) {{
      const item = document.createElement("li");
      item.textContent = problem;
      list.appendChild(item);
    }}
    d.appendChild(list);
  }}
}}

$("run").addEventListener("click", async () => {{
  $("run").disabled = true;
  try {{
    // The first press pays for the runtime; every press after it is arithmetic.
    booting = booting || boot();
    await booting;
    if (!pyodide) return;
    $("run").textContent = "Run";
    const began = performance.now();
    report(await verdict($("source").value));
    $("timing").textContent = "checked in " + Math.round(performance.now() - began) + "ms";
  }} finally {{
    $("run").disabled = false;
  }}
}});
$("reset").addEventListener("click", () => {{ $("source").value = START; }});
</script>
</body>
</html>
"""


CSS = """
:root { color-scheme: light dark; --edge: #cfd8dc; --ink: #263238; --muted: #546e7a;
        --good: #2e7d32; --bad: #b3413a; --panel: #fafafa; }
@media (prefers-color-scheme: dark) {
  :root { --edge: #37474f; --ink: #eceff1; --muted: #b0bec5; --panel: #1c262b;
          --good: #81c784; --bad: #e8756c; }
  body { background: #11181c; }
}
* { box-sizing: border-box; }
body { font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
       color: var(--ink); margin: 0; padding: 16px; max-width: 1600px; margin-inline: auto; }
header h1 { font-size: 20px; margin: 0 0 4px; }
header p, footer p { color: var(--muted); margin: 4px 0; }
#agreement { border: 1px solid var(--edge); border-left-width: 4px; border-radius: 4px;
             padding: 10px 12px; margin: 12px 0; font-size: 14px; }
#agreement.good { border-left-color: var(--good); }
#agreement.bad { border-left-color: var(--bad); }
#agreement.pending { border-left-color: var(--muted); }
/* The model beside its results, but only once both fit. The generator wraps a node's source at
   66 characters, so an editor under about 600px breaks the file the reader is being asked to
   read: at 900px the two columns were 443px each and 183 of the model's 685 lines wrapped. One
   column to 1300px -- what a tablet and a phone have always had -- then two. */
main { display: grid; gap: 16px; grid-template-columns: 1fr; }
@media (min-width: 1300px) { main { grid-template-columns: 1fr 1fr; } }
.bar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
button { font: inherit; padding: 6px 14px; border: 1px solid var(--edge); border-radius: 4px;
         background: var(--panel); color: var(--ink); cursor: pointer; }
button:disabled { opacity: .5; cursor: default; }
#timing { color: var(--muted); font-size: 13px; margin-left: auto; }
textarea { width: 100%; height: 62vh; min-height: 320px; font: 13px/1.5 ui-monospace,
           SFMono-Regular, Menlo, monospace; padding: 10px; border: 1px solid var(--edge);
           border-radius: 4px; background: var(--panel); color: var(--ink); resize: vertical; }
.verdict { font-weight: 600; margin-bottom: 8px; }
.outputs { display: flex; flex-wrap: wrap; gap: 20px; margin: 4px 0 18px; }
.output .figure { font-size: 30px; font-weight: 600; line-height: 1.1; }
.output .unit { color: var(--muted); font-size: 13px; }
.output .what { font-size: 13px; margin-top: 2px; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.verdict.good { color: var(--good); }
.verdict.bad { color: var(--bad); }
#detail ul { padding-left: 18px; }
#detail li { margin-bottom: 8px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
             font-size: 13px; color: var(--bad); }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--edge);
         vertical-align: top; }
th { color: var(--muted); font-weight: 600; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
footer { margin-top: 24px; border-top: 1px solid var(--edge); padding-top: 12px; font-size: 13px; }
"""


def build(stage) -> str:
    """One page for one stage of the running example."""
    model = stage.path.read_text()
    return PAGE.format(
        css=both_ways(CSS),
        theme=FRAME,
        title=html.escape(f"{label_of(stage.chapter)} \u00b7 {stage.title}"),
        model=html.escape(model),
        model_json=json.dumps(model),
        boot=BOOT,
        modules=json.dumps(sources()),
        results=json.dumps(results_for(load_model(stage.path))),
        wheels=json.dumps(wheels()),
        fixtures=json.dumps(fixtures(stage.path)),
        pyodide=PYODIDE,
        stage=html.escape(shown(stage.path)),
    )


def pages() -> dict[str, object]:
    """Where each stage's page goes, keyed by the directory a chapter embeds.

    Named for the chapter rather than the stage, because the chapter is what a reader is in when
    they press Run, and a URL in a book should say where it belongs.
    """
    return {
        stage.chapter.replace("_", "-"): stage
        for stage in stages()
        if not stage.is_the_finished_model
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    for slug, stage in pages().items():
        target = args.out / slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build(stage))
        print(f"  wrote {shown(target)} ({len(target.read_text()):,} bytes)")
    return 0


if __name__ == "__main__":  # pragma: no cover - a thin wrapper around main()
    raise SystemExit(main())
