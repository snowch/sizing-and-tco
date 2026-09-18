"""What the browser calls. The real toolkit, in front of a reader who has just been shown a file.

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

import tempfile
import traceback
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
