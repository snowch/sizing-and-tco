#!/usr/bin/env python3
"""Assemble the self-contained page that draws one future at a time.

    python3 scripts/build-futures.py                 # into _build/futures/
    python3 scripts/build-futures.py --out DIR       # somewhere else

ch01 says the honest answer to *how big* is a range, and that you get it by running the
arithmetic again and again. A reader who has not met sampling has no reason to believe that
sentence: repeating a sum gives the same sum. This page is the demonstration, embedded in the
chapter at the paragraph that makes the claim.

It is built from the **stamped model result**, like every other page here, so the spreads a
reader draws from are the ones the model file declares and the dashed line on the pile is the
point estimate the chapter's table prints. What it is *not* is a re-run of the stamped
experiment, and the page says so in its own footer rather than leaving a reader to assume:
the browser's random stream is not numpy's, correlations are applied by ch14's method across a
whole sample and cannot be applied to one draw, and the measured constant in this chain is held
at its point value here. Same distributions, a different handful of futures.

Everything is inlined — the payload, the sampler, the evaluator, the widget, the stylesheet — so
the page is one file that opens from a local disk, from GitHub Pages, or from anywhere else, with
no server, no bundler and no network.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.outline import CHAPTERS  # noqa: E402
from bench.stamp import load_result, shown  # noqa: E402
from bench.tables import REPOSITORY  # noqa: E402

VIEWER = ROOT / "sizing" / "viewer"
DEFAULT_OUT = ROOT / "_build" / "futures"

#: One page, for now: ch01's. Keyed by the file it is published as, because the chapter's
#: `{iframe}` names that path and nothing else resolves it.
PAGES = {
    "point-estimates": {
        "result": "web_service-reference",
        "answer": "hosts_recommended",
        # The order the six inputs are listed in the chapter's own paragraph, so a reader meets
        # them in the same order twice.
        "order": [
            "peak_request_rate_t0",
            "annual_growth",
            "service_demand",
            "hot_fraction",
            "index_overhead",
            "os_reserve",
        ],
        # Where the pile's right-hand edge sits, as a multiple of the stamped p95. Everything
        # past it goes in the column marked *more*, which is a column rather than a clamp so a
        # reader can see there is a tail and how little of it there is. At 1.6 the edge lands
        # near the stamped p99: about one future in a hundred is out there.
        "reach": 1.6,
        # Roughly how many bars. Rounded below so that each one covers a whole number of hosts:
        # this answer is a whole number, and bins of eight beside bins of nine draw a sawtooth
        # nothing in the model put there. The first version of this page had one.
        "bars": 46,
    },
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>One future at a time — {answer_label}</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>One future at a time</h1>
  <p>Every input below is uncertain, and the model file says by how much. One press picks a value
  for each of them, from its own spread, and works the fleet through once. That is one future —
  one answer to <em>what if it turns out like this?</em></p>
</header>
<main>
  <div id="bar">
    <button id="one" class="primary" type="button">Draw one future</button>
    <button id="many" type="button">Draw 100</button>
    <button id="again" type="button">Start again</button>
    <span id="count"></span>
  </div>
  <section id="left">
    <h2>What this future brought</h2>
    <p class="note">The pale shape is the spread the model file declares: where it is fat, values
    are common. The blue line is this future's value, and the ticks below it are where the last
    sixty landed.</p>
    <div id="inputs"></div>
  </section>
  <section id="right">
    <h2>{answer_label}</h2>
    <p class="note">Every answer you draw stays on the pile.</p>
    <svg id="pile" role="img"
         aria-label="Answers piling up between {lo} and {hi} {answer_unit}"></svg>
    <p class="key"><span><i class="est"></i>the single number</span>
      <span><i class="now"></i>this future</span></p>
    <p class="verdict" id="verdict"></p>
  </section>
</main>
<footer>
  <p>Drawn here, in this tab, from the spreads in
  <a href="{stamp}">{result}</a> — not a replay of it. The book's own run ties two of these
  inputs together and samples the measured constant in this chain; both are done across a whole
  set of futures rather than one at a time, so neither can happen here. Expect the same middle
  and a thinner tail.</p>
  <p>{chapter} says what to do with the pile. <a href="{model}">The model</a> has every formula
  behind it, with sliders.</p>
</footer>
<script>window.PAYLOAD = {payload};</script>
<script type="module">
{sample_js}
{evaluate_js}
window.SAMPLE = {{ at, stream }};
window.EVALUATE = {{ evaluatePoint }};
{futures_js}
</script>
</body>
</html>
"""


def ancestors(payload: dict, target: str) -> set[str]:
    """Every node the answer is computed from, the answer included.

    The page carries these and nothing else. An input that cannot reach the answer would be drawn
    and then ignored, which on a page whose whole subject is *what moves this number* would be a
    lie told in the reader's own hands.
    """
    seen: set[str] = set()
    stack = [target]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(payload["nodes"][name].get("depends_on", []))
    return seen


def trim(payload: dict, keep: set[str]) -> dict:
    """The part of the export the browser needs: the graph, and nothing said about it."""
    nodes = {}
    for name in keep:
        node = payload["nodes"][name]
        cut = {"kind": node["kind"], "point": node.get("point")}
        for field in ("ast", "label", "unit", "distribution", "blocked_by"):
            if field in node:
                cut[field] = node[field]
        nodes[name] = cut
    return {
        "order": [name for name in payload["order"] if name in keep],
        "nodes": nodes,
        "factors": {k: v for k, v in payload["factors"].items() if k in keep},
    }


def build(slug: str, out_dir: Path) -> Path:
    spec = PAGES[slug]
    result = load_result(spec["result"])
    payload = result["summary"]
    answer = spec["answer"]

    keep = ancestors(payload, answer)
    spreads = {
        name: payload["nodes"][name]["distribution"]
        for name in payload["order"]
        if name in keep
        and payload["nodes"][name]["kind"] == "input"
        and payload["nodes"][name].get("distribution")
    }
    # The page shows every uncertain input it draws. A chapter that listed six and a page that
    # showed four of them would teach the reader to stop counting.
    order = spec["order"]
    assert set(order) == set(spreads), (
        f"{slug}: the page lists {sorted(order)} and the answer draws {sorted(spreads)}"
    )

    summary = payload["nodes"][answer]["summary"]
    point = payload["nodes"][answer]["point"]
    step = max(1, round(summary["p95"] * spec["reach"] / spec["bars"]))
    bins = math.ceil(summary["p95"] * spec["reach"] / step)
    top = step * bins

    page = trim(payload, keep) | {
        "answer": answer,
        "answer_label": payload["nodes"][answer]["label"],
        "answer_unit": payload["nodes"][answer]["unit"],
        "spreads": spreads,
        "shown": order,
        "point": point,
        "band": [0, top],
        "bins": bins,
    }

    # Both files are ES modules that would normally import each other. Inlined into one script
    # block there is nothing to import from, so the export keywords come out and the import lines
    # with them — the same dozen characters of surgery `build-viewers.py` does, for the same
    # reason: a book should not have to ship a bundler.
    sample_js = (VIEWER / "sample.js").read_text().replace("export function", "function")
    sample_js = sample_js.replace("export const SHAPES", "const SHAPES")
    evaluate_js = (VIEWER / "evaluate.js").read_text().replace("export function", "function")
    futures_js = (VIEWER / "futures.js").read_text()

    chapter = next(c for c in CHAPTERS if c.slug == "point_estimates")
    rendered = PAGE.format(
        css=(VIEWER / "futures.css").read_text(),
        answer_label=html.escape(page["answer_label"]),
        answer_unit=html.escape(page["answer_unit"]),
        lo=0,
        hi=top,
        chapter=f"{chapter.label} {html.escape(chapter.title)}",
        result=html.escape(spec["result"]),
        stamp=f"{REPOSITORY}/bench/results/{spec['result']}.json",
        # Relative, not root-relative: this page sits beside `models/` in the built site, and a
        # `/models/...` link would drop the project's base path and 404 for every reader.
        model=f"../models/{spec['result']}.html",
        payload=json.dumps(page, separators=(",", ":")),
        sample_js=sample_js,
        evaluate_js=evaluate_js,
        futures_js=futures_js,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slug}.html"
    path.write_text(rendered)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    # Relative to the repository, not to wherever the shell happens to be.
    out = args.out if args.out.is_absolute() else ROOT / args.out

    for slug in PAGES:
        path = build(slug, out)
        print(f"  wrote {shown(path)} ({path.stat().st_size / 1024:.0f} KB)")
    print(f"\nbuild-futures: OK ({len(PAGES)} page(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
