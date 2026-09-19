// Start the toolkit in this tab. One copy, inlined into every page that runs it.
//
// The runtime is fetched from a pinned URL (about ten megabytes, once per browser); the
// toolkit's own modules and the handful of stamped results a model's measured constants read
// are carried by the page and written where the toolkit looks for them on disk. Nothing is sent
// anywhere: after the fetch, everything runs here.
async function bootToolkit({ pyodideUrl, modules, results, status }) {
  status("Starting Python… about ten megabytes, once.");
  const { loadPyodide } = await import(pyodideUrl + "pyodide.mjs");
  const pyodide = await loadPyodide({ indexURL: pyodideUrl });
  await pyodide.loadPackage(["numpy", "micropip"]);
  await pyodide.pyimport("micropip").install(["Pint", "PyYAML"]);
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
