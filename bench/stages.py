"""The storage model as the book builds it, one chapter at a time.

The book does not hand a reader a finished model and explain it backwards. It starts with what
arrives and what accumulates, and adds nodes as the chapters earn them. Those intermediate models
are real: they load, they typecheck, they classify, and `make check` runs the same rules over them
that it runs over the finished file.

They are **derived** from ``models/storage_cluster/model.yaml`` rather than kept beside it. A
second copy of a model is a copy that drifts, and a book describing a model the repository no
longer has is the failure this whole repository exists to prevent. ``build-order.yaml`` says which
chapter introduces which node, and everything else is computed.

Two nodes are not simply added. The growth rate and the peak read throughput are single numbers
until ch03 gives them shapes, so an earlier stage declares them under ``certain_until`` — a value,
and a provenance that says the distribution is coming. That is the only kind of edit a stage may
make to a node, because any other would let a staged model say something the real one does not.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path

import yaml

from sizing.dsl import MODELS_DIR

MODEL_PATH = MODELS_DIR / "storage_cluster" / "model.yaml"
STAGES_PATH = MODELS_DIR / "storage_cluster" / "build-order.yaml"

#: Where the built stages land. Committed, like the generated figures in chapters/_generated:
#: a reader following the book can open the file the chapter is quoting, and `--check` fails
#: the build if what is committed is not what the manifest and the model now produce.
OUT_DIR = MODELS_DIR / "storage_cluster" / "stages"


@dataclass(frozen=True)
class Stage:
    """One chapter's worth of model."""

    index: int
    stage: str
    chapter: str
    title: str
    classification: str
    outputs: tuple[str, ...]
    introduces: tuple[str, ...]
    certain_for_now: dict[str, dict]

    @property
    def name(self) -> str:
        return f"storage_cluster_{self.stage}"

    @property
    def is_the_finished_model(self) -> bool:
        """True for the stage that has every node in it.

        That stage is not an earlier version of anything — it is the model. Writing it out would
        put a second copy of `models/storage_cluster/model.yaml` in the repository, and stamping
        it would put a second copy of `storage_cluster-reference.json` beside the first. Both are
        regenerated on every `make models`, and a duplicate that regenerates is a duplicate that
        eventually disagrees.
        """
        return set(nodes_by(self.index)) == set(_raw_model()["nodes"])

    @property
    def path(self) -> Path:
        """Where this stage's model file is — which for the last one is the model itself."""
        if self.is_the_finished_model:
            return MODEL_PATH
        return OUT_DIR / f"{self.index:02d}-{self.stage}" / "model.yaml"


def _raw_model() -> dict:
    return yaml.safe_load(MODEL_PATH.read_text())


def stages() -> tuple[Stage, ...]:
    """The manifest, in reading order.

    ``certain_until`` is declared once for the whole book and resolved here, so that a node whose
    shape arrives in ch03 cannot be held back in one stage and not the next.
    """
    spec = yaml.safe_load(STAGES_PATH.read_text())
    held = spec.get("certain_until") or {}
    order = [one["stage"] for one in spec["stages"]]
    for name, pending in held.items():
        if pending["stage"] not in order:
            raise ValueError(
                f"certain_until[{name!r}] names stage {pending['stage']!r}, which is "
                f"not one of {order}"
            )

    built = []
    for i, one in enumerate(spec["stages"]):
        built.append(
            Stage(
                index=i + 1,
                stage=one["stage"],
                chapter=one["chapter"],
                title=one["title"],
                classification=one["classification"],
                outputs=tuple(one["outputs"]),
                introduces=tuple(one.get("introduces") or ()),
                certain_for_now={
                    name: pending
                    for name, pending in held.items()
                    if order.index(one["stage"]) < order.index(pending["stage"])
                },
            )
        )
    return tuple(built)


def nodes_by(index: int) -> tuple[str, ...]:
    """Every node the book has introduced by the end of stage ``index``, in the model's order."""
    introduced = {n for s in stages() if s.index <= index for n in s.introduces}
    return tuple(n for n in _raw_model()["nodes"] if n in introduced)


def build(stage: Stage) -> dict:
    """The stage as a model document, ready to be written out and loaded like any other."""
    raw = _raw_model()
    keep = nodes_by(stage.index)

    nodes = {}
    for name in keep:
        spec = copy.deepcopy(raw["nodes"][name])
        pending = stage.certain_for_now.get(name)
        if pending is not None:
            # The one permitted edit: a node that is not uncertain yet.
            spec.pop("distribution", None)
            spec["value"] = pending["value"]
            spec["provenance"] = {"kind": "assumption", "source": pending["source"]}
        nodes[name] = spec

    return {
        "model": stage.name,
        "title": f"{raw['title']} — {stage.title}",
        "currency": raw["currency"],
        "description": f"The storage model as it stands at the end of {label_of(stage.chapter)}.",
        "nodes": nodes,
        "outputs": list(stage.outputs),
        # A correlation is a statement about two quantities that vary. An input the stage has
        # not introduced is not there to correlate, and one it is still holding certain does
        # not vary, so neither can carry one yet. The pairs the finished model declares are
        # ch13's subject in any case.
        "correlations": [
            c
            for c in raw.get("correlations", [])
            if {c["a"], c["b"]} <= set(nodes) and not {c["a"], c["b"]} & set(stage.certain_for_now)
        ],
    }


#: Every stage runs under the same conditions as the finished model, so that a figure drawn from
#: a stage and a figure drawn from the whole thing are comparable. The scenario overrides nothing,
#: exactly as `models/storage_cluster/scenarios/reference.yaml` does.
REFERENCE_SCENARIO = {
    "scenario": "reference",
    "title": "Reference scenario",
    "because": (
        "The same conditions the finished model is quoted under, so that a number from a stage "
        "and a number from the whole model differ only by what the stage does not contain yet."
    ),
    "samples": 100000,
    "seed": 20260916,
    "overrides": {},
}


def generated_header(stage: Stage, nodes: int) -> str:
    """The comment at the top of a stage file.

    The caveat lives here rather than in ``description`` because ``description`` is the first
    thing in the document, and a reader meeting their first model file should not open on four
    lines about the build that produced it. What they need to know about the file is a comment;
    what the viewer needs is one line.
    """
    return (
        f"# Generated by bench/stages.py from models/storage_cluster/model.yaml.\n"
        f"# The finished model with everything the book has not introduced by the end of "
        f"{label_of(stage.chapter)} removed,\n"
        f"# so that a reader can see it at {nodes} nodes. Not a model anybody would ship.\n"
        f"# Do not edit: say which chapter introduces a node in build-order.yaml instead.\n"
    )


def label_of(slug: str) -> str:
    """A chapter's number as a reader sees it, from the outline rather than typed."""
    from bench.outline import CHAPTERS

    return next(c.label for c in CHAPTERS if c.slug == slug)


#: Scenario files carry no node count, so they keep the short form.
GENERATED = (
    "# Generated by bench/stages.py from models/storage_cluster/model.yaml.\n"
    "# Do not edit: say which chapter introduces the node in build-order.yaml instead.\n"
)


def write_all() -> tuple[Path, ...]:
    """Write every stage and its scenario, and return where the models landed."""
    written = []
    for stage in stages():
        if stage.is_the_finished_model:
            continue
        stage.path.parent.mkdir(parents=True, exist_ok=True)
        document = build(stage)
        stage.path.write_text(
            generated_header(stage, len(document["nodes"]))
            + yaml.safe_dump(document, sort_keys=False, width=98, allow_unicode=True)
        )
        scenarios = stage.path.parent / "scenarios"
        scenarios.mkdir(exist_ok=True)
        (scenarios / "reference.yaml").write_text(
            GENERATED + yaml.safe_dump(REFERENCE_SCENARIO, sort_keys=False, width=98)
        )
        written.append(stage.path)
    return tuple(written)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if what is committed is out of date"
    )
    args = parser.parse_args()

    if not args.check:
        for path in write_all():
            print(f"  wrote {path.relative_to(MODELS_DIR.parent)}")
        return 0

    stale = []
    for stage in stages():
        if stage.is_the_finished_model:
            continue
        document = build(stage)
        want = generated_header(stage, len(document["nodes"])) + yaml.safe_dump(
            document, sort_keys=False, width=98, allow_unicode=True
        )
        if not stage.path.exists() or stage.path.read_text() != want:
            stale.append(str(stage.path.relative_to(MODELS_DIR.parent)))
    if stale:
        print("stages: STALE — the committed stage models are not what the manifest now builds:")
        for one in stale:
            print(f"  {one}")
        print("Run `python3 -m bench.stages` and commit what changes.")
        return 1
    print(f"stages: OK ({len(stages())} stage(s))")
    return 0


if __name__ == "__main__":  # pragma: no cover - a thin wrapper around main()
    raise SystemExit(main())
