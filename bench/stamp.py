"""What a number has to carry before this book is allowed to print it.

The book's claim is that every figure in it can be traced to something that was run. That claim
is worth exactly as much as its weakest number, so every file under ``bench/results/`` records:

* **which target** produced it — ``corpus`` or ``rig``;
* **what** produced it: the corpus and codec, or the machine and kernel;
* **a content hash of the code that produced it**, so editing that code invalidates the number
  rather than quietly contradicting it;
* **the units of every figure in its summary**, which is how the rules below can be dimensional
  checks rather than guesses about what a key name means.

``scripts/verify-numbers.py`` checks all of it on every file and fails CI when one is missing,
stale, or recorded somewhere it should not have been.

## The two targets, and the one rule that separates them

The distinction this book rests on is the same one *Systems From Scratch* makes between an
emulator and real silicon, and it exists for the same reason: two questions that look alike and
are not.

**A ``corpus`` result answers a question about data and code.** How many bytes a codec makes of a
declared body of samples; how many spans a declared trace corpus carries per request. Nothing
about the machine enters into it, so CI re-derives every one of them on every push and fails if
one has moved. In exchange, a ``corpus`` result **may not carry a figure with time in its
units** — no rate, no duration, no throughput. Compression ratio is a property of the codec and
the data. How fast the codec ran is a property of the computer that ran it, and the two must not
arrive in the same file wearing the same stamp.

**A ``rig`` result answers a question about a machine.** Collector throughput per core, query
scan rate, rebuild rate. These cannot be taken in CI and this module refuses to let them be:
:func:`classify_machine` compares the running machine against ``rig/machine.yml`` and says
``other`` unless it matches, and ``make bench-rig`` will not start anywhere else.

If you find yourself wanting to relax that: a throughput measured on a shared CI runner is
indistinguishable from a real one once it is a number in a table, which is the entire reason the
check exists.

## A third kind of file

Most results are a ``measurement``. A ``model`` result is different in kind: it is the stamped
output of evaluating and sampling a model file (:mod:`sizing.evaluate`), and it is how a figure
that is *computed* rather than measured still gets to say where it came from. It records the
model, the scenario, the seed, the sample count, and a fingerprint over the DSL core — so a
change to the sampler invalidates every published interval, which is the intended behaviour and
the reason :data:`KIND_SOURCES` exists.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from sizing.units import UnitError, has_time

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "bench" / "results"
RIG_DECLARATION = ROOT / "rig" / "machine.yml"

#: The four targets, and what declaring one means.
#:
#: Three of them are measurements — something outside this repository was asked a question. The
#: fourth is not, and separating it out is what stops the distinction going soft. A sweep of a
#: model is arithmetic over numbers the book already had; it is not evidence about the world, and
#: a file that recorded it as though it were would be claiming something it cannot support.
TARGETS = ("corpus", "rig", "estate", "model")

TARGET_MEANING = {
    "corpus": "a deterministic measurement over a declared corpus with a named codec; "
    "reproducible anywhere, re-derived by CI, and never a rate or a duration",
    "rig": "a throughput or latency figure measured natively on the declared reference machine, "
    "and refused anywhere else",
    "estate": "an observation of a real deployment over a stated window; reproducible by nobody, "
    "checkable by nobody, and therefore held to the strictest disclosure rules in the book",
    "model": "computed from a model file in this repository. No machine and no body of data was "
    "involved, so it is evidence about what the book's own models say and about nothing else — "
    "and its fingerprint covers the whole DSL core, so the claim moves when the method does",
}

#: What a file *is*. A ``measurement`` was run against data or a machine; a ``model`` is the
#: stamped output of a model file the build evaluated.
KINDS = ("measurement", "model")

#: Stamps every result must carry. A number missing any of them cannot be checked by anyone,
#: including its author six months later.
REQUIRED_STAMPS = (
    "name",
    "target",
    "kind",
    "generated_at",
    "produced_by",
    "code_fingerprint",
    "code_sources",
    "summary",
    "units",
)

#: Files that can change any measured number, whichever runner produced it.
#:
#: Deliberately short, and ``stamp.py`` is deliberately not in it: this module writes JSON and
#: hashes bytes, and cannot move a measurement, so listing it here would invalidate every result
#: in the book each time a docstring changed.
CORE_SOURCES: tuple[str, ...] = ("bench/measure.py",)

#: Sources core to one *target* only. The timing harness belongs here when there is one, so that
#: touching it churns the rig results and leaves the corpus results alone.
TARGET_SOURCES: dict[str, tuple[str, ...]] = {"rig": ()}

#: Sources core to one *kind* only — and the most important entry in this module.
#:
#: A ``model`` result's fingerprint covers the whole DSL core, so changing how the book samples,
#: evaluates or checks units invalidates every interval it has published. A ``measurement``'s
#: does not, because a compression ratio does not depend on how the book draws random numbers.
#: Putting the sampler in :data:`CORE_SOURCES` instead would churn every corpus measurement on
#: every edit to ``mc.py``, and a re-stamp people perform without reading what moved is worse
#: than no check at all.
KIND_SOURCES: dict[str, tuple[str, ...]] = {
    "model": (
        "sizing/dsl.py",
        "sizing/evaluate.py",
        "sizing/mc.py",
        "sizing/normal.py",
        "sizing/units.py",
    )
}


class StaleFingerprintError(RuntimeError):
    """A result was produced by code that is no longer what is checked in."""


class WrongMachineError(RuntimeError):
    """A rig measurement was attempted somewhere that is not the rig."""


# -- the code hash -----------------------------------------------------------------------


def code_fingerprint(
    sources: str | list[str] | tuple[str, ...] | None = None,
    target: str | None = None,
    kind: str | None = None,
) -> str:
    """Hash the sources a result depends on.

    :data:`CORE_SOURCES`, plus whatever is core to this target and this kind, plus the runner's
    own. Content, not modification time: comparing timestamps cannot tell an unrelated new file
    from a change to the thing being measured, and is wrong in both directions.
    """
    if sources is None:
        sources = ()
    elif isinstance(sources, str):
        sources = (sources,)

    everything = sorted(
        {
            *CORE_SOURCES,
            *TARGET_SOURCES.get(target or "", ()),
            *KIND_SOURCES.get(kind or "", ()),
            *sources,
        }
    )
    digest = hashlib.sha256()
    for relative in everything:
        path = ROOT / relative
        if not path.exists():
            raise FileNotFoundError(relative)
        digest.update(relative.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


# -- which machine is this -----------------------------------------------------------------


def _cpu_model() -> str:
    """The processor's own name for itself, or the platform's best guess."""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            for key in ("model name", "Model", "Hardware"):
                if line.startswith(key):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def rig_declaration() -> dict | None:
    """What the reference machine is declared to be, or None if the book has not declared one.

    A file rather than an environment variable, deliberately. ``RIG=1 make bench-rig`` would let
    anybody stamp a laptop timing as a reference measurement by typing four characters, and the
    whole point of the rig target is that it cannot be done by accident.
    """
    if not RIG_DECLARATION.exists():
        return None
    return yaml.safe_load(RIG_DECLARATION.read_text())


def classify_machine() -> str:
    """``rig`` if this is the declared reference machine, ``other`` if it is anything else.

    Matched on the processor's own model string and its core count, both of which are properties
    of the silicon rather than of how the machine was booted. A partial match is not a match: a
    rig figure taken on a machine with half the cores is a different number.
    """
    declared = rig_declaration()
    if not declared:
        return "other"
    machine = declared.get("machine", {})
    wanted_cpu = str(machine.get("cpu_model", "")).strip()
    wanted_cores = machine.get("cores")
    if not wanted_cpu or wanted_cores is None:
        return "other"
    import os

    if _cpu_model() != wanted_cpu or os.cpu_count() != int(wanted_cores):
        return "other"
    return "rig"


def require_rig() -> dict:
    """Refuse to take a rig measurement anywhere but the rig."""
    declared = rig_declaration()
    if classify_machine() != "rig":
        expected = "no reference machine is declared (rig/machine.yml is missing)"
        if declared:
            machine = declared.get("machine", {})
            expected = f"the declared rig is {machine.get('cpu_model')!r} with {machine.get('cores')} cores"
        raise WrongMachineError(
            f"Refusing to measure: this is not the reference machine. {expected}; this machine is "
            f"{_cpu_model()!r}. A throughput taken on the wrong computer is indistinguishable from "
            "a real one once it is a number in a table, which is why this check exists (ch02)."
        )
    return declared or {}


def recorded_on() -> dict:
    """Where this file was written, whatever it is a measurement of.

    Separate from what the result is *about*. A corpus measurement is about a codec and is valid
    anywhere, and it is still worth knowing which machine and which interpreter produced the file
    — that is how a numpy upgrade that moved a figure gets explained rather than argued about.
    """
    return {
        "kind": classify_machine(),
        "cpu": _cpu_model(),
        "arch": platform.machine(),
        "os": platform.platform(terse=True),
        "python": platform.python_version(),
        "numpy": _numpy_version(),
    }


def _numpy_version() -> str:
    try:
        import numpy

        return numpy.__version__
    except ImportError:  # pragma: no cover - numpy is a hard dependency
        return "absent"


def git_revision() -> str | None:
    """The commit this was produced at, when there is one. Informational, never a check.

    The fingerprint is what decides whether a result is current. This is here so that a result
    can be located in history, and it is allowed to be absent — a result generated in a fresh
    worktree is not less true than one generated after a commit.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


# -- writing one --------------------------------------------------------------------------


def build_result(
    name: str,
    *,
    target: str,
    kind: str = "measurement",
    produced_by: dict,
    summary: dict,
    units: dict[str, str],
    code_sources: list[str] | tuple[str, ...],
    conditions: dict | None = None,
    write: bool = True,
) -> dict:
    """Assemble a stamped result and, by default, write it.

    ``units`` maps every figure in ``summary`` to a declared unit. It is not decoration: it is
    what lets :func:`provenance_problems` enforce the corpus rule dimensionally instead of
    guessing from a key's name, and it is what a table renderer uses so that no unit is ever
    typed into a chapter by hand.
    """
    if target not in TARGETS:
        raise ValueError(f"unknown target {target!r}; expected one of {TARGETS}")
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}; expected one of {KINDS}")
    if target == "rig" and kind == "measurement":
        require_rig()

    payload: dict[str, Any] = {
        "name": name,
        "target": target,
        "kind": kind,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "produced_by": produced_by,
        "recorded_on": recorded_on(),
        "git_revision": git_revision(),
        "code_sources": sorted(code_sources),
        "code_fingerprint": code_fingerprint(code_sources, target, kind),
        "summary": summary,
        "units": units,
    }
    if conditions:
        payload["conditions"] = conditions

    problems = provenance_problems(f"{name}.json", payload)
    if problems:
        raise ValueError(
            f"refusing to write bench/results/{name}.json:\n  - " + "\n  - ".join(problems)
        )

    if write:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        path = RESULTS_DIR / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"  wrote {path.relative_to(ROOT)}")
    return payload


def load_result(name: str) -> dict:
    """Read a stamped result, or say clearly which runner would produce it."""
    path = RESULTS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"bench/results/{name}.json does not exist. Find what writes it with "
            f"`grep -rl {name} bench/ models/`."
        )
    return json.loads(path.read_text())


def result_exists(name: str) -> bool:
    return (RESULTS_DIR / f"{name}.json").exists()


# -- the rules ------------------------------------------------------------------------------


def _leaf_figures(summary: Any, prefix: str = "") -> dict[str, float]:
    """Every number in a summary, by dotted path, so units can be checked against all of them."""
    found: dict[str, float] = {}
    if isinstance(summary, dict):
        for key, value in summary.items():
            found |= _leaf_figures(value, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(summary, list):
        for i, value in enumerate(summary):
            found |= _leaf_figures(value, f"{prefix}[{i}]")
    elif isinstance(summary, bool):
        pass  # a flag is not a figure
    elif isinstance(summary, int | float):
        found[prefix] = float(summary)
    return found


def _unit_for(path: str, units: dict[str, str]) -> str | None:
    """The declared unit for a figure, allowing one declaration to cover a whole sub-tree.

    ``{"clock": "byte"}`` covers ``clock.p50`` and ``clock.samples[3]`` alike, so a summary with
    a distribution in it does not need forty identical lines.
    """
    if path in units:
        return units[path]
    parts = path.replace("[", ".[").split(".")
    for cut in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:cut]).replace(".[", "[")
        if prefix in units:
            return units[prefix]
    return None


def provenance_problems(filename: str, payload: dict) -> list[str]:
    """Everything wrong with a result, as sentences somebody can act on.

    Called both when writing a result and by ``scripts/verify-numbers.py`` over every committed
    one, so a file cannot be written by a runner that has since been changed to break a rule.
    """
    problems: list[str] = []
    target = payload.get("target")
    kind = payload.get("kind")
    summary = payload.get("summary", {})
    units = payload.get("units", {})
    produced_by = payload.get("produced_by") or {}

    if target not in TARGETS:
        problems.append(f"{filename}: target {target!r} is not one of {TARGETS}")
    if kind not in KINDS:
        problems.append(f"{filename}: kind {kind!r} is not one of {KINDS}")
    if problems:
        return problems

    # A model result declares units per node rather than per figure: its summary holds a whole
    # graph, and a leaf-by-leaf declaration would be several hundred lines restating what the
    # model file already says. The requirement is the same one in a different shape — every
    # quantity in the file has a declared unit and the build can find it.
    if kind == "model" and target != "model":
        problems.append(
            f"{filename}: kind 'model' must declare target 'model'. A model run is a computation, "
            "not a measurement of anything outside this repository."
        )

    if kind == "model":
        declared_nodes = set(units)
        graph_nodes = set(summary.get("nodes", {}))
        for missing in sorted(graph_nodes - declared_nodes):
            problems.append(f"{filename}: node {missing!r} appears in the graph with no unit")
        for extra in sorted(declared_nodes - graph_nodes):
            problems.append(f"{filename}: `units` names {extra!r}, which is not a node")
        for node_name, unit in sorted(units.items()):
            try:
                has_time(unit)
            except UnitError as exc:
                problems.append(f"{filename}: node {node_name!r} declares {unit!r} — {exc}")
        if not produced_by:
            problems.append(f"{filename}: `produced_by` is empty — a result must say what made it")
        for required in ("model", "scenario", "seed", "samples"):
            if required not in produced_by:
                problems.append(
                    f"{filename}: a model result must record {required!r} in `produced_by`, or "
                    "nobody can reproduce the interval it publishes."
                )
        return problems

    # A sampling experiment is stamped `kind: measurement` because it measures the model rather
    # than the world, and it escaped the rule above for years on that technicality. It should not
    # have: an unseeded run is a number nobody can reproduce, which is the one thing this
    # repository refuses everywhere else. Appendix B says so in as many words, and said it while
    # six results in `bench/results/` recorded no seed at all.
    if target == "model" and "seed" not in produced_by:
        problems.append(
            f"{filename}: a result computed from a model must record 'seed' in `produced_by`. "
            "Where the run uses many seeds, record the one they are derived from and say how."
        )

    # Every figure declares a unit, and every declared unit is a unit.
    figures = _leaf_figures(summary)
    for path in sorted(figures):
        unit = _unit_for(path, units)
        if unit is None:
            problems.append(
                f"{filename}: the figure {path!r} declares no unit. Add it to `units` — "
                "a prefix covers a whole sub-tree, so one entry usually does. Use "
                "'dimensionless' for a pure ratio."
            )
            continue
        try:
            if target == "corpus" and has_time(unit):
                problems.append(
                    f"{filename}: {path!r} is in {unit!r}, which has time in it, and this is a "
                    "`corpus` result. How fast a codec ran is a property of the machine that ran "
                    "it, not of the codec — take it on the rig (target `rig`) or do not take it."
                )
        except UnitError as exc:
            problems.append(f"{filename}: {path!r} declares {unit!r}, which is not a unit ({exc})")

    for declared in sorted(units):
        if declared not in figures and not any(f.startswith(declared) for f in figures):
            problems.append(
                f"{filename}: `units` declares {declared!r}, which no figure in the summary uses. "
                "A stale unit is a renamed figure nobody re-stamped."
            )

    if not produced_by:
        problems.append(f"{filename}: `produced_by` is empty — a result must say what made it")

    if target == "model":
        for required in ("model", "scenario"):
            if required not in produced_by:
                problems.append(
                    f"{filename}: a model result must record {required!r} in `produced_by`, or "
                    "nobody can tell which model it is about."
                )

    if kind == "measurement" and target == "corpus":
        for required in ("corpus", "codec"):
            if required not in produced_by:
                problems.append(
                    f"{filename}: a corpus measurement must record {required!r} in `produced_by`. "
                    "A compression figure without the body of data it compressed is not a "
                    "measurement, it is an anecdote."
                )
    if (
        kind == "measurement"
        and target == "rig"
        and payload.get("recorded_on", {}).get("kind") != "rig"
    ):
        problems.append(
            f"{filename}: a rig measurement must have been recorded on the rig; this one says "
            f"{payload.get('recorded_on', {}).get('kind')!r}."
        )
    if kind == "measurement" and target == "estate":
        for required in ("system", "window", "observed_at"):
            if required not in produced_by:
                problems.append(
                    f"{filename}: an estate observation must record {required!r} in "
                    "`produced_by`. Nobody can re-run this measurement, so the disclosure is the "
                    "only thing standing between it and a number somebody remembered."
                )
    return problems


def main() -> int:  # pragma: no cover - a convenience for `python3 -m bench.stamp`
    """Print what this machine is, and whether it may take a rig measurement."""
    declared = rig_declaration()
    print(f"this machine: {_cpu_model()!r} ({platform.machine()})")
    print(f"classified as: {classify_machine()}")
    if declared:
        machine = declared.get("machine", {})
        print(f"declared rig: {machine.get('cpu_model')!r}, {machine.get('cores')} cores")
    else:
        print("declared rig: none (rig/machine.yml is absent) — no rig figures can be taken")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


#: The targets a runner in this repository can actually produce, and how.
#:
#: ``estate`` is deliberately absent. An observation of a real deployment cannot be produced by
#: code in a book — it is taken by somebody with access to a running system, recorded by hand
#: through :func:`build_result`, and reviewed by a human being. That is the whole of its
#: verification, it is much weaker than the other two, and the chapters that use one say so at
#: the point of use rather than in a footnote.
RUNNABLE_TARGETS = ("corpus", "rig")


#: How close two runs of the same computation have to be before the book calls them the same.
#:
#: Not exact equality, and the reason is a CI failure rather than a preference. Numpy chooses
#: different instruction paths on different processors, so a percentile over a hundred thousand
#: floats can differ in its last bits between one runner and the next. A check that compared
#: exactly went green on one machine and red on another with an identical tree, which is the
#: worst kind of check: it fails for a reason that has nothing to do with the thing being checked,
#: and people learn to re-run it until it passes.
#:
#: One part in a million is far tighter than anything this book prints — every figure is reported
#: to three or four significant figures — and far looser than the noise. A real change to a model,
#: a constant or the sampler moves a figure by orders of magnitude more than this.
RERUN_TOLERANCE = 1e-6


def numeric_differences(
    committed: Any, fresh: Any, tolerance: float = RERUN_TOLERANCE, path: str = ""
) -> list[str]:
    """Where two summaries disagree by more than re-running on another machine would explain.

    Walks both structures together. A missing or added key is always a difference; two numbers
    are the same if they agree to :data:`RERUN_TOLERANCE` relative; anything else is compared for
    equality, because a changed string or a changed flag is never floating-point noise.
    """
    if isinstance(committed, dict) and isinstance(fresh, dict):
        out = []
        for key in sorted(set(committed) | set(fresh)):
            where = f"{path}.{key}" if path else str(key)
            if key not in committed:
                out.append(f"{where}: added")
            elif key not in fresh:
                out.append(f"{where}: removed")
            else:
                out += numeric_differences(committed[key], fresh[key], tolerance, where)
        return out
    if isinstance(committed, list) and isinstance(fresh, list):
        if len(committed) != len(fresh):
            return [f"{path}: {len(committed)} entries became {len(fresh)}"]
        out = []
        for i, (was, now) in enumerate(zip(committed, fresh, strict=True)):
            out += numeric_differences(was, now, tolerance, f"{path}[{i}]")
        return out
    if isinstance(committed, bool) or isinstance(fresh, bool):
        # `True == 1` in Python, so a flag that quietly became a count would slip through a value
        # comparison. A verdict turning into a number is a change of meaning, not of magnitude.
        same = type(committed) is type(fresh) and committed == fresh
        return [] if same else [f"{path}: {committed!r} -> {fresh!r}"]
    if isinstance(committed, int | float) and isinstance(fresh, int | float):
        if abs(committed - fresh) <= tolerance * max(1.0, abs(committed)):
            return []
        return [f"{path}: {committed!r} -> {fresh!r}"]
    return [] if committed == fresh else [f"{path}: {committed!r} -> {fresh!r}"]


def shown(path: Path | str) -> str:
    """A path as a reader should see it: relative to the repository where it can be.

    This exists because the same bug was fixed three times in three files before anybody wrote it
    down, and the third time it took the Pages deploy out. ``Path.relative_to`` raises when the
    path is outside the root **or** when one of the two is relative and the other absolute — and
    the second case is the one that bites, because a script given ``--out _build/html/models`` on
    the command line has a perfectly reasonable path that simply is not absolute.

    Printing a path is never important enough to fail a build. This never raises.
    """
    path = Path(path)
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)
