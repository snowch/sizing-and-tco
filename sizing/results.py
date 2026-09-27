"""Where a stamped result lives, and how a model finds one.

This used to be two functions in ``bench.stamp``, imported lazily from ``sizing.dsl`` when a
model declared a measured constant. That made the toolkit depend on the book's harness -- the
wrong way round -- and it meant a model with a measured node could not load anywhere ``bench``
was not: in the browser, the viewer ships the ``sizing`` package alone, so
every stage from ch09 on failed to load there, silently, on a page nobody had opened.

Now the toolkit owns the two lines that read a result, ``bench.stamp`` imports them from here,
and a page that runs the toolkit writes the handful of results a model needs under the same
path it would look at on disk.

A model may also carry results of its own, in a ``results/`` folder beside its ``scenarios/``.
That is where a reader's own measurement goes: spans per request on their application, the
compression of their data. The model's folder is read first, so a reader who has measured a
constant the book measured on its own corpus uses theirs. A result found there is the reader's,
not the book's, and ``scripts/verify-models.py`` holds it to the rules for an ``estate`` result:
nobody else can re-take it, so it says what system, over what window and on what date.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "bench" / "results"


def result_path(name: str, beside: Path | None = None) -> Path | None:
    """Where the result a measured node names lives: the model's own folder first, then the book's.

    ``beside`` is the folder holding the model file. A name that is not a plain file name finds
    nothing, so a model cannot read a file from anywhere else by naming a path.
    """
    if not name or Path(name).name != name:
        return None
    folders = ([beside / "results"] if beside is not None else []) + [RESULTS_DIR]
    return next((f / f"{name}.json" for f in folders if (f / f"{name}.json").exists()), None)


def load_result(name: str, beside: Path | None = None) -> dict:
    """Read a stamped result, or say clearly which runner would produce it."""
    path = result_path(name, beside)
    if path is None:
        raise FileNotFoundError(
            f"bench/results/{name}.json does not exist. Find what writes it with "
            f"`grep -rl {name} bench/ models/`."
        )
    return json.loads(path.read_text())


def result_exists(name: str, beside: Path | None = None) -> bool:
    return result_path(name, beside) is not None


def is_own(name: str, beside: Path | None) -> bool:
    """Whether the result a node names is the model's own rather than the book's."""
    path = result_path(name, beside)
    return path is not None and beside is not None and path.parent == beside / "results"
