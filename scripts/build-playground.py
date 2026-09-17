#!/usr/bin/env python3
"""The model file from ch01, runnable in a browser.

    python3 scripts/build-playground.py                # into _build/playground/
    python3 scripts/build-playground.py --out DIR

ch01 ends by telling a reader they have a file that runs, and that multiplying a rate by a plain
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.stamp import shown  # noqa: E402
from sizing.playground.driver import check  # noqa: E402

DEFAULT_OUT = ROOT / "_build" / "playground"
STAGE = ROOT / "models" / "storage_cluster" / "stages" / "01-demand" / "model.yaml"

#: Pinned, because an unpinned runtime changes what a reader sees without changing a line here.
PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/"

#: Every module the two calls reach. Inlined rather than fetched, so the page has one network
#: dependency (the runtime) instead of two.
MODULES = ("__init__", "units", "expr", "dsl", "normal", "mc", "evaluate", "graph")


def fixtures() -> list[dict]:
    """Models whose verdict this build computed, for the browser to agree with.

    The first is the file ch01 leaves the reader with. The second is the mistake ch01 says a
    spreadsheet accepts, which is the one a reader is most likely to make on purpose.
    """
    good = STAGE.read_text()
    broken = good.replace(
        "formula: usable_capacity_t0 * annual_growth ** horizon_periods",
        "formula: peak_read_throughput * horizon_periods",
    )
    assert broken != good, "the fixture no longer matches the stage file it edits"
    cases = [
        ("the file as ch01 leaves it", good),
        ("a rate multiplied by a plain number", broken),
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


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Run the model &mdash; Sizing and TCO</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>Run the model</h1>
  <p>The file ch01 leaves you with, and the toolkit that reads it. Edit it and press
  <b>Check</b>. Nothing is sent anywhere &mdash; the whole thing runs in this tab.</p>
</header>

<div id="agreement" class="pending">Starting Python&hellip; the runtime is a few megabytes, so
the first load is the slow one.</div>

<main>
  <section>
    <div class="bar">
      <button id="run" disabled>Check</button>
      <button id="reset" disabled>Back to the file</button>
      <span id="timing"></span>
    </div>
    <textarea id="source" spellcheck="false" disabled>{model}</textarea>
  </section>
  <section>
    <div id="verdict" class="verdict"></div>
    <div id="detail"></div>
  </section>
</main>

<footer>
  <p>This runs <code>sizing.dsl.load_model</code> and <code>sizing.evaluate.check_units</code>
  &mdash; the same two calls <code>make check</code> makes, not a second implementation of them.
  The fixtures above were checked by the build; the page re-runs them here so that a browser
  which disagrees says so rather than teaching you something this repository does not do.</p>
  <p>Built from <code>{stage}</code>.</p>
</footer>

<script type="module">
const FIXTURES = {fixtures};
const MODULES = {modules};
const START = {model_json};

const $ = (id) => document.getElementById(id);
const show = (el, text, cls) => {{ el.textContent = text; if (cls) el.className = cls; }};

let pyodide = null;

async function boot() {{
  const began = performance.now();
  try {{
    const {{ loadPyodide }} = await import("{pyodide}pyodide.mjs");
    pyodide = await loadPyodide({{ indexURL: "{pyodide}" }});
    await pyodide.loadPackage(["numpy", "micropip"]);
    const micropip = pyodide.pyimport("micropip");
    await micropip.install(["Pint", "PyYAML"]);
  }} catch (error) {{
    show($("agreement"),
      "Python did not start, so this page cannot check anything: " + error +
      " \\u2014 everything the page would have told you is in ch01 and in `make check`.",
      "bad");
    return;
  }}

  pyodide.FS.mkdirTree("/sizing/playground");
  for (const [name, source] of Object.entries(MODULES)) {{
    pyodide.FS.writeFile("/sizing/" + name, source);
  }}
  await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, "/")
from sizing.playground.driver import check
`);

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
      " checked files, including the one ch01 says a spreadsheet would accept.", "good");
  }}
  for (const id of ["run", "reset", "source"]) $(id).disabled = false;
  report(await verdict($("source").value));
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
    show(v, "It loads, and every formula is dimensionally sound.", "verdict good");
    const table = document.createElement("table");
    table.innerHTML = "<tr><th>Node</th><th>Kind</th><th>Unit</th><th>Formula</th></tr>" +
      result.nodes.map((n) =>
        `<tr><td>${{n.name}}</td><td>${{n.kind}}</td><td>${{n.unit}}</td>` +
        `<td>${{n.formula ? "<code>" + n.formula + "</code>" : ""}}</td></tr>`).join("");
    d.appendChild(table);
    const note = document.createElement("p");
    note.textContent = "The build classifies this as a " + result.classification +
      " model. It works that out from the file: a measured constant or a declared ceiling makes " +
      "it a sizing model, and this one has neither yet.";
    d.appendChild(note);
  }} else {{
    show(v, result.stage === "load"
      ? "It does not load."
      : "It loads, and the units do not work out.", "verdict bad");
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
  const began = performance.now();
  report(await verdict($("source").value));
  $("timing").textContent = "checked in " + Math.round(performance.now() - began) + "ms";
  $("run").disabled = false;
}});
$("reset").addEventListener("click", () => {{ $("source").value = START; }});

boot();
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
       color: var(--ink); margin: 0; padding: 16px; max-width: 1080px; margin-inline: auto; }
header h1 { font-size: 20px; margin: 0 0 4px; }
header p, footer p { color: var(--muted); margin: 4px 0; }
#agreement { border: 1px solid var(--edge); border-left-width: 4px; border-radius: 4px;
             padding: 10px 12px; margin: 12px 0; font-size: 14px; }
#agreement.good { border-left-color: var(--good); }
#agreement.bad { border-left-color: var(--bad); }
#agreement.pending { border-left-color: var(--muted); }
main { display: grid; gap: 16px; grid-template-columns: 1fr; }
@media (min-width: 900px) { main { grid-template-columns: 1fr 1fr; } }
.bar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
button { font: inherit; padding: 6px 14px; border: 1px solid var(--edge); border-radius: 4px;
         background: var(--panel); color: var(--ink); cursor: pointer; }
button:disabled { opacity: .5; cursor: default; }
#timing { color: var(--muted); font-size: 13px; margin-left: auto; }
textarea { width: 100%; height: 62vh; min-height: 320px; font: 13px/1.5 ui-monospace,
           SFMono-Regular, Menlo, monospace; padding: 10px; border: 1px solid var(--edge);
           border-radius: 4px; background: var(--panel); color: var(--ink); resize: vertical; }
.verdict { font-weight: 600; margin-bottom: 8px; }
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


def build() -> str:
    modules = {f"{name}.py": (ROOT / "sizing" / f"{name}.py").read_text() for name in MODULES}
    modules["playground/__init__.py"] = ""
    modules["playground/driver.py"] = (ROOT / "sizing" / "playground" / "driver.py").read_text()
    model = STAGE.read_text()
    return PAGE.format(
        css=CSS,
        model=html.escape(model),
        model_json=json.dumps(model),
        modules=json.dumps(modules),
        fixtures=json.dumps(fixtures()),
        pyodide=PYODIDE,
        stage=html.escape(shown(STAGE)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / "index.html"
    target.write_text(build())
    print(f"  wrote {shown(target)} ({len(target.read_text()):,} bytes)")
    return 0


if __name__ == "__main__":  # pragma: no cover - a thin wrapper around main()
    raise SystemExit(main())
