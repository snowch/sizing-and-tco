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

#: The packages a Run loads from the runtime's own distribution, at the versions its lock file
#: pins.
RUNTIME_PACKAGES = ("numpy", "pyyaml")

#: What a Run installs from PyPI, as exact files rather than names: Pint at the version
#: ``requirements.txt`` pins for the native toolkit, and the four pure-Python packages it needs,
#: each with the digest PyPI published beside it. Pinned for the reason the runtime is, so that
#: Run installs the same code on every day it is pressed, and listed so that the offline control
#: knows what a Run will fetch. ``tests/test_scripts.py`` holds the Pint version to the native pin.
WHEELS = (
    (
        "https://files.pythonhosted.org/packages/1b/dd/a9fe6a0a09512da23951c68bf36466aeecd89def3183dc095edbc807ddc5/pint-0.25.3-py3-none-any.whl",
        "27eb25143bd5de9fcc4d5a4b484f16faf6b4615aa93ece6b3373a8c1a3c1b97d",
    ),
    (
        "https://files.pythonhosted.org/packages/27/cd/c883e1a7c447479d6e13985565080e3fea88ab5a107c21684c813dba1875/flexcache-0.3-py3-none-any.whl",
        "d43c9fea82336af6e0115e308d9d33a185390b8346a017564611f1466dcd2e32",
    ),
    (
        "https://files.pythonhosted.org/packages/fe/5e/3be305568fe5f34448807976dc82fc151d76c3e0e03958f34770286278c1/flexparser-0.4-py3-none-any.whl",
        "3738b456192dcb3e15620f324c447721023c0293f6af9955b481e91d00179846",
    ),
    (
        "https://files.pythonhosted.org/packages/39/be/3ae887e84c38c4dd1c549cd5825adc93f48069a94fe1cb8ac52a9da16f15/platformdirs-4.11.11-py3-none-any.whl",
        "972ea6b2b387155a536226a0750e46923d731d459a387c4a255c583ed2f64547",
    ),
    (
        "https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80/typing_extensions-4.16.0-py3-none-any.whl",
        "481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8",
    ),
)

#: The cache the worker keeps the runtime in. The page that fills it ahead of need and the
#: worker that serves from it have to agree on the name, so it is declared once, here.
RUNTIME_CACHE = "sizing-and-tco-runtime-v1"


def wheels() -> list[str]:
    """The pinned wheels, as the URLs a page hands the runtime."""
    return [url for url, _digest in WHEELS]


def offline_manifest() -> dict:
    """What a page needs to fetch the runtime ahead of need, and where to keep it."""
    return {
        "pyodide": PYODIDE,
        "packages": list(RUNTIME_PACKAGES),
        "wheels": wheels(),
        "cache": RUNTIME_CACHE,
    }


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
