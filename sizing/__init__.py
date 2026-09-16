"""The model-as-code toolkit behind *Sizing and TCO*.

A model is a directed acyclic graph of named quantities in a text file. Every node declares a
unit and a kind, the build checks the graph dimensionally, evaluates it, samples it, and exports
one JSON file that the published page reads. Nothing is computed in the browser that was not
first computed here.

* :mod:`sizing.units` — the unit registry, and dimensional checking at build time
* :mod:`sizing.mc` — Monte Carlo, from first principles, in numpy
* :mod:`sizing.dsl` — loading a model file into a graph
* :mod:`sizing.evaluate` — point evaluation, sampling, ceilings, tornado
* :mod:`sizing.graph` — deterministic layout
* :mod:`sizing.export` — one JSON per model for the viewer
"""
