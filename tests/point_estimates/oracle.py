"""What the chapter's problems are graded against: the model's own bands, the commute in the
taxi example, and the toolkit's own reading of three model files.

Nothing in this module is a stub. The reader is handed its output, not its source, and can
ignore it.
"""

from __future__ import annotations

import math
from pathlib import Path

import yaml

from sizing.dsl import Scenario, load_model
from sizing.evaluate import point

MODEL = "models/web_service/model.yaml"
TOTAL = "hosts_recommended"

#: The taxi example's three inputs. The table on the page is rendered from the same file.
COMMUTE = "tests/point_estimates/fixtures/commute.yaml"

#: Problem 1.3's three descriptions, each written as a model file, in the order the page gives them.
DESCRIBED = (
    "tests/point_estimates/fixtures/model_a.yaml",
    "tests/point_estimates/fixtures/model_b.yaml",
    "tests/point_estimates/fixtures/model_c.yaml",
)


def the_model():
    return load_model(MODEL)


def total_with(model, held: dict[str, float]) -> float:
    """The hosts the model recommends with these inputs held at these values."""
    return point(model, Scenario("held", "held", held))[TOTAL]


def ends(model) -> dict[str, tuple[float, float]]:
    """The bottom and top of each band that can move the host count, however the file writes it.

    The file bands eighteen inputs. Twelve of them are on the cost side and cannot reach a host
    count at all, so holding them at their extremes does nothing to it. Handing a reader
    eighteen entries after a chapter that discussed six, twelve of which are inert, cost the
    chapter a paragraph explaining that they were harmless -- which is a problem apologising for
    its own scope.

    Which ones move it is decided by moving them, rather than by walking the graph. That is the
    definition the problems care about, it needs nothing but the model, and it stays true if the
    model's wiring changes.
    """
    out = {}
    for name, node in model.nodes.items():
        for parameters in (getattr(node, "distribution", None) or {}).values():
            if "p10" in parameters:
                band = (parameters["p10"], parameters["p90"])
            else:
                band = (parameters["minimum"], parameters["maximum"])
            if total_with(model, {name: band[0]}) != total_with(model, {name: band[1]}):
                out[name] = band
    return out


def commute() -> dict[str, tuple[float, float]]:
    """Each input of the taxi commute: its usual value, and the most it could be."""
    raw = yaml.safe_load(Path(COMMUTE).read_text())
    return {name: (float(entry["usual"]), float(entry["most"])) for name, entry in raw.items()}


def cost_of_commute(values: dict[str, float]) -> float:
    """A year's fares: days, times minutes a day, times the fare a minute."""
    return math.prod(values.values())


def rise(moving: tuple[str, ...]) -> float:
    """How many times the year's cost grows when these inputs, and no others, go to their most."""
    inputs = commute()
    usual = {name: low for name, (low, _high) in inputs.items()}
    moved = {**usual, **{name: inputs[name][1] for name in moving}}
    return cost_of_commute(moved) / cost_of_commute(usual)


def kinds() -> list[str]:
    """What the toolkit calls each of problem 1.3's models, read from the files."""
    return [load_model(path).classification for path in DESCRIBED]
