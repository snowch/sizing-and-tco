"""Working a model out: once at a point, once across a hundred thousand possible worlds.

Three passes over the same graph, sharing one expression walker:

**Units**, with Pint quantities, at build time. Every formula is evaluated dimensionally and the
result compared against what the node declared. A model that multiplies series by requests and
calls the answer bytes does not build. This is the pass that has no equivalent in a spreadsheet
and is the reason the DSL exists.

**A point**, in plain floats. One value per node, from the scenario's overrides, each input's
stated value or the median of its distribution, and each measured constant's stamped figure. This
is the number a reader sees first, and ch13 exists because it is not an answer on its own.

**A sample**, in numpy arrays. Every uncertain input becomes a hundred thousand draws, the draws
are correlated where the model says they move together, and then the *same* formulas propagate
them through the graph. Nothing about the arithmetic changes between the second pass and the
third — which is the point, and is why the walker below takes its function table as an argument
rather than having three copies with different imports at the top.

## Nodes that cannot be worked out

A ``measured`` node whose stamped result does not exist has no value, and neither does anything
downstream of it. Those nodes are skipped rather than filled in, and :meth:`Model.blocked` says
which missing constant is responsible for each one. Everything that can be computed still is, so
a half-measured model is a useful document rather than a blank page.
"""

from __future__ import annotations

import functools
import math
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from sizing import mc
from sizing.dsl import (  # noqa: F401
    Ceiling,
    Derived,
    Input,
    Measured,
    Model,
    Scenario,
    load_scenario,
)
from sizing.units import UNITS, compatible, described
from sizing.units import parse as parse_unit

#: The percentiles a tornado swings an input between. Wide enough to matter, narrow enough that
#: the input is still plausibly there — ch18 argues about the choice, which is a real argument.
TORNADO_LOW, TORNADO_HIGH = 0.1, 0.9


class EvaluationError(ValueError):
    """A model that loads and still cannot be worked out."""


# -- one walker, three function tables -------------------------------------------------------


def _walk(tree: dict, lookup: dict[str, Any], functions: dict[str, Any]) -> Any:
    """Evaluate an expression tree against whatever ``lookup`` holds.

    Floats, numpy arrays and Pint quantities all work, because arithmetic on all three is spelled
    the same way. The only thing that differs between the three passes is ``functions``.
    """
    op = tree["op"]
    if op == "const":
        return tree["value"]
    if op == "ref":
        name = tree["name"]
        if name not in lookup:
            raise EvaluationError(f"{name!r} has no value at this point in the graph")
        return lookup[name]
    if op == "neg":
        return -_walk(tree["args"][0], lookup, functions)
    if op == "call":
        args = [_walk(arg, lookup, functions) for arg in tree["args"]]
        return functions[tree["fn"]](*args)
    left, right = (_walk(arg, lookup, functions) for arg in tree["args"])
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        return left / right
    return left**right


SCALAR_FUNCTIONS = {
    "min": min,
    "max": max,
    "ceil": math.ceil,
    "floor": math.floor,
    "sqrt": math.sqrt,
    "log": math.log,
    "exp": math.exp,
}

# `np.maximum` and `np.minimum` take two arrays; a third positional argument is their `out=`.
# Handed `max(a, b, c)`, they wrote the answer into c's samples in place -- every sample of the
# third chain silently became the maximum -- and no model had used a three-way max until the web
# service's three host chains met. Reduce over the arguments instead, however many there are.
ARRAY_FUNCTIONS = {
    "min": lambda *args: functools.reduce(np.minimum, args),
    "max": lambda *args: functools.reduce(np.maximum, args),
    "ceil": np.ceil,
    "floor": np.floor,
    "sqrt": np.sqrt,
    "log": np.log,
    "exp": np.exp,
}


def _unit_ceil(q):
    """``ceil`` on a quantity: round the magnitude, keep the unit.

    You cannot buy two thirds of a node, and the result is still measured in nodes. Pint has no
    opinion about this, so the book states one.
    """
    return UNITS.Quantity(math.ceil(_magnitude(q)), _units_of(q))


def _unit_floor(q):
    return UNITS.Quantity(math.floor(_magnitude(q)), _units_of(q))


def _magnitude(q):
    return q.magnitude if hasattr(q, "magnitude") else q


def _units_of(q):
    return q.units if hasattr(q, "units") else UNITS.dimensionless


UNIT_FUNCTIONS = {
    "min": lambda *a: min(a),
    "max": lambda *a: max(a),
    "ceil": _unit_ceil,
    "floor": _unit_floor,
    "sqrt": np.sqrt,
    "log": lambda q: math.log(_magnitude(UNITS.Quantity(q).to("dimensionless"))),
    "exp": lambda q: math.exp(_magnitude(UNITS.Quantity(q).to("dimensionless"))),
}


# -- pass one: units ---------------------------------------------------------------------


def plausible_magnitudes(model: Model) -> dict[str, float]:
    """A realistic number for every node, to do the dimensional pass with.

    Not cosmetic. Checking units by evaluating each formula at magnitude 1 looks reasonable and
    is wrong in a way this model caught immediately: ``node_raw_capacity * (1 - capacity_headroom)``
    becomes a division by zero, and the unit checker reports a dimensional error in a formula
    whose dimensions are fine. The arithmetic has to be done on numbers that are not all the
    same number.

    So each node gets its real value where one can be computed — that is what the numbers *are*,
    and they can never be degenerate in a way the model itself is not. A node downstream of a
    constant nobody has measured gets 1.0, and if that makes its formula undefined it is retried
    at a value that cancels nothing. A node that still cannot be evaluated is reported by
    :func:`check_units` for what it is, rather than as a units problem it is not.
    """
    magnitudes: dict[str, float] = {}
    for name in model.order:
        node = model.nodes[name]
        try:
            if isinstance(node, Input):
                resolved = point_value_of_input(node, None)
                magnitudes[name] = 1.0 if resolved is None else resolved
            elif isinstance(node, Measured):
                magnitudes[name] = 1.0 if node.value is None else float(node.value)
            elif isinstance(node, Derived):
                magnitudes[name] = float(_walk(node.formula, magnitudes, SCALAR_FUNCTIONS))
            else:
                magnitudes[name] = float(_walk(node.of, magnitudes, SCALAR_FUNCTIONS))
        except Exception:
            # 0.37 rather than 1.0 or 0: it cancels nothing, it keeps `1 - x` positive, and it
            # leaves a logarithm defined. Only reached downstream of an unmeasured constant.
            magnitudes[name] = 0.37
    return magnitudes


def check_units(model: Model) -> tuple[list[str], dict[str, float]]:
    """Every dimensional error in a model, and the conversion each formula needs.

    Returns problems and factors. The problems are returned rather than raised because a unit
    mistake at the top of a chain produces several downstream, and fixing them one build at a
    time is miserable.

    **The factors are the half of this that is easy to get wrong.** Checking dimensions alone is
    not enough, and the case that proves it is the running example's unit cost: ``USD/TB/year``
    and ``USD/TB/month`` have exactly the same dimensions, so a check that compared only
    dimensionality would wave through a unit-economics figure twelve times too large. Each
    formula is therefore evaluated dimensionally, the result *converted* into the unit the node
    declared, and the conversion factor recorded for the evaluator to apply.

    That is what lets a model file be written the way a person thinks: take the inputs in the
    units the invoices and datasheets use, declare each output in the unit you want to read it
    in, and let the build do the arithmetic everybody gets wrong by hand. Appendix D lists the
    ones that bite — ``TB`` against ``TiB`` above all, which Pint converts correctly and
    silently, and which the reader still has to know which of the two the vendor meant.
    """
    problems: list[str] = []
    factors: dict[str, float] = {}
    magnitudes = plausible_magnitudes(model)
    quantities: dict[str, Any] = {}

    for name in model.order:
        node = model.nodes[name]
        declared = parse_unit(node.unit)
        quantities[name] = UNITS.Quantity(magnitudes[name], declared)
        if not isinstance(node, Derived | Ceiling):
            continue

        parts = [
            (
                "",
                node.formula if isinstance(node, Derived) else node.of,
                node.formula_text if isinstance(node, Derived) else node.of_text,
                node.unit,
            )
        ]
        if isinstance(node, Ceiling):
            # A limit is compared against the value, so it must be the same kind of thing; a
            # headroom is a fraction of it, so it must be a pure number. Both are checked here
            # rather than at evaluation, where the failure would surface as a strange product.
            parts.append((" limit", node.limit, node.limit_text, node.unit))
            parts.append((" headroom", node.headroom, node.headroom_text or "0", "dimensionless"))

        for suffix, tree, text, wanted in parts:
            try:
                produced = _walk(tree, quantities, UNIT_FUNCTIONS)
            except Exception as exc:  # pint raises its own hierarchy, plus UnitError
                problems.append(
                    f"{model.name}: node {name!r}{suffix} does not typecheck. `{text}` — {exc}"
                )
                continue
            produced_unit = str(_units_of(produced))
            if not compatible(produced_unit, wanted):
                problems.append(
                    f"{model.name}: node {name!r}{suffix} declares {wanted!r}, "
                    f"{described(wanted)}, but `{text}` produces {produced_unit!r}, "
                    f"{described(produced_unit)}"
                )
                continue
            factor = float(UNITS.Quantity(1.0, produced_unit).to(wanted).magnitude)
            key = name if suffix == "" else f"{name}.{suffix.strip()}"
            factors[key] = factor
            for issue in _mixed_operands(tree, quantities, text, wanted):
                problems.append(f"{model.name}: node {name!r}{suffix} {issue}")
            rounding = _rounds_in_the_wrong_unit(tree, quantities, text, wanted)
            if rounding:
                problems.append(f"{model.name}: node {name!r}{suffix} {rounding}")

    return problems, factors


def _unit_name(walked: Any) -> str:
    """The unit a walked subtree produced, as Pint spells it. A bare number is dimensionless."""
    return str(_units_of(walked)) if hasattr(walked, "units") else "dimensionless"


def _mixed_operands(tree: dict, quantities: dict[str, Any], text: str, wanted: str) -> list[str]:
    """Where a formula's raw arithmetic is wrong however its result is converted.

    The evaluator applies one conversion factor per node, to the whole formula's result. That is
    right for products and quotients, whose factors multiply through, and wrong wherever two
    operands meet other than by multiplying: a sum, a difference, a ``min`` or a ``max`` of
    quantities declared in different units of one dimension adds or compares their numbers as if
    the units matched, and a ``ceil`` or ``floor`` at the top of a formula rounds a number that is
    not yet in the unit it will be read in. Both typecheck, because the dimensions agree, and both
    compute a wrong number in silence; ``TB + TiB`` and ``USD/year + USD/month`` are the cases
    that bite. Each is refused here with the repair: declare the operands in one unit.
    """
    op = tree["op"]
    if op in ("const", "ref"):
        return []
    args = tree.get("args", [])
    problems: list[str] = []
    for arg in args:
        problems.extend(_mixed_operands(arg, quantities, text, wanted))
    produced = [_unit_name(_walk(arg, quantities, UNIT_FUNCTIONS)) for arg in args]
    meets = op in ("+", "-") or (op == "call" and tree["fn"] in ("min", "max"))
    if meets and len(set(produced)) > 1:
        named = " and ".join(repr(unit) for unit in dict.fromkeys(produced))
        how = {"+": "adds", "-": "subtracts"}.get(op, f"takes the {tree.get('fn')} of")
        problems.append(
            f"{how} quantities in {named}: `{text}`. The build converts a formula's result "
            "once, into the node's unit, so quantities that meet in a sum, a difference or a "
            "comparison must be declared in one unit. Declare them in one, or convert one of "
            "them in a node of its own."
        )
    return problems


def _rounds_in_the_wrong_unit(tree: dict, quantities: dict[str, Any], text: str, wanted: str):
    """A ``ceil`` or ``floor`` at the top of a formula, over a number not yet in the node's unit."""
    if tree["op"] != "call" or tree["fn"] not in ("ceil", "floor"):
        return None
    inside = _unit_name(_walk(tree["args"][0], quantities, UNIT_FUNCTIONS))
    if not compatible(inside, wanted):
        return None  # the dimensional check reports that one
    factor = float(UNITS.Quantity(1.0, inside).to(wanted).magnitude)
    if abs(factor - 1.0) < 1e-12:
        return None
    return (
        f"rounds a number in {inside!r} that the node reads in {wanted!r}: `{text}`. The build "
        f"converts after the formula, so `{tree['fn']}` has rounded the wrong number. Declare "
        "what is under it in the node's own unit."
    )


def conversion_factors(model: Model) -> dict[str, float]:
    """Just the factors, for a model already known to typecheck."""
    problems, factors = check_units(model)
    if problems:
        raise EvaluationError(
            f"{model.name} does not typecheck, so it cannot be evaluated:\n  - "
            + "\n  - ".join(problems)
        )
    return factors


# -- pass two: a point --------------------------------------------------------------------


def point_value_of_input(node: Input, scenario: Scenario | None) -> float | None:
    """What a single number for this input would be.

    A scenario override wins; then a stated value; then the median of a declared distribution.
    The median rather than the mean, deliberately: for the lognormals this book uses for prices
    the two differ, the median is the one a person means when they say "about", and a table of
    means silently overstates every skewed input in the model.
    """
    if scenario and node.name in scenario.overrides:
        return float(scenario.overrides[node.name])
    if node.value is not None:
        return float(node.value)
    if node.distribution is not None:
        shape, parameters = mc.one_shape(node.distribution)
        return float(mc.SHAPES[shape](np.array([0.5]), **parameters)[0])
    return None


def point(
    model: Model, scenario: Scenario | None = None, factors: dict[str, float] | None = None
) -> dict[str, float]:
    """One value per node, skipping anything an unmeasured constant blocks."""
    factors = conversion_factors(model) if factors is None else factors
    blocked = model.blocked()
    values: dict[str, float] = {}
    for name in model.order:
        if name in blocked:
            continue
        node = model.nodes[name]
        if isinstance(node, Input):
            resolved = point_value_of_input(node, scenario)
            if resolved is None:
                raise EvaluationError(
                    f"{model.name}: input {name!r} has neither a value nor a distribution"
                )
            values[name] = resolved
        elif isinstance(node, Measured):
            if scenario and name in scenario.overrides:
                values[name] = float(scenario.overrides[name])
            else:
                values[name] = float(node.value)  # type: ignore[arg-type]
        elif isinstance(node, Derived):
            values[name] = float(_walk(node.formula, values, SCALAR_FUNCTIONS)) * factors[name]
        else:
            values[name] = float(_walk(node.of, values, SCALAR_FUNCTIONS)) * factors[name]
    return values


# -- pass three: a sample -----------------------------------------------------------------


def sampled_inputs(model: Model) -> tuple[str, ...]:
    """Nodes that carry uncertainty of their own, in a stable order.

    Inputs with a declared distribution, and measured constants with a stated standard error.
    Those are the only two places randomness enters a model: everything else is arithmetic, which
    is the whole reason Monte Carlo over the inputs is the right tool for a definitional model (ch13)
    and not sufficient on its own for a conditional one.
    """
    names = []
    for name in sorted(model.nodes):
        node = model.nodes[name]
        if (
            isinstance(node, Input)
            and node.is_uncertain
            or isinstance(node, Measured)
            and node.is_measured
            and node.sd > 0
        ):
            names.append(name)
    return tuple(names)


@dataclass(frozen=True)
class Evaluation:
    model: Model
    scenario: Scenario
    point: dict[str, float]
    samples: dict[str, np.ndarray]
    factors: dict[str, float] = field(default_factory=dict)
    summaries: dict[str, dict] = field(default_factory=dict)
    histograms: dict[str, dict] = field(default_factory=dict)
    ceilings: dict[str, dict] = field(default_factory=dict)
    blocked: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def sampled(self) -> tuple[str, ...]:
        return tuple(sorted(self.samples))


def evaluate(model: Model, scenario: Scenario) -> Evaluation:
    """Work the model out at a point and across its uncertainty, in one pass each."""
    factors = conversion_factors(model)
    blocked = model.blocked()
    values = point(model, scenario, factors)
    generator = mc.rng(scenario.seed)
    n = scenario.samples

    # Draw the uncertain inputs, then correlate them. Correlation happens once, over a matrix of
    # every sampled input at once, because a pairwise fix applied one pair at a time would undo
    # the previous one. An input a scenario has pinned is not drawn: pinning it is the modeller
    # saying they want to see this model with that question closed.
    uncertain = [
        name
        for name in sampled_inputs(model)
        if name not in blocked and name not in scenario.overrides
    ]
    columns = []
    for name in uncertain:
        node = model.nodes[name]
        if isinstance(node, Input):
            columns.append(mc.sample(node.distribution, n, generator))  # type: ignore[arg-type]
        else:
            assert isinstance(node, Measured)
            columns.append(
                mc.normal_ppf_scaled(generator.random(n), float(node.value), node.sd)  # type: ignore[arg-type]
            )
    if columns:
        matrix = np.column_stack(columns)
        # A correlation between two inputs only means something while both are drawn. Pin one
        # -- a scenario override, or a slider a reader has fixed -- and it has no variation left
        # to share, so the pair is dropped rather than refused. Without this, fixing the growth
        # rate raised an error from the correlation it is declared in, and nothing in the book
        # had ever pinned a correlated input to find out.
        drawn_names = set(uncertain)
        live = [c for c in model.correlations if c["a"] in drawn_names and c["b"] in drawn_names]
        if live:
            matrix = mc.correlate(matrix, mc.correlation_matrix(uncertain, live), generator)
        drawn = {name: matrix[:, i] for i, name in enumerate(uncertain)}
    else:
        drawn = {}

    # Propagate. A node with no uncertainty upstream of it stays a scalar and broadcasts, so a
    # sixty-node model costs memory in proportion to how uncertain it is rather than how big.
    samples: dict[str, Any] = {}
    for name in model.order:
        if name in blocked:
            continue
        node = model.nodes[name]
        if name in drawn:
            samples[name] = drawn[name]
        elif isinstance(node, Derived):
            samples[name] = _walk(node.formula, samples, ARRAY_FUNCTIONS) * factors[name]
        elif isinstance(node, Ceiling):
            samples[name] = _walk(node.of, samples, ARRAY_FUNCTIONS) * factors[name]
        else:
            samples[name] = values[name]

    varying = {
        name: np.asarray(value, dtype=float)
        for name, value in samples.items()
        if isinstance(value, np.ndarray) and np.asarray(value).ndim == 1
    }

    return Evaluation(
        model=model,
        scenario=scenario,
        point=values,
        samples=varying,
        factors=factors,
        summaries={name: mc.summarise(v) for name, v in varying.items()},
        histograms={name: mc.histogram(v) for name, v in varying.items()},
        ceilings=ceiling_report(model, values, varying, factors),
        blocked=blocked,
    )


def ceiling_report(
    model: Model,
    values: dict[str, float],
    samples: dict[str, np.ndarray],
    factors: dict[str, float],
) -> dict[str, dict]:
    """Where each ceiling sits, at the point and across the whole distribution.

    ``p_over_allowed`` is the number this book exists to produce. A sizing model's output is not
    "you need 47 nodes"; it is "at 47 nodes this ceiling is breached in eighteen per cent of the
    futures the model thinks are plausible". Only one of those is something a person can take
    responsibility for.
    """
    report: dict[str, dict] = {}
    for node in model.of_kind("ceiling"):
        assert isinstance(node, Ceiling)
        if node.name not in values:
            continue
        at_point = values[node.name]
        limit = float(_walk(node.limit, values, SCALAR_FUNCTIONS)) * factors.get(
            f"{node.name}.limit", 1.0
        )
        headroom = float(_walk(node.headroom, values, SCALAR_FUNCTIONS)) * factors.get(
            f"{node.name}.headroom", 1.0
        )
        allowed = limit * (1.0 - headroom)
        entry = {
            "value": at_point,
            "limit": limit,
            "limit_text": node.limit_text,
            "headroom": headroom,
            "headroom_text": node.headroom_text,
            "allowed": allowed,
            "because": node.because,
            "verdict": verdict(at_point, limit, allowed),
        }
        drawn = samples.get(node.name)
        if drawn is not None:
            entry["p_over_allowed"] = float(np.mean(drawn > allowed))
            entry["p_over_limit"] = float(np.mean(drawn > limit))
        report[node.name] = entry
    return report


def verdict(value: float, limit: float, allowed: float) -> str:
    """``ok``, ``inside headroom`` or ``over``.

    Three states rather than two, because the middle one is the whole argument of ch11. A design
    under the hard limit but inside the margin it declared has not failed — it has spent the
    reserve it was keeping for the failure it has not had yet.
    """
    if value > limit:
        return "over"
    if value > allowed:
        return "inside headroom"
    return "ok"


# -- sensitivity ---------------------------------------------------------------------------


def swing_of(model: Model, name: str) -> tuple[float, float] | None:
    """The low and high an input is swung between for a tornado.

    From the input's own distribution, so the bars compare like with like: each asks "how far
    does the output move across the middle eighty per cent of what this input could be", and an
    input nobody is uncertain about gets no bar rather than a misleadingly short one.
    """
    node = model.nodes[name]
    if isinstance(node, Input) and node.is_uncertain:
        shape, parameters = mc.one_shape(node.distribution)  # type: ignore[arg-type]
        low, high = mc.SHAPES[shape](np.array([TORNADO_LOW, TORNADO_HIGH]), **parameters)
        return float(low), float(high)
    if isinstance(node, Measured) and node.is_measured and node.sd > 0:
        return (
            float(node.value) - mc.Z90 * node.sd,  # type: ignore[operator]
            float(node.value) + mc.Z90 * node.sd,  # type: ignore[operator]
        )
    return None


def tornado(model: Model, scenario: Scenario, output: str) -> list[dict]:
    """How far one output moves when each uncertain input is swung on its own.

    One at a time, everything else held at its point value. That is a real limitation and ch18
    names it: an input whose effect only shows up in combination with another gets a short bar
    here and can still be the thing that sinks you. A tornado says which input is worth going and
    *measuring*; the sampled interval says what the model currently believes.
    """
    factors = conversion_factors(model)
    base = point(model, scenario, factors)
    if output not in base:
        return []
    blocked = model.blocked()
    bars = []
    for name in sampled_inputs(model):
        if name in blocked or name in scenario.overrides:
            continue
        swing = swing_of(model, name)
        if swing is None:
            continue
        low_value, high_value = (
            _output_with(model, scenario, name, setting, output, factors) for setting in swing
        )
        bars.append(
            {
                "node": name,
                "label": model.nodes[name].display,
                "kind": model.nodes[name].kind,
                "low_input": swing[0],
                "high_input": swing[1],
                "low": low_value,
                "high": high_value,
                "base": base[output],
                "span": abs(high_value - low_value),
            }
        )
    return sorted(bars, key=lambda bar: bar["span"], reverse=True)


def _output_with(
    model: Model,
    scenario: Scenario,
    name: str,
    setting: float,
    output: str,
    factors: dict[str, float],
) -> float:
    forced = replace(scenario, overrides={**scenario.overrides, name: setting})
    return point(model, forced, factors)[output]
