#!/usr/bin/env python3
"""Refuse to build a model this book would not defend.

    python3 scripts/verify-models.py                      # every model under models/
    python3 scripts/verify-models.py path/to/model.yaml   # a file of your own, wherever it is

Eight rules. The last one is the reason this script exists rather than being folded into the test
suite: it is where the book's central claim stops being a paragraph in the front matter and
becomes something the build enforces.

1. **Every formula typechecks.** Units are checked dimensionally, and each node's declared unit is
   compared with what its formula produces. A model that multiplies series by requests and calls
   the answer bytes does not build. Quantities in different units of one dimension may not meet
   in `+`, `-`, `min` or `max`, because the build converts a formula's result once, into the
   node's unit; `TB + TiB` will not typecheck. A plain number is not an amount of data: a node
   declared in bytes, or a ceiling limit in bytes, whose formula gives a plain number does not
   build.
2. **Every input declares a provenance kind and a source, and every correlation a reason.** Not
   "has a provenance field": a non-empty source string, from the three kinds. A number nobody
   will admit to is the commonest defect in a spreadsheet and the cheapest one to make
   impossible. Every input also declares who decides it: `decided:` is `you`, `outside` or
   `definition`. A correlation's `because` may not be empty: a coefficient with no reason cannot
   be argued with.
3. **A `fact` cites something.** The strongest provenance kind has to point at a stamped result,
   a file, a specification or a document. An assumption wearing a better label is worse than an
   assumption.
4. **Every measured node names a result**, and that result either exists and is current, or the
   node is reported as not yet measured. Never filled in.
5. **A measured constant states its uncertainty.** A standard error of zero is a claim to have
   measured something exactly, and almost nothing is.
6. **Every ceiling declares a headroom and a reason.** A limit with no margin is not a sizing
   rule, and a margin with no reason cannot be argued with — which means it will be copied into
   the next model by somebody who does not know what it was for.
7. **The graph is acyclic and every node is reachable from an output.** An unreachable node is
   either a mistake or a leftover, and both are worth a sentence.
8. **The classification is honest.** A model with a `measured` node or a `ceiling` in it is a
   conditional model, and a conditional model must declare headroom on every ceiling it has. A
   model with neither is a definitional model, and is allowed to be simple — because for it,
   sampling the inputs really is enough. That is the distinction ch01 is built on, and this is
   where the repository holds itself to it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.stamp import RESULTS_DIR, code_fingerprint, load_result, shown  # noqa: E402
from sizing import mc  # noqa: E402
from sizing.dsl import (  # noqa: E402
    DECIDED_BY,
    PROVENANCE_KINDS,
    Ceiling,
    Input,
    Measured,
    Model,
    ModelError,
    Scenario,
    discover,
    load_model,
    scenarios_for,
)
from sizing.evaluate import check_units, evaluate  # noqa: E402

#: A `fact` has to point at something. Any of these in the source string counts as pointing.
CITATION_MARKERS = ("bench/results/", ".json", ".yaml", "definition", "invoice", "@", "http")


def _shown(model: Model) -> str:
    """A model as a reader should see it, or its name if it came from nowhere on disk."""
    return model.name if model.path is None else shown(model.path)


def check_model(model: Model, problems: list[str]) -> None:
    where = _shown(model)

    # 1 — units
    unit_problems, _ = check_units(model)
    problems += [f"{where}: {line}" for line in unit_problems]

    for name in sorted(model.nodes):
        node = model.nodes[name]

        # 2, 3 — provenance
        if isinstance(node, Input):
            # Who settles this one. The model cannot infer it: the nearest signal is whether the
            # input was given a shape, and ch02 is a whole section on how poor a proxy that is.
            # Left to the inference, a model files the records its users uploaded as somebody's
            # choice, and a year in seconds as one too.
            if node.decided not in DECIDED_BY:
                problems.append(
                    f"{where}: input {name!r} declares decided {node.decided!r}; expected one of "
                    f"{', '.join(DECIDED_BY)}. `you` is a choice somebody could make "
                    f"differently, `outside` is an observation whether or not it has a shape yet, "
                    f"and `definition` is an identity like a year in seconds."
                )
            provenance = node.provenance
            if provenance is None or provenance.kind not in PROVENANCE_KINDS:
                problems.append(
                    f"{where}: input {name!r} declares provenance kind "
                    f"{getattr(provenance, 'kind', None)!r}; expected one of "
                    f"{', '.join(PROVENANCE_KINDS)}"
                )
            elif not provenance.source.strip():
                problems.append(
                    f"{where}: input {name!r} has an empty provenance source. Every number in a "
                    "model says where it came from, including the ones somebody decided."
                )
            elif node.is_uncertain and not any(
                shape in provenance.source.lower() for shape in mc.SHAPES
            ):
                shape, _ = mc.one_shape(node.distribution)
                problems.append(
                    f"{where}: input {name!r} is sampled as a {shape} and its provenance never "
                    f"says so. The shape is a claim about what can happen — that a price cannot "
                    f"go negative, that a count has a hard maximum — and it is the claim a "
                    f"reviewer should argue with first. Name it in the source and say why (ch13, "
                    "appendix C)."
                )
            elif provenance.kind == "fact" and not any(
                marker in provenance.source for marker in CITATION_MARKERS
            ):
                problems.append(
                    f"{where}: input {name!r} is declared a `fact` but its source cites nothing: "
                    f"{provenance.source!r}. A fact points at a stamped result, a file, a "
                    "specification or a document; anything else is an assumption with a better "
                    "label on it."
                )

        # 4, 5 — measured constants
        if isinstance(node, Measured):
            if not node.result.strip():
                problems.append(f"{where}: measured node {name!r} names no result file")
            elif node.is_measured:
                payload = load_result(node.result)
                if "value" not in payload.get("summary", {}):
                    problems.append(
                        f"{where}: {node.result}.json has no `summary.value`, so node {name!r} "
                        "has nothing to read"
                    )
                elif node.sd <= 0:
                    problems.append(
                        f"{where}: measured node {name!r} reports a standard error of "
                        f"{node.sd}. A constant measured exactly is a claim; if the runner really "
                        "cannot estimate one, say so in `conditions` and set it deliberately."
                    )
                unit = payload.get("units", {}).get("value")
                if unit and unit != node.unit:
                    problems.append(
                        f"{where}: node {name!r} declares {node.unit!r} but "
                        f"{node.result}.json measured {unit!r}"
                    )

        # 6 — ceilings
        if isinstance(node, Ceiling):
            if not node.declares_headroom:
                problems.append(
                    f"{where}: ceiling {name!r} declares no headroom. A limit with no margin is "
                    "not a sizing rule — see ch11, and ch01's distinction between a definitional "
                    "model and a conditional one."
                )
            if not node.because.strip():
                problems.append(
                    f"{where}: ceiling {name!r} gives no reason. A margin nobody can argue with "
                    "gets copied into the next model by somebody who does not know what it was "
                    "for."
                )

    # 2 (continued) — a pair of inputs said to move together gives its reason too
    for pair in model.correlations:
        if not str(pair.get("because") or "").strip():
            problems.append(
                f"{where}: the correlation between {pair.get('a')!r} and {pair.get('b')!r} gives "
                "no reason. A coefficient with no reason cannot be argued with, and the next "
                "person to copy it does not know what it was for."
            )

    # 7 — shape
    reachable: set[str] = set()
    for output in model.outputs:
        reachable |= {output} | model.ancestors(output)
    for orphan in sorted(set(model.nodes) - reachable):
        problems.append(
            f"{where}: node {orphan!r} feeds no output. Either it is a leftover, or an output is "
            "missing from the model's `outputs:` list."
        )
    if not model.outputs:
        problems.append(f"{where}: declares no outputs, so nothing in it can be checked")

    # 8 — the distinction
    ceilings = model.of_kind("ceiling")
    if model.is_conditional:
        if not ceilings:
            problems.append(
                f"{where}: has measured constants but no ceiling. A model with empirical inputs "
                "and no declared limit is claiming that nothing in it changes regime — which may "
                "be true, and should be stated by declaring the ceiling and its headroom rather "
                "than by leaving it out."
            )
    elif ceilings:  # pragma: no cover - unreachable by construction, kept as a tripwire
        problems.append(f"{where}: classified as a definitional model but declares ceilings")


def check_scenarios(model: Model, problems: list[str]) -> None:
    """Every scenario evaluates, and every override names a real input."""
    where = _shown(model)
    for scenario in scenarios_for(model):
        for name in sorted(scenario.overrides):
            if name not in model.nodes:
                problems.append(
                    f"{where}: scenario {scenario.name!r} overrides {name!r}, which is not a node"
                )
            elif model.nodes[name].kind == "derived":
                problems.append(
                    f"{where}: scenario {scenario.name!r} overrides {name!r}, which is derived. "
                    "Pin the inputs it comes from instead, or the graph and the number disagree."
                )
        try:
            evaluate(model, scenario)
        except Exception as exc:
            problems.append(f"{where}: scenario {scenario.name!r} does not evaluate — {exc}")


def check_stamps(problems: list[str]) -> None:
    """Every model result was produced by the code and the model file that are checked in."""
    for path in sorted(RESULTS_DIR.glob("*.json")):
        payload = load_result(path.stem)
        if payload.get("kind") != "model":
            continue
        try:
            expected = code_fingerprint(
                payload.get("code_sources"), payload.get("target"), payload.get("kind")
            )
        except FileNotFoundError as exc:
            problems.append(f"{path.name} names a source that no longer exists: {exc}")
            continue
        if payload.get("code_fingerprint") != expected:
            problems.append(
                f"{path.name} was produced by different code or a different model file than is "
                f"checked in (stamped {payload.get('code_fingerprint')}, now {expected}). "
                "Re-run `python3 -m bench.run_models`."
            )


def check_file(path: str | Path) -> tuple[Model | None, list[str]]:
    """One model file, wherever it is: every rule above, and its scenarios if it has any.

    A file that will not load at all -- a YAML error, a formula naming a node the file does not
    define -- is one problem rather than a traceback, so a file of the reader's own is answered
    the way the book's are. The stamps are not checked: they belong to the repository, not to the
    file. The browser's model checker calls this too, so the page and the desk give one verdict.
    """
    try:
        model = load_model(path)
    except ModelError as exc:
        return None, [str(exc)]
    except yaml.YAMLError as exc:
        return None, [f"{shown(path)}: is not valid YAML. {exc}"]
    except OSError as exc:
        return None, [f"{shown(path)}: cannot be opened ({exc.strerror})"]
    problems: list[str] = []
    check_model(model, problems)
    check_scenarios(model, problems)
    return model, problems


def what_it_says(model: Model) -> list[dict]:
    """Each output under each of the file's scenarios: the point value, and the 5th and 95th.

    A file with no scenarios is worked out as written, with nothing overridden. Sampled with the
    seed and the number of draws every model in the book uses, so the same file gives the same
    answer on every machine.
    """
    scenarios = scenarios_for(model) or (Scenario(name="as written", title="as written"),)
    out = []
    for scenario in scenarios:
        evaluation = evaluate(model, scenario)
        for name in model.outputs:
            summary = evaluation.summaries.get(name, {})
            out.append(
                {
                    "scenario": scenario.name,
                    "name": name,
                    "unit": model.nodes[name].unit,
                    "point": evaluation.point.get(name),
                    "p5": summary.get("p5"),
                    "p95": summary.get("p95"),
                    "waits_on": list(evaluation.blocked.get(name, ())),
                }
            )
    return out


def check_files(paths: list[str]) -> int:
    """The verifier pointed at files of your own, and what each one says when it passes."""
    from bench.tables import fmt, unit_label

    checked = [(path, *check_file(path)) for path in paths]
    problems = [problem for _path, _model, found in checked for problem in found]
    if problems:
        print("verify-models: FAILED")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    for path, model, _ in checked:
        assert model is not None
        print(f"{shown(path)}: {len(model.nodes)} nodes, {model.classification} model")
        for row in what_it_says(model):
            unit = unit_label(row["unit"])
            name = f"{row['name']} ({unit})" if unit else row["name"]
            if row["waits_on"]:
                said = f"not yet measured: waits on {', '.join(row['waits_on'])}"
            else:
                said = fmt(row["point"], row["unit"])
                if row["p5"] is not None:
                    said += f", 5th to 95th {fmt(row['p5'], row['unit'])} to "
                    said += fmt(row["p95"], row["unit"])
            print(f"  {row['scenario']}: {name} = {said}")
    print(f"\nverify-models: OK ({len(checked)} file(s))")
    return 0


def main() -> int:
    if len(sys.argv) > 1:
        return check_files(sys.argv[1:])
    problems: list[str] = []
    models = discover()
    if not models:
        print("verify-models: no models found under models/*/model.yaml")
        return 1
    for model in models:
        check_model(model, problems)
        check_scenarios(model, problems)
    check_stamps(problems)

    if problems:
        print("verify-models: FAILED")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    for model in models:
        missing = (
            f", {len(model.unmeasured)} constant(s) not yet measured" if model.unmeasured else ""
        )
        print(
            f"  {model.name}: {len(model.nodes)} nodes, {model.classification} model, "
            f"{len(model.of_kind('ceiling'))} ceiling(s){missing}"
        )
    print(f"\nverify-models: OK ({len(models)} model(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
