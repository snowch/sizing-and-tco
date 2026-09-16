"""A model is a text file, and this is what one is allowed to say.

The argument for this whole package is in ch01, and it is short: a spreadsheet cannot tell you
where a number came from. A cell holds a value. It does not hold the fact that the value was
measured last March against version 2.4 of something, or that it is a vendor's claim nobody has
checked, or that it was invented in a meeting. Those facts live in the head of whoever built the
sheet, and they leave when that person does.

So a model here is a directed acyclic graph of **named quantities**, each of which declares a
unit and a kind, in a file that diffs and reviews like code. Four kinds:

``input``
    A number or a distribution, with a provenance kind — ``fact``, ``vendor_claim`` or
    ``assumption`` — and a source string. Required, both of them. A model with an input whose
    source is blank does not build.

``derived``
    Arithmetic over other nodes. Its unit is *checked* against its formula, never assumed.

``measured``
    An empirical constant backed by a stamped file under ``bench/results/``, carrying its
    measurement uncertainty and the stack and version it belongs to. When the file is absent the
    node is **not yet measured**, and so is everything downstream of it: the build renders a box
    saying so, and never a placeholder.

``ceiling``
    A utilisation knee or a hard limit, with a declared headroom margin and a stated reason.
    Reports where a scenario sits relative to it, and under sampling reports how much of the
    distribution is over.

The last two are the whole of the book's central distinction (front matter). A model with neither
is a **cost model**: its structure is accounting identities, its inputs are uncertain, and
sampling the inputs is sufficient. A model with either is a **sizing model**, where a chain of
multiplications meets something it cannot represent, and a number alone is not an answer.
``scripts/verify-models.py`` classifies every model on exactly that basis and holds the two to
different rules, so the distinction is something the build enforces rather than something the
front matter asserts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import yaml

from sizing import expr
from sizing.units import UnitError
from sizing.units import parse as parse_unit

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"

#: How much a modeller is claiming when they write a number down.
#:
#: Three, and the gap between the first two is the one that costs money. A ``fact`` is something
#: this repository can point at: a stamped measurement, an invoice, a published specification. A
#: ``vendor_claim`` is a number somebody selling you something has stated — often true, never
#: checked here, and coloured differently in every figure so that it cannot quietly become the
#: first kind. An ``assumption`` is a decision, and naming it as one is what lets a reviewer
#: argue with it.
PROVENANCE_KINDS = ("fact", "vendor_claim", "assumption")

PROVENANCE_MEANING = {
    "fact": "traceable to a stamped measurement, an invoice or a published specification",
    "vendor_claim": "stated by someone selling it; plausible, unverified, and never promoted",
    "assumption": "a decision this model makes, which a reviewer may disagree with",
}


class ModelError(ValueError):
    """A model file that cannot be loaded, naming the file and the node."""


@dataclass(frozen=True)
class Provenance:
    kind: str
    source: str


@dataclass(frozen=True)
class Node:
    name: str
    unit: str
    label: str | None = None
    note: str | None = None
    kind: ClassVar[str] = "node"

    def depends_on(self) -> set[str]:
        return set()

    @property
    def display(self) -> str:
        """What a figure calls this node. Falls back to the name, which is already readable."""
        return self.label or self.name.replace("_", " ")


@dataclass(frozen=True)
class Input(Node):
    value: float | None = None
    distribution: dict | None = None
    provenance: Provenance | None = None
    slider: tuple[float, float] | None = None
    kind: ClassVar[str] = "input"

    @property
    def is_uncertain(self) -> bool:
        return self.distribution is not None


@dataclass(frozen=True)
class Derived(Node):
    formula: dict = field(default_factory=dict)
    formula_text: str = ""
    kind: ClassVar[str] = "derived"

    def depends_on(self) -> set[str]:
        return expr.refs(self.formula)


@dataclass(frozen=True)
class Measured(Node):
    result: str = ""
    #: The stamped payload, or None when nobody has taken this measurement yet.
    measurement: dict | None = None
    kind: ClassVar[str] = "measured"

    @property
    def is_measured(self) -> bool:
        return self.measurement is not None

    @property
    def value(self) -> float | None:
        if self.measurement is None:
            return None
        return float(self.measurement["summary"]["value"])

    @property
    def sd(self) -> float:
        """The measurement's standard error, or zero if it was reported without one.

        Zero is a claim, and a loud one: it says this constant was measured exactly. Almost
        nothing is, so ``scripts/verify-models.py`` reports a measured node with no stated
        uncertainty rather than letting it pass as precision.
        """
        if self.measurement is None:
            return 0.0
        return float(self.measurement["summary"].get("sd", 0.0))

    @property
    def stack(self) -> str | None:
        """What was measured — the implementation and version this constant belongs to.

        The reason a measured constant is not a fact about the world. ch03: change the encoder,
        change the version, change the shape of your data, and this number is about something
        else.
        """
        if self.measurement is None:
            return None
        return self.measurement.get("produced_by", {}).get("stack")


@dataclass(frozen=True)
class Ceiling(Node):
    of: dict = field(default_factory=dict)
    of_text: str = ""
    limit: dict = field(default_factory=dict)
    limit_text: str = ""
    headroom: dict = field(default_factory=dict)
    headroom_text: str = ""
    because: str = ""
    kind: ClassVar[str] = "ceiling"

    def depends_on(self) -> set[str]:
        """Everything the ceiling reads — including its limit and its margin.

        ``limit`` and ``headroom`` are expressions rather than numbers so that a margin used by a
        sizing formula and the margin a ceiling checks against can be *the same node*. Writing
        0.25 in both places is how a model comes to be sized for one headroom and audited against
        another, six months after anybody remembers there were two.
        """
        return expr.refs(self.of) | expr.refs(self.limit) | expr.refs(self.headroom)

    @property
    def declares_headroom(self) -> bool:
        """Whether a margin was stated at all. A ceiling without one is not a sizing rule."""
        return bool(self.headroom_text.strip())


KINDS: dict[str, type[Node]] = {
    "input": Input,
    "derived": Derived,
    "measured": Measured,
    "ceiling": Ceiling,
}


@dataclass(frozen=True)
class Model:
    name: str
    title: str
    currency: str
    nodes: dict[str, Node]
    outputs: tuple[str, ...]
    correlations: tuple[dict, ...] = ()
    description: str = ""
    path: Path | None = None

    # -- shape -------------------------------------------------------------------------

    @property
    def order(self) -> tuple[str, ...]:
        """Every node, parents before children.

        Kahn's algorithm, and the cycle message is the useful part: a model with a loop in it is
        almost always a node that was renamed at one end of a pair of formulas.
        """
        pending = {name: set(node.depends_on()) for name, node in self.nodes.items()}
        ready = sorted(name for name, needs in pending.items() if not needs)
        out: list[str] = []
        while ready:
            name = ready.pop(0)
            out.append(name)
            newly = []
            for other, needs in pending.items():
                if name in needs:
                    needs.discard(name)
                    if not needs and other not in out and other not in ready:
                        newly.append(other)
            ready = sorted([*ready, *newly])
        if len(out) != len(self.nodes):
            stuck = sorted(set(self.nodes) - set(out))
            raise ModelError(
                f"{self.name}: these nodes depend on each other in a loop, so none of them can be "
                f"evaluated: {', '.join(stuck)}"
            )
        return tuple(out)

    def ancestors(self, name: str) -> set[str]:
        """Everything that feeds a node, however far back.

        What the viewer highlights when a reader clicks an output: the sub-graph that produced
        this number and nothing else. On a model with sixty nodes that is the difference between
        a picture and a diagram.
        """
        seen: set[str] = set()
        stack = [name]
        while stack:
            current = stack.pop()
            for parent in self.nodes[current].depends_on():
                if parent not in seen:
                    seen.add(parent)
                    stack.append(parent)
        return seen

    def of_kind(self, kind: str) -> tuple[Node, ...]:
        return tuple(node for node in self.nodes.values() if node.kind == kind)

    # -- the distinction the book is built on -------------------------------------------

    @property
    def is_sizing_model(self) -> bool:
        """Whether this model has something in it that sampling the inputs cannot cover.

        A measured constant or a ceiling, either one. See the module docstring, and the front
        matter, and ``scripts/verify-models.py``, which holds the two kinds of model to different
        rules on the strength of this one property.
        """
        return bool(self.of_kind("measured") or self.of_kind("ceiling"))

    @property
    def classification(self) -> str:
        return "sizing" if self.is_sizing_model else "cost"

    # -- what is not yet known -----------------------------------------------------------

    @property
    def unmeasured(self) -> tuple[str, ...]:
        """Measured nodes whose stamped result does not exist yet."""
        return tuple(
            sorted(
                node.name
                for node in self.nodes.values()
                if isinstance(node, Measured) and not node.is_measured
            )
        )

    def blocked(self) -> dict[str, tuple[str, ...]]:
        """Every node that cannot be evaluated, and which unmeasured constants are why.

        This is ``pending=`` generalised from a figure to a graph. The template this book
        inherits from marks a *figure* as awaiting a measurement; here the missing measurement is
        a node, and everything downstream of it inherits the state automatically. Nothing has to
        be marked by hand, so nothing can be forgotten when the measurement lands.
        """
        missing = set(self.unmeasured)
        if not missing:
            return {}
        out: dict[str, tuple[str, ...]] = {}
        for name in self.order:
            causes: set[str] = set()
            if name in missing:
                causes.add(name)
            for parent in self.nodes[name].depends_on():
                causes |= set(out.get(parent, ()))
            if causes:
                out[name] = tuple(sorted(causes))
        return out


@dataclass(frozen=True)
class Scenario:
    name: str
    title: str
    overrides: dict[str, float] = field(default_factory=dict)
    because: str = ""
    samples: int = 100_000
    seed: int = 20260916
    path: Path | None = None


# -- loading -------------------------------------------------------------------------------


def _require(mapping: dict, key: str, where: str) -> Any:
    if key not in mapping:
        raise ModelError(f"{where}: missing required field {key!r}")
    return mapping[key]


def _node_from(name: str, spec: dict, where: str) -> Node:
    if not isinstance(spec, dict):
        raise ModelError(f"{where}: node {name!r} is not a mapping")
    kind = _require(spec, "kind", f"{where}: node {name!r}")
    if kind not in KINDS:
        raise ModelError(
            f"{where}: node {name!r} has kind {kind!r}; expected one of {', '.join(KINDS)}"
        )
    unit = str(_require(spec, "unit", f"{where}: node {name!r}"))
    try:
        parse_unit(unit)
    except UnitError as exc:
        raise ModelError(f"{where}: node {name!r} declares an unknown unit — {exc}") from exc

    common = {
        "name": name,
        "unit": unit,
        "label": spec.get("label"),
        "note": spec.get("note"),
    }

    if kind == "input":
        provenance = spec.get("provenance") or {}
        return Input(
            **common,
            value=None if spec.get("value") is None else float(spec["value"]),
            distribution=spec.get("distribution"),
            provenance=Provenance(
                kind=str(provenance.get("kind", "")),
                source=str(provenance.get("source", "")),
            ),
            slider=tuple(float(v) for v in spec["range"]) if spec.get("range") else None,
        )

    if kind == "derived":
        text = str(_require(spec, "formula", f"{where}: node {name!r}"))
        return Derived(
            **common, formula=expr.parse(text, where=f"{where}: node {name!r}"), formula_text=text
        )

    if kind == "measured":
        result = str(_require(spec, "result", f"{where}: node {name!r}"))
        from bench.stamp import load_result, result_exists

        return Measured(
            **common,
            result=result,
            measurement=load_result(result) if result_exists(result) else None,
        )

    at = f"{where}: node {name!r}"
    text = str(_require(spec, "of", at))
    limit_text = str(_require(spec, "limit", at))
    headroom_text = "" if spec.get("headroom") is None else str(spec["headroom"])
    return Ceiling(
        **common,
        of=expr.parse(text, where=at),
        of_text=text,
        limit=expr.parse(limit_text, where=f"{at} limit"),
        limit_text=limit_text,
        headroom=expr.parse(headroom_text or "0", where=f"{at} headroom"),
        headroom_text=headroom_text,
        because=str(spec.get("because", "")),
    )


def load_model(path: str | Path) -> Model:
    """Read a model file into a graph, refusing anything that cannot be evaluated.

    Structural failures raise here — an unknown kind, a formula that does not parse, a reference
    to a node that does not exist, a cycle. Editorial failures do not: a blank provenance source
    or a ceiling with no headroom loads fine and is reported by ``scripts/verify-models.py``,
    which lists every one of them at once instead of stopping at the first.
    """
    path = Path(path)
    where = path.relative_to(ROOT) if path.is_absolute() else path
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ModelError(f"{where}: is not a mapping")

    nodes_spec = _require(raw, "nodes", str(where))
    nodes = {name: _node_from(name, spec, str(where)) for name, spec in nodes_spec.items()}

    for node in nodes.values():
        for needed in sorted(node.depends_on()):
            if needed not in nodes:
                raise ModelError(
                    f"{where}: node {node.name!r} refers to {needed!r}, which this model does not "
                    "define. Every quantity in a formula is a node, so that it has a unit and a "
                    "provenance of its own."
                )

    outputs = tuple(str(name) for name in raw.get("outputs", ()))
    for name in outputs:
        if name not in nodes:
            raise ModelError(f"{where}: declares an output {name!r} that is not a node")

    model = Model(
        name=str(_require(raw, "model", str(where))),
        title=str(raw.get("title", raw["model"])),
        currency=str(raw.get("currency", "USD")),
        nodes=nodes,
        outputs=outputs,
        correlations=tuple(raw.get("correlations", ())),
        description=str(raw.get("description", "")).strip(),
        path=path,
    )
    _ = model.order  # raises on a cycle, here rather than three steps later
    return model


def load_scenario(path: str | Path) -> Scenario:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    return Scenario(
        name=str(_require(raw, "scenario", str(path))),
        title=str(raw.get("title", raw["scenario"])),
        overrides={str(k): float(v) for k, v in (raw.get("overrides") or {}).items()},
        because=str(raw.get("because", "")).strip(),
        samples=int(raw.get("samples", 100_000)),
        seed=int(raw.get("seed", 20260916)),
        path=path,
    )


def model_dir(name: str) -> Path:
    return MODELS_DIR / name


def discover() -> tuple[Model, ...]:
    """Every model in the repository, in a stable order."""
    return tuple(load_model(path) for path in sorted(MODELS_DIR.glob("*/model.yaml")))


def scenarios_for(model: Model) -> tuple[Scenario, ...]:
    assert model.path is not None
    return tuple(
        load_scenario(path) for path in sorted((model.path.parent / "scenarios").glob("*.yaml"))
    )
