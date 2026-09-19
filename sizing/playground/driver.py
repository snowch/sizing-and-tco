"""What the browser calls. The real toolkit, in front of a reader who has just been shown a file.

Two calls. ``check`` is the playground's: load a file, check its units, evaluate its point.
``resample`` is the viewer's: the same sampler that stamped the book's intervals, run again with
the inputs a reader has fixed, so that "suppose you knew growth was 1.6" gets the interval that
is left rather than a point value and a note saying the distributions belong to the scenario.

ch02 ends by telling a reader they have a file that runs, and that a rate multiplied by a number
is refused rather than accepted. Until now both were claims: running the file needed a checkout,
a pip install and three make targets, in a chapter whose whole argument is not to take a number
on trust.

Nothing here reimplements anything. It loads the model with ``sizing.dsl.load_model``,
checks it with ``sizing.evaluate.check_units`` and evaluates it with
``sizing.evaluate.point`` — the calls the build makes — so a verdict in the browser is
the build's verdict, not a second opinion about it.
"""

from __future__ import annotations

import json
import tempfile
import traceback
from dataclasses import replace
from pathlib import Path


def check(text: str) -> dict:
    """Load a model file as written and report what the build would say about it."""
    from sizing.dsl import load_model
    from sizing.evaluate import check_units, point

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "model.yaml"
        path.write_text(text)
        try:
            model = load_model(path)
        except Exception as error:  # a malformed file is the commonest thing a reader will make
            return {
                "stage": "load",
                "ok": False,
                "problems": [f"{type(error).__name__}: {error}"],
                "detail": traceback.format_exc(limit=1),
            }

    problems, factors = check_units(model)
    if problems:
        return {"stage": "units", "ok": False, "problems": problems}

    # Only once the units are sound: a value computed from a formula that does not typecheck is
    # a number nobody should be shown, which is the whole argument of the chapter this page
    # belongs to.
    try:
        values = point(model, factors=factors)
    except Exception as error:
        return {
            "stage": "evaluate",
            "ok": False,
            "problems": [f"{type(error).__name__}: {error}"],
        }

    nodes = [
        {
            "name": name,
            "kind": node.kind,
            "unit": node.unit,
            "label": node.label,
            "formula": getattr(node, "formula_text", None),
            "value": values.get(name),
        }
        for name, node in model.nodes.items()
    ]
    return {
        "stage": "ok",
        "ok": True,
        "problems": [],
        "nodes": nodes,
        "order": list(model.order),
        "outputs": list(model.outputs),
        "classification": "sizing" if model.is_sizing_model else "cost",
        "factors": {name: value for name, value in factors.items() if value != 1.0},
    }


def resample(model_text: str, scenario_text: str, fixed: dict | None = None) -> str:
    """Sample the model again with some inputs held at a value, and return what the page needs.

    ``fixed`` maps input names to values. A fixed input is a scenario override: the sampler does
    not draw it, so the interval that comes out is the doubt left in everything else -- which is
    ch19's question asked by dragging a slider. With nothing fixed this is exactly the run that
    stamped the result the page was built from, seed and all, and the page checks that it is.

    Returns JSON text rather than a Python object: the payload is a few hundred kilobytes of
    nested floats, and a string crosses into JavaScript in one piece.
    """
    from sizing.dsl import load_model, load_scenario
    from sizing.export import export_payload

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "scenarios").mkdir()
        (root / "model.yaml").write_text(model_text)
        (root / "scenarios" / "scenario.yaml").write_text(scenario_text)
        model = load_model(root / "model.yaml")
        scenario = load_scenario(root / "scenarios" / "scenario.yaml")
        scenario = replace(
            scenario,
            overrides={**scenario.overrides, **{k: float(v) for k, v in (fixed or {}).items()}},
        )
        payload = export_payload(model, scenario)
    return json.dumps(payload)
