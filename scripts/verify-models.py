#!/usr/bin/env python3
"""Refuse to build a model this book would not defend.

Eight rules. The last one is the reason this script exists rather than being folded into the test
suite: it is where the book's central claim stops being a paragraph in the front matter and
becomes something the build enforces.

1. **Every formula typechecks.** Units are checked dimensionally and each node's declared unit is
   compared against what its formula actually produces. A model that multiplies series by
   requests and calls the answer bytes does not build.
2. **Every input declares a provenance kind and a source.** Not "has a provenance field" — a
   non-empty source string, from the three kinds. A number nobody will admit to is the commonest
   defect in a spreadsheet and the cheapest one to make impossible.
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
   sizing model, and a sizing model must declare headroom on every ceiling it has. A model with
   neither is a cost model, and is allowed to be simple — because for it, sampling the inputs
   really is enough. That is the distinction the front matter is built on, and this is where the
   repository holds itself to it.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.stamp import RESULTS_DIR, code_fingerprint, load_result, shown  # noqa: E402
from sizing.dsl import (  # noqa: E402
    PROVENANCE_KINDS,
    Ceiling,
    Input,
    Measured,
    Model,
    discover,
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
                    "not a sizing rule — see ch11, and the front matter's distinction between a "
                    "cost model and a sizing one."
                )
            if not node.because.strip():
                problems.append(
                    f"{where}: ceiling {name!r} gives no reason. A margin nobody can argue with "
                    "gets copied into the next model by somebody who does not know what it was "
                    "for."
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
    if model.is_sizing_model:
        if not ceilings:
            problems.append(
                f"{where}: has measured constants but no ceiling. A model with empirical inputs "
                "and no declared limit is claiming that nothing in it changes regime — which may "
                "be true, and should be stated by declaring the ceiling and its headroom rather "
                "than by leaving it out."
            )
    elif ceilings:  # pragma: no cover - unreachable by construction, kept as a tripwire
        problems.append(f"{where}: classified as a cost model but declares ceilings")


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


def main() -> int:
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
