"""Where a stamped result lives, and how a model finds one.

This used to be two functions in ``bench.stamp``, imported lazily from ``sizing.dsl`` when a
model declared a measured constant. That made the toolkit depend on the book's harness -- the
wrong way round -- and it meant a model with a measured node could not load anywhere ``bench``
was not: in the browser, the viewer ships the ``sizing`` package alone, so
every stage from ch09 on failed to load there, silently, on a page nobody had opened.

Now the toolkit owns the two lines that read a result, ``bench.stamp`` imports them from here,
and a page that runs the toolkit writes the handful of results a model needs under the same
path it would look at on disk.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "bench" / "results"


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
