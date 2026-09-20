"""What a page that runs the toolkit in a browser has to carry, in one place.

Four things run the real toolkit under Pyodide: the inline runner in a chapter that quotes the
model file, the playground for a chapter that does not, the viewer's resample, and the check
under each of a chapter's problems. Each used to carry its own copy of the runtime URL and the
module list, and a third copy is how the two existing ones will drift. This is the one copy.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from sizing.dsl import Measured, Model, load_model
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

#: What a Check installs on top of that, to run a chapter's problems in the page: pytest at the
#: version ``requirements-dev.txt`` pins for the native suite, and the four pure-Python packages
#: it imports. The same shape as ``WHEELS``, pinned for the same reason, and listed for the same
#: offline control. Pygments is the largest of them and is there to colour a terminal the page
#: does not have; pytest imports it whether or not it will colour anything, so it ships.
PROBLEM_WHEELS = (
    (
        "https://files.pythonhosted.org/packages/24/25/1de2678b631f5a49215c6c96fff41ba892b0a34df68d6d80292b1b48aa7f/pytest-9.1.1-py3-none-any.whl",
        "37a86b45efb9a47a61a36449063e8e18d0cab3161329fc099eb21783169c4f0c",
    ),
    (
        "https://files.pythonhosted.org/packages/54/20/4d324d65cc6d9205fabedc306948156824eb9f0ee1633355a8f7ec5c66bf/pluggy-1.6.0-py3-none-any.whl",
        "e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746",
    ),
    (
        "https://files.pythonhosted.org/packages/cb/b1/3846dd7f199d53cb17f49cba7e651e9ce294d8497c8c150530ed11865bb8/iniconfig-2.3.0-py3-none-any.whl",
        "f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12",
    ),
    (
        "https://files.pythonhosted.org/packages/49/df/1fceb2f8900f8639e278b056416d49134fb8d84c5942ffaa01ad34782422/packaging-24.0-py3-none-any.whl",
        "2ddfb553fdf02fb784c234c7ba6ccc288296ceabec964ad2eae3777778130bc5",
    ),
    (
        "https://files.pythonhosted.org/packages/71/46/17f022dd3e953bf20a04a028a21ec746d942f8d2af30fa0f124fa0e6a684/pygments-2.21.0-py3-none-any.whl",
        "2363c69b61c4a97c838da3b130dcd6468f4848992b21a82f2a63ec34377137d9",
    ),
)

#: The cache the worker keeps the runtime in. The page that fills it ahead of need and the
#: worker that serves from it have to agree on the name, so it is declared once, here.
RUNTIME_CACHE = "sizing-and-tco-runtime-v1"


def wheels() -> list[str]:
    """The pinned wheels a Run installs, as the URLs a page hands the runtime."""
    return [url for url, _digest in WHEELS]


def problem_wheels() -> list[str]:
    """The pinned wheels a Check installs on top of a Run's."""
    return [url for url, _digest in PROBLEM_WHEELS]


def offline_manifest() -> dict:
    """What a page needs to fetch the runtime ahead of need, and where to keep it."""
    return {
        "pyodide": PYODIDE,
        "packages": list(RUNTIME_PACKAGES),
        "wheels": wheels() + problem_wheels(),
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


#: Where the chapter problems live: one package per chapter, named by slug, holding the stubs
#: file a reader edits and the tests that grade it.
TESTS = ROOT / "tests"

#: A quoted path in a test: the model files and scenarios its tests load, and the one script a
#: problem runs. Quoted, so that a path a docstring merely mentions is not shipped.
QUOTED = re.compile(r"""["'](models/[\w./-]+\.yaml|scripts/[\w-]+\.py)["']""")
#: A stamped result a test loads by name.
LOADED = re.compile(r"""load_result\(\s*["']([\w-]+)["']\s*\)""")

#: Results a chapter's tests load by a name they build at run time, which the scan cannot see.
#: ``tests/test_problems.py`` runs every chapter's tests over exactly what this module ships, so
#: a name missing here fails there rather than in a reader's browser.
PROBLEM_RESULTS = {
    "a_tco_for_finance": (
        "web_service-reference",
        "web_service-sized_for_growth",
        "web_service-power_first",
    ),
}


def problem_chapters() -> list[str]:
    """The slugs of the chapters that have problems with tests, in order."""
    return sorted(path.parent.name for path in TESTS.glob("*/stubs.py"))


def problem_files(slug: str) -> dict[str, str]:
    """Every file a chapter's problems read, keyed by the path each takes under ``/`` in the browser.

    The chapter's test package as it is in the repository; the model files, scenarios and stamped
    results its tests name; and the harness's own stamp module, where a test holds the reader to
    the book's provenance rules. The paths are the repository's, so a test that says
    ``models/web_service/model.yaml`` finds it in the browser exactly where it finds it at a desk.
    Text only, on purpose: nothing under ``sizing`` imports ``bench``.
    """
    here = TESTS / slug
    out = {"tests/__init__.py": (TESTS / "__init__.py").read_text()}
    for path in sorted(here.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            out[path.relative_to(ROOT).as_posix()] = path.read_text()
    text = "\n".join(out.values())
    for name in sorted(set(QUOTED.findall(text))):
        path = ROOT / name
        if not path.is_file():
            continue
        out[name] = path.read_text()
        if path.name == "model.yaml":
            for result, payload in results_for(load_model(path)).items():
                out[f"bench/results/{result}"] = payload
    for name in sorted({*LOADED.findall(text), *PROBLEM_RESULTS.get(slug, ())}):
        if result_exists(name) and load_result(name):
            out[f"bench/results/{name}.json"] = (
                ROOT / "bench" / "results" / f"{name}.json"
            ).read_text()
    if re.search(r"^\s*(from|import) bench\b", text, re.M) or any(
        name.startswith("scripts/") for name in out
    ):
        for name in ("bench/__init__.py", "bench/stamp.py"):
            out[name] = (ROOT / name).read_text()
    return out


def problem_pieces(slug: str) -> list[dict]:
    """For each of a chapter's test files, the pieces of the stubs file it grades.

    A test imports the functions it grades from the chapter's stubs file, and those are the
    pieces of it a reader edits. Each is located by parsing the file, decorators included, so a
    page can show the piece under the problem it belongs to and splice what the reader types back
    into the whole. A test that imports nothing from the stubs has no piece, and the page shows
    it none.
    """
    stubs = TESTS / slug / "stubs.py"
    source = stubs.read_text()
    starts = [0]
    for line in source.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    spans: dict[str, tuple[int, int]] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            first = min([node.lineno, *(d.lineno for d in node.decorator_list)])
            end = starts[node.end_lineno]
            if source[end - 1 : end] == "\n":
                end -= 1
            spans[node.name] = (starts[first - 1], end)
    out = []
    for test in sorted((TESTS / slug).glob("test_problem_*.py")):
        names = [
            alias.name
            for node in ast.walk(ast.parse(test.read_text()))
            if isinstance(node, ast.ImportFrom) and node.module == f"tests.{slug}.stubs"
            for alias in node.names
        ]
        pieces = sorted(
            (
                {"name": name, "start": spans[name][0], "end": spans[name][1]}
                for name in dict.fromkeys(names)
                if name in spans
            ),
            key=lambda piece: piece["start"],
        )
        out.append(
            {
                "test": test.relative_to(ROOT).as_posix(),
                "stubs": stubs.relative_to(ROOT).as_posix(),
                "pieces": pieces,
            }
        )
    return out
