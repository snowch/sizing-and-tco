// Start the toolkit in this tab. One copy, inlined into every page that runs it.
//
// The runtime is fetched from a pinned URL (about ten megabytes, once per browser); the
// toolkit's own modules, the handful of stamped results a model's measured constants read and,
// under a chapter's problems, the chapter's own tests are carried by the page and written where
// the toolkit looks for them on disk. Nothing is sent anywhere: after the fetch, everything
// runs here.
async function bootToolkit({ pyodideUrl, modules, results, wheels, files, status }) {
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
  layOut(pyodide, { modules, results, files });
  await pyodide.runPythonAsync(
    "import sys\nsys.path.insert(0, '/')\nfrom sizing.playground.driver import check, resample");
  return pyodide;
}

// Write what a page carries where the toolkit looks for it: its modules under /sizing, stamped
// results under /bench/results, and any other file at the path it has in the repository.
function layOut(pyodide, { modules, results, files }) {
  const write = (path, text) => {
    pyodide.FS.mkdirTree(path.slice(0, path.lastIndexOf("/")));
    pyodide.FS.writeFile(path, text);
  };
  for (const [name, source] of Object.entries(modules || {})) write("/sizing/" + name, source);
  for (const [name, text] of Object.entries(results || {})) write("/bench/results/" + name, text);
  for (const [path, text] of Object.entries(files || {})) write("/" + path, text);
}

// One runtime per tab, however many controls on the page ask for it. A chapter can carry the
// model's Run and a Check under each of its problems: the first to be pressed starts Python,
// the rest wait for the same start and then lay their own files out beside it. Every caller's
// status line hears how the start is going, whichever of them began it.
function shareToolkit(options) {
  const shared = window.__toolkit || (window.__toolkit = { listeners: [] });
  if (options.status) shared.listeners.push(options.status);
  const status = (text) => { for (const say of shared.listeners) say(text); };
  if (!shared.booting) {
    shared.booting = bootToolkit({ ...options, status });
    return shared.booting;
  }
  return shared.booting.then((pyodide) => { layOut(pyodide, options); return pyodide; });
}
