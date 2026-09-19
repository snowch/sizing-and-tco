"""What a page that runs the toolkit in a browser has to carry, in one place.

Three pages run the real toolkit under Pyodide: the inline runner in a chapter that quotes the
model file, the playground for a chapter that does not, and the viewer's resample. Each used to
carry its own copy of the runtime URL and the module list, and a third copy is how the two
existing ones will drift. This is the one copy.
"""

from __future__ import annotations

from pathlib import Path

from sizing.dsl import Measured, Model
from sizing.results import load_result, result_exists

ROOT = Path(__file__).resolve().parent.parent.parent

#: Pinned, because an unpinned runtime changes what a reader sees without changing a line here.
PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/"

#: Every module the browser's calls reach. Inlined rather than fetched, so a page has one network
#: dependency (the runtime) instead of two.
MODULES = (
    "__init__",
    "units",
    "expr",
    "dsl",
    "normal",
    "mc",
    "evaluate",
    "graph",
    "results",
    "export",
)


#: The JavaScript that starts the runtime and lays the toolkit out for it. Inlined by each page.
BOOT = (Path(__file__).resolve().parent / "boot.js").read_text()


def sources() -> dict[str, str]:
    """The toolkit's source, keyed by the path each file takes under ``/sizing/`` in the browser."""
    out = {f"{name}.py": (ROOT / "sizing" / f"{name}.py").read_text() for name in MODULES}
    out["playground/__init__.py"] = ""
    out["playground/driver.py"] = (ROOT / "sizing" / "playground" / "driver.py").read_text()
    return out


def results_for(model: Model) -> dict[str, str]:
    """The stamped results a model's measured constants read, keyed by file name.

    A measured node loads ``bench/results/<result>.json`` when the model loads. In the browser
    there is no such directory unless the page writes one, so the page carries exactly the
    results this model needs and puts them where the toolkit looks. A constant nobody has
    measured has no file here either, and stays *not yet measured* in the browser as on disk.
    """
    names = sorted(node.result for node in model.nodes.values() if isinstance(node, Measured))
    return {
        f"{name}.json": (ROOT / "bench" / "results" / f"{name}.json").read_text()
        for name in names
        if result_exists(name) and load_result(name)
    }
