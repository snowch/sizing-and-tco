"""What the chapter's first two problems are graded against: the model's own bands, and itself.

Both problems ask for a ratio out of the same six inputs, so the way those six are found lives
here rather than in either test file. Nothing in this module is a stub. The reader is handed its
output, not its source, and can ignore it.
"""

from __future__ import annotations

from sizing.dsl import Scenario, load_model
from sizing.evaluate import point

MODEL = "models/web_service/model.yaml"
TOTAL = "hosts_recommended"


def the_model():
    return load_model(MODEL)


def total_with(model, held: dict[str, float]) -> float:
    """The hosts the model recommends with these inputs held at these values."""
    return point(model, Scenario("held", "held", held))[TOTAL]


def ends(model) -> dict[str, tuple[float, float]]:
    """The bottom and top of each band that can move the host count, however the file writes it.

    The file bands eighteen inputs. Twelve of them are on the cost side and cannot reach a host
    count at all, so holding them at their extremes does nothing: the ratio these problems ask
    for is the same number to the last digit with them and without them. Handing a reader
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


def on_paper(model) -> float:
    """Every input at the bottom of its band, then every input at the top, and the ratio."""
    bands = ends(model)
    low = total_with(model, {name: bottom for name, (bottom, _top) in bands.items()})
    high = total_with(model, {name: top for name, (_bottom, top) in bands.items()})
    return high / low


def each_alone(model) -> dict[str, float]:
    """What one input can do to the host count on its own, across its band."""
    out = {}
    for name, (bottom, top) in ends(model).items():
        low, high = total_with(model, {name: bottom}), total_with(model, {name: top})
        out[name] = max(low, high) / min(low, high)
    return out
