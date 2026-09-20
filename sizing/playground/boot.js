// Start the toolkit in this tab. One copy, inlined into every page that runs it.
//
// The runtime is fetched from a pinned URL (about ten megabytes, once per browser); the
// toolkit's own modules and the handful of stamped results a model's measured constants read
// are carried by the page and written where the toolkit looks for them on disk. Nothing is sent
// anywhere: after the fetch, everything runs here.
async function bootToolkit({ pyodideUrl, modules, results, wheels, status }) {
  // Whether the runtime is already on this device: kept by the worker after an earlier Run, or
  // fetched ahead of need by the offline control. The line under the button should not promise
  // a download that is not going to happen.
  let kept = false;
  try {
    kept = "caches" in window && Boolean(await caches.match(pyodideUrl + "pyodide.asm.wasm"));
  } catch (error) {
    kept = false;
  }
  status(kept ? "Starting Python from the copy this browser keeps…"
              : "Starting Python… about ten megabytes, once.");
  const { loadPyodide } = await import(pyodideUrl + "pyodide.mjs");
  const pyodide = await loadPyodide({ indexURL: pyodideUrl });
  // numpy and PyYAML come with the runtime, from its own pinned lock file. Pint and what it
  // needs are exact wheels from PyPI, pinned in sizing/playground/toolkit.py, so that a Run
  // installs the same code on every day it is pressed and the offline control knows what to keep.
  await pyodide.loadPackage(["numpy", "pyyaml", ...(wheels || [])]);
  pyodide.FS.mkdirTree("/sizing/playground");
  pyodide.FS.mkdirTree("/bench/results");
  for (const [name, source] of Object.entries(modules)) {
    pyodide.FS.writeFile("/sizing/" + name, source);
  }
  for (const [name, text] of Object.entries(results || {})) {
    pyodide.FS.writeFile("/bench/results/" + name, text);
  }
  await pyodide.runPythonAsync(
    "import sys\nsys.path.insert(0, '/')\nfrom sizing.playground.driver import check, resample");
  return pyodide;
}
