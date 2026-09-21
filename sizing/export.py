"""One JSON per model and scenario — everything the published page needs, and nothing it does not.

The page is static. There is no server, no database and no Python in the browser, so whatever a
reader can see has to be in this file, computed here, by the build that also ran the tests.

## What is in it, and what is deliberately not

**In:** the graph with its layout, every node's kind, unit, provenance and formula; the point
value of every node; a summary and a sixty-four-bin histogram for every *sampled* node; the
ceiling reports; a tornado per output; and the expression trees the browser needs to recompute
point values when a slider moves.

**Not in:** the samples themselves. A hundred thousand draws for each of fifty nodes is forty
megabytes on a book page, to show something a histogram already shows. The histogram is forty
numbers and says the same thing.

**Also not in: any way to re-run the Monte Carlo.** That is a decision rather than an omission.
Moving a slider recomputes every point value instantly, because a point is arithmetic; it does
*not* redraw the intervals, because the intervals came from a sampler that was seeded, stamped
and checked, and a second sampler in JavaScript would be a second answer nobody had verified. So
the distributions belong to the scenario, the page says so when a slider moves off it, and a
reader who wants the interval for their own settings writes a scenario file and re-runs the
build. This book does not show a number it did not produce.

## Two evaluators, one answer

``viewer_expectations`` holds a set of slider positions and the values Python computes at each.
``tests/test_viewer.py`` runs the JavaScript over exactly those and fails on any disagreement, so
the browser cannot quietly drift from the build. See ``sizing/expr.py``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sizing import graph
from sizing.dsl import Ceiling, Derived, Input, Measured, Model, Scenario, scenarios_for
from sizing.evaluate import conversion_factors, evaluate, point, tornado

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "models" / "_out"

#: Slider positions the exported JavaScript is checked against. Fractions of each slider's
#: declared range, chosen to include both ends and something off-centre, because an interpreter
#: that is right at the midpoint and wrong at the edges is a real and boring bug.
PROBE_FRACTIONS = (0.0, 0.25, 0.5, 0.9, 1.0)


def export_payload(model: Model, scenario: Scenario) -> dict:
    """Everything the page for one model and scenario needs."""
    evaluation = evaluate(model, scenario)
    placement = graph.place(model)
    blocked = model.blocked()

    nodes: dict[str, Any] = {}
    for name in model.order:
        node = model.nodes[name]
        entry: dict[str, Any] = {
            "kind": node.kind,
            "unit": node.unit,
            "label": node.display,
            "note": node.note,
            "depends_on": sorted(node.depends_on()),
            **placement[name],
        }
        if name in blocked:
            entry["blocked_by"] = list(blocked[name])
        if name in evaluation.point:
            entry["point"] = evaluation.point[name]
        if name in evaluation.summaries:
            entry["summary"] = evaluation.summaries[name]
            entry["histogram"] = evaluation.histograms[name]

        if isinstance(node, Input):
            entry["provenance"] = {
                "kind": node.provenance.kind if node.provenance else "",
                "source": node.provenance.source if node.provenance else "",
            }
            entry["distribution"] = node.distribution
            # Who settles this one, so the graph can mark it rather than guess. `verify-models`
            # refuses a model that leaves it out.
            entry["decided"] = node.decided
            if node.slider:
                entry["slider"] = {"min": node.slider[0], "max": node.slider[1]}
        elif isinstance(node, Derived):
            entry["formula"] = node.formula_text
            entry["ast"] = node.formula
        elif isinstance(node, Measured):
            entry["result"] = node.result
            entry["measured"] = (
                None
                if not node.is_measured
                else {
                    "value": node.value,
                    "sd": node.sd,
                    "stack": node.stack,
                    "corpus": (node.measurement or {}).get("produced_by", {}).get("corpus"),
                    "generated_at": (node.measurement or {}).get("generated_at"),
                    "fingerprint": (node.measurement or {}).get("code_fingerprint"),
                }
            )
        else:
            assert isinstance(node, Ceiling)
            entry["formula"] = node.of_text
            entry["ast"] = node.of
            entry["ceiling"] = evaluation.ceilings.get(name)
        nodes[name] = entry

    return {
        "model": model.name,
        "title": model.title,
        "description": model.description,
        "currency": model.currency,
        "classification": model.classification,
        "scenario": {
            "name": scenario.name,
            "title": scenario.title,
            "because": scenario.because,
            "samples": scenario.samples,
            "seed": scenario.seed,
            "overrides": scenario.overrides,
        },
        "scenarios": [s.name for s in scenarios_for(model)],
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "order": list(model.order),
        "outputs": list(model.outputs),
        "nodes": nodes,
        "factors": conversion_factors(model),
        "correlations": [dict(c) for c in model.correlations],
        "unmeasured": list(model.unmeasured),
        "tornado": {name: tornado(model, scenario, name) for name in model.outputs},
        "viewer_expectations": viewer_expectations(model, scenario),
    }


def viewer_expectations(model: Model, scenario: Scenario) -> list[dict]:
    """Slider positions, and what Python says the model is at each of them.

    The contract between the two evaluators. Every value of every node is recorded, not just the
    outputs: a browser that agrees about the total and disagrees about an intermediate node is
    still showing the reader a wrong number, on the node panel, where it is least likely to be
    noticed.
    """
    sliders = [
        (name, node.slider)
        for name, node in model.nodes.items()
        if isinstance(node, Input) and node.slider
    ]
    factors = conversion_factors(model)
    probes = []
    for fraction in PROBE_FRACTIONS:
        overrides = {name: low + fraction * (high - low) for name, (low, high) in sorted(sliders)}
        from dataclasses import replace

        probed = replace(scenario, overrides={**scenario.overrides, **overrides})
        probes.append({"overrides": overrides, "values": point(model, probed, factors)})
    return probes


def write(model: Model, scenario: Scenario, out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{model.name}.{scenario.name}.json"
    payload = export_payload(model, scenario)
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return path
