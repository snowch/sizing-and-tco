"""A model is a text file, and this is what one is allowed to say.

The argument for this whole package is in ch02, and it is short: a spreadsheet cannot tell you
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

The last two are the whole of the book's central distinction (ch01). A model with neither is a
**definitional model**: its relationships hold by definition, its inputs are uncertain, and
sampling the inputs is sufficient. A model with either is a **conditional model**: it holds only
on the implementation its constants were measured on and below the limits it declares, where a
chain of multiplications meets something it cannot represent, and a number alone is not an answer.
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
from sizing.mc import DEFAULT_SAMPLES
from sizing.results import load_result, result_exists
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

#: The version of the rules a model file is written against, declared on its first line as
#: ``dsl: 1``. The loader refuses a file that names another, so a tool that writes model files can
#: tell which rules it is being held to, and a file cannot be read under rules it was not written
#: for. Raise it when a change makes a file that loaded before stop loading.
DSL_VERSION = 1

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


#: Who settles an input. A model cannot work this out for itself: the nearest signal it has is
#: whether the input was given a shape, and ch02 is about how poor a proxy that is -- nothing in
#: that chapter's file has a shape, so the growth rate reads as a choice. Declaring it makes the
#: split a claim the model makes rather than an inference from how finished the file is.
#:
#: ``you`` is a choice somebody made and can change: the fleet, the horizon, a headroom margin.
#: ``outside`` is outside your control, an observation, whether or not it has been given a shape
#: yet: the busy hour, the records held, a price. ``definition`` is an identity nobody chooses and the world does not
#: vary -- a year in seconds, one host, one request.
DECIDED_BY = ("you", "outside", "definition")


@dataclass(frozen=True)
class Input(Node):
    value: float | None = None
    distribution: dict | None = None
    provenance: Provenance | None = None
    slider: tuple[float, float] | None = None
    #: One of :data:`DECIDED_BY`. Empty only in a file that has not declared it, which
    #: ``verify-models.py`` refuses.
    decided: str = ""
    kind: ClassVar[str] = "input"

    @property
    def is_uncertain(self) -> bool:
        return self.distribution is not None

    @property
    def is_yours(self) -> bool:
        """Whether a reader could have chosen this differently."""
        return self.decided == "you"


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
    #: The rules the file says it was written against, or None where it does not say.
    dsl: int | None = None

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
    def is_conditional(self) -> bool:
        """Whether this model has something in it that sampling the inputs cannot cover.

        A measured constant or a ceiling, either one. See the module docstring, ch01, and
        ``scripts/verify-models.py``, which holds the two kinds of model to different rules on
        the strength of this one property.
        """
        return bool(self.of_kind("measured") or self.of_kind("ceiling"))

    @property
    def classification(self) -> str:
        return "conditional" if self.is_conditional else "definitional"

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
    samples: int = DEFAULT_SAMPLES
    seed: int = 20260916
    path: Path | None = None


# -- loading -------------------------------------------------------------------------------


def _text(mapping: dict, key: str, default: str = "") -> str:
    """A field as text, where an empty one is empty.

    YAML reads `because:` with nothing after it as None, and `str(None)` is the four letters
    "None". That passed every check for a non-empty reason, so a ceiling with no reason built.
    """
    value = mapping.get(key)
    return default if value is None else str(value)


class _Refusing(yaml.SafeLoader):
    """PyYAML's safe loader, refusing a key written twice in one mapping.

    PyYAML keeps the second of two keys without a word, so a node declared twice in a model file
    was silently the second declaration, and whoever edited the first never saw it take effect.
    """


def _refuse_duplicates(loader: yaml.SafeLoader, node: yaml.MappingNode) -> dict:
    seen: set = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node)
        if key in seen:
            raise ModelError(
                f"line {key_node.start_mark.line + 1}: {key!r} is written twice in the same "
                "mapping, and only the second would count"
            )
        seen.add(key)
    return loader.construct_mapping(node)


_Refusing.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _refuse_duplicates)


def read_yaml(text: str, where: str) -> Any:
    """A model or scenario file's text as data, refusing duplicate keys and naming the file."""
    try:
        return yaml.load(text, Loader=_Refusing)
    except ModelError as exc:
        raise ModelError(f"{where}: {exc}") from None


def _number(value: Any, what: str) -> float:
    """A number from the file, refusing a YAML 1.1 boolean.

    PyYAML reads `yes`, `no`, `on` and `off` as booleans, and `float(True)` is one, so `value: yes`
    loaded as 1.0 and nothing said so.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelError(f"{what} is {value!r}, which is not a number")
    return float(value)


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
    unit = _text(spec, "unit").strip()
    if not unit:
        raise ModelError(
            f"{where}: node {name!r} declares no unit. A pure ratio is written `dimensionless`. A "
            "blank is refused because it could mean a pure ratio, or it could mean the unit was "
            "never decided (ch02)."
        )
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
        at = f"{where}: node {name!r}"
        distribution = spec.get("distribution")
        if isinstance(distribution, dict):
            for shape, parameters in distribution.items():
                for parameter, value in (parameters or {}).items():
                    _number(value, f"{at}: {shape} {parameter}")
        return Input(
            **common,
            value=None if spec.get("value") is None else _number(spec["value"], f"{at}: value"),
            distribution=distribution,
            provenance=Provenance(
                kind=_text(provenance, "kind"),
                source=_text(provenance, "source"),
            ),
            slider=tuple(_number(v, f"{at}: range") for v in spec["range"])
            if spec.get("range")
            else None,
            decided=_text(spec, "decided"),
        )

    if kind == "derived":
        text = str(_require(spec, "formula", f"{where}: node {name!r}"))
        return Derived(
            **common, formula=expr.parse(text, where=f"{where}: node {name!r}"), formula_text=text
        )

    if kind == "measured":
        result = str(_require(spec, "result", f"{where}: node {name!r}"))
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
        because=_text(spec, "because"),
    )


def load_model(path: str | Path) -> Model:
    """Read a model file into a graph, refusing anything that cannot be evaluated.

    Structural failures raise here — an unknown kind, a formula that does not parse, a reference
    to a node that does not exist, a cycle. Editorial failures do not: a blank provenance source
    or a ceiling with no headroom loads fine and is reported by ``scripts/verify-models.py``,
    which lists every one of them at once instead of stopping at the first.
    """
    # Resolved, always. A model loaded by a relative path used to arrive with a relative
    # `path`, and everything downstream that wanted to show it relative to the repository root
    # raised instead — in the verifier, which is the one place a confusing error is least
    # affordable.
    path = Path(path).resolve()
    try:
        where = path.relative_to(ROOT)
    except ValueError:
        where = path
    raw = read_yaml(path.read_text(), str(where))
    if not isinstance(raw, dict):
        raise ModelError(f"{where}: is not a mapping")
    if "dsl" in raw and raw["dsl"] != DSL_VERSION:
        raise ModelError(
            f"{where}: is written for dsl {raw['dsl']!r}, and this toolkit reads dsl {DSL_VERSION}"
        )

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
        currency=_text(raw, "currency", "USD"),
        dsl=raw.get("dsl"),
        nodes=nodes,
        outputs=outputs,
        correlations=tuple(raw.get("correlations", ())),
        description=_text(raw, "description").strip(),
        path=path,
    )
    _ = model.order  # raises on a cycle, here rather than three steps later
    return model


def load_scenario(path: str | Path) -> Scenario:
    path = Path(path)
    raw = read_yaml(path.read_text(), str(path))
    if not isinstance(raw, dict):
        raise ModelError(f"{path}: is not a mapping")
    name = str(_require(raw, "scenario", str(path)))
    return Scenario(
        name=name,
        title=_text(raw, "title", name),
        overrides={
            str(k): _number(v, f"{path}: override {k!r}")
            for k, v in (raw.get("overrides") or {}).items()
        },
        because=_text(raw, "because").strip(),
        samples=int(_number(raw.get("samples", DEFAULT_SAMPLES), f"{path}: samples")),
        seed=int(_number(raw.get("seed", 20260916), f"{path}: seed")),
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
