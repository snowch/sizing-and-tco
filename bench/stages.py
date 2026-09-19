"""A model as the book builds it, one chapter at a time.

The book does not hand a reader a finished model and explain it backwards. It starts with what
arrives and what accumulates, and adds nodes as the chapters earn them. Those intermediate models
are real: they load, they typecheck, they classify, and `make check` runs the same rules over them
that it runs over the finished file.

They are **derived** from the model rather than kept beside it. A second copy of a model is a copy
that drifts, and a book describing a model the repository no longer has is the failure this whole
repository exists to prevent. A model is staged by carrying a ``build-order.yaml`` next to its
``model.yaml``; the manifest says which chapter introduces which node, and everything else is
computed.

Any model may be staged, and more than one may be at once -- which is how the running example is
replaced without `main` ever describing half of one model and half of another. The chapters
embed and quote the stages of one model, named in ``bench.outline.RUNNING_EXAMPLE``; ``stages()``
returns those. Every staged model is built, stamped and held to the same rules, whichever one the
chapters are currently about.

Two nodes are not simply added. An input that is a single number until a later chapter gives it
a shape is declared under ``certain_until`` -- a value, and a provenance that says the
distribution is coming. That is the only kind of edit a stage may make to a node, because any
other would let a staged model say something the real one does not.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path

import yaml

from bench.outline import RUNNING_EXAMPLE, label_of
from sizing.dsl import MODELS_DIR

__all__ = [
    "Stage",
    "all_stages",
    "build",
    "label_of",
    "manifest_path",
    "model_path",
    "nodes_by",
    "out_dir",
    "staged_models",
    "stages",
    "write_all",
    "as_yaml",
]

#: The manifest a model carries to say it is built across chapters.
MANIFEST = "build-order.yaml"

#: Keys whose values a person reads and the toolkit never parses. Written as folded paragraphs
#: under their key when they are long, so that a stage file reads on a tablet without a line
#: ever wrapping: a wrapped continuation in a chapter's editable block is indistinguishable
#: from a key at the wrong level, which is how ch02's first model file came to look like nonsense.
PROSE_KEYS = frozenset({"title", "description", "source", "note", "because"})

#: Where prose folds. A tablet shows about eighty columns of the editable block; the fold sits
#: well inside that because the emitter breaks after the word that crosses it, not before.
WIDTH = 60


class Prose(str):
    """A string a person reads. ``StageDumper`` folds it when it is long."""


class StageDumper(yaml.SafeDumper):
    """Writes a stage the way a person would.

    PyYAML's defaults are made for machines: a long string is wrapped at the width with its
    continuation indented two spaces deeper, a list of two numbers takes three lines, and a
    formula longer than the width is broken across two. Here prose folds under its key, a short
    list is written inline, a long one is indented under its key, and nothing the toolkit parses
    is ever split -- a formula is one line however long, and scrolls rather than wraps.
    """

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

    def write_plain(self, text, split=True):
        super().write_plain(text, split=False)

    def write_single_quoted(self, text, split=True):
        super().write_single_quoted(text, split=False)

    def write_double_quoted(self, text, split=True):
        super().write_double_quoted(text, split=False)


def _represent_prose(dumper: yaml.SafeDumper, value: Prose):
    style = ">" if len(value) > WIDTH or "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(value), style=style)


def _represent_list(dumper: yaml.SafeDumper, value: list):
    scalars = all(isinstance(v, (int, float, str)) and not isinstance(v, bool) for v in value)
    inline = scalars and len(", ".join(str(v) for v in value)) <= WIDTH
    return dumper.represent_sequence("tag:yaml.org,2002:seq", value, flow_style=inline)


StageDumper.add_representer(Prose, _represent_prose)
StageDumper.add_representer(list, _represent_list)


def _prose_marked(value):
    """The same document with every prose value wrapped, so the dumper knows which to fold."""
    if isinstance(value, dict):
        return {
            key: Prose(field)
            if key in PROSE_KEYS and isinstance(field, str)
            else _prose_marked(field)
            for key, field in value.items()
        }
    if isinstance(value, list):
        return [_prose_marked(item) for item in value]
    return value


def as_yaml(document: dict) -> str:
    """A document as text, in the form a person would have written it. See ``StageDumper``."""
    return yaml.dump(
        _prose_marked(document),
        Dumper=StageDumper,
        sort_keys=False,
        width=WIDTH,
        allow_unicode=True,
    )


def model_path(model: str) -> Path:
    return MODELS_DIR / model / "model.yaml"


def manifest_path(model: str) -> Path:
    return MODELS_DIR / model / MANIFEST


def out_dir(model: str) -> Path:
    """Where a model's built stages land. Committed, like the generated figures in
    chapters/_generated: a reader following the book can open the file the chapter is quoting,
    and ``--check`` fails the build if what is committed is not what the manifest and the model
    now produce."""
    return MODELS_DIR / model / "stages"


def staged_models() -> tuple[str, ...]:
    """Every model that carries a manifest, by directory name, in a stable order."""
    return tuple(sorted(path.parent.name for path in MODELS_DIR.glob(f"*/{MANIFEST}")))


@dataclass(frozen=True)
class Stage:
    """One chapter's worth of one model."""

    model: str
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
        return f"{self.model}_{self.stage}"

    @property
    def is_the_finished_model(self) -> bool:
        """True for the stage that has every node in it.

        That stage is not an earlier version of anything -- it is the model. Writing it out would
        put a second copy of the model file in the repository, and stamping it would put a second
        copy of its reference result beside the first. Both are regenerated on every
        `make models`, and a duplicate that regenerates is a duplicate that eventually disagrees.
        """
        return set(nodes_by(self.model, self.index)) == set(_raw_model(self.model)["nodes"])

    @property
    def path(self) -> Path:
        """Where this stage's model file is -- which for the last one is the model itself."""
        if self.is_the_finished_model:
            return model_path(self.model)
        return out_dir(self.model) / f"{self.index:02d}-{self.stage}" / "model.yaml"


def _raw_model(model: str) -> dict:
    return yaml.safe_load(model_path(model).read_text())


def _manifest(model: str) -> dict:
    return yaml.safe_load(manifest_path(model).read_text())


def stages(model: str = RUNNING_EXAMPLE) -> tuple[Stage, ...]:
    """One model's manifest, in reading order. By default, the model the chapters are about.

    ``certain_until`` is declared once for the whole book and resolved here, so that a node whose
    shape arrives in ch04 cannot be held back in one stage and not the next.
    """
    spec = _manifest(model)
    held = spec.get("certain_until") or {}
    order = [one["stage"] for one in spec["stages"]]
    for name, pending in held.items():
        if pending["stage"] not in order:
            raise ValueError(
                f"{model}: certain_until[{name!r}] names stage {pending['stage']!r}, which is "
                f"not one of {order}"
            )

    built = []
    for i, one in enumerate(spec["stages"]):
        built.append(
            Stage(
                model=model,
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


def all_stages() -> tuple[Stage, ...]:
    """Every stage of every staged model. What gets built, stamped and checked."""
    return tuple(stage for model in staged_models() for stage in stages(model))


def nodes_by(model: str, index: int) -> tuple[str, ...]:
    """Every node the book has introduced by the end of stage ``index``, in the model's order."""
    introduced = {n for s in stages(model) if s.index <= index for n in s.introduces}
    return tuple(n for n in _raw_model(model)["nodes"] if n in introduced)


def build(stage: Stage) -> dict:
    """The stage as a model document, ready to be written out and loaded like any other."""
    raw = _raw_model(stage.model)
    keep = nodes_by(stage.model, stage.index)
    short = _manifest(stage.model).get("describe") or stage.model.replace("_", " ")

    nodes = {}
    for name in keep:
        spec = copy.deepcopy(raw["nodes"][name])
        pending = stage.certain_for_now.get(name)
        if pending is not None:
            # The one permitted edit: a node that is not uncertain yet. The value takes the
            # distribution's place, so the node reads in the same order as the finished one.
            placed = {}
            for key, field in spec.items():
                if key == "distribution":
                    placed["value"] = pending["value"]
                else:
                    placed[key] = field
            placed.setdefault("value", pending["value"])
            placed["provenance"] = {"kind": "assumption", "source": pending["source"]}
            spec = placed
        nodes[name] = spec

    return {
        "model": stage.name,
        "title": f"{raw['title']} — {stage.title}",
        "currency": raw["currency"],
        "description": f"The {short} as it stands at the end of {label_of(stage.chapter)}.",
        "nodes": nodes,
        "outputs": list(stage.outputs),
        # A correlation is a statement about two quantities that vary. An input the stage has
        # not introduced is not there to correlate, and one it is still holding certain does
        # not vary, so neither can carry one yet. The pairs the finished model declares are
        # ch14's subject in any case.
        "correlations": [
            c
            for c in raw.get("correlations", [])
            if {c["a"], c["b"]} <= set(nodes) and not {c["a"], c["b"]} & set(stage.certain_for_now)
        ],
    }


#: Every stage runs under the same conditions as the finished model, so that a figure drawn from
#: a stage and a figure drawn from the whole thing are comparable. The scenario overrides nothing,
#: exactly as a model's own `scenarios/reference.yaml` does.
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
        f"# Generated by bench/stages.py from models/{stage.model}/model.yaml.\n"
        f"# The finished model with everything the book has not introduced by the end\n"
        f"# of {label_of(stage.chapter)} removed, so that a reader can see it at {nodes} nodes. "
        f"Not a model\n"
        f"# anybody would ship. Do not edit: say which chapter introduces a node in\n"
        f"# build-order.yaml instead.\n"
    )


def generated_short(model: str) -> str:
    """Scenario files carry no node count, so they keep the short form."""
    return (
        f"# Generated by bench/stages.py from models/{model}/model.yaml.\n"
        "# Do not edit: say which chapter introduces the node in build-order.yaml instead.\n"
    )


def _document(stage: Stage) -> str:
    document = build(stage)
    return generated_header(stage, len(document["nodes"])) + as_yaml(document)


def write_all(model: str | None = None) -> tuple[Path, ...]:
    """Write every stage and its scenario -- of one model, or of all of them -- and say where."""
    written = []
    for stage in stages(model) if model else all_stages():
        if stage.is_the_finished_model:
            continue
        stage.path.parent.mkdir(parents=True, exist_ok=True)
        stage.path.write_text(_document(stage))
        scenarios = stage.path.parent / "scenarios"
        scenarios.mkdir(exist_ok=True)
        (scenarios / "reference.yaml").write_text(
            generated_short(stage.model) + as_yaml(REFERENCE_SCENARIO)
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
    for stage in all_stages():
        if stage.is_the_finished_model:
            continue
        if not stage.path.exists() or stage.path.read_text() != _document(stage):
            stale.append(str(stage.path.relative_to(MODELS_DIR.parent)))
    if stale:
        print("stages: STALE — the committed stage models are not what the manifest now builds:")
        for one in stale:
            print(f"  {one}")
        print("Run `python3 -m bench.stages` and commit what changes.")
        return 1
    models = ", ".join(staged_models())
    print(f"stages: OK ({len(all_stages())} stage(s) across {models})")
    return 0


if __name__ == "__main__":  # pragma: no cover - a thin wrapper around main()
    raise SystemExit(main())
