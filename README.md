# Sizing and TCO

*Capacity planning, sizing and total cost of ownership, modelled as code.*

A self-study book and a toolkit, built around one question — **how big, how much, and how wrong
could I be?** — and a rule about answering it: every number says where it came from.

**Read it at <https://snowch.github.io/sizing-and-tco>.**

Companion to [computer-systems](https://github.com/snowch/computer-systems), and built on the same
bargain: nothing is published that the repository cannot re-derive.

## What is here

- **A model-as-code DSL** (`sizing/`). A model is a graph of named quantities in a YAML file. Every
  node declares a unit, so the build refuses a model that multiplies the wrong two things. Every
  input declares whether it is a fact, a vendor's claim or an assumption. Every empirical constant
  points at the measurement behind it, and a constant nobody has measured leaves the nodes below it
  visibly empty rather than quietly filled in.
- **Monte Carlo from first principles** (`sizing/mc.py`). Numpy and the standard library, about a
  hundred and fifty lines, written to be read: inverse-transform sampling, four distributions,
  rank correlation, and the arithmetic of how many samples is enough. No simulation framework,
  because you cannot learn sampling from a library call.
- **Two worked models** (`models/`). A scale-out storage cluster, which is the cost exemplar, and
  an observability platform, which is the sizing exemplar and has a hole in it on purpose.
- **The checks that make it worth reading** (`scripts/`). Dimensional analysis that fails the
  build. Provenance that cannot be left blank. A rule against typing a measured figure into a
  sentence. And a test pinning the browser's copy of the evaluator to Python's.

## Getting started

```bash
python3 -m pip install -r requirements.txt -r requirements-dev.txt
npm install -g "mystmd@$(node -p "require('./package.json').devDependencies.mystmd")"

make models    # evaluate and sample every model, and stamp what each one said
make check     # exactly what CI runs
make book      # live preview at localhost:3000
```

`make help` lists the rest.

## Status

The toolkit is complete and both reference models run end to end through the dependency graph, the
generated input UI, the tornado, the sampled distributions, the unit gate and the reference-scenario
tests. The front matter and the two Monte Carlo chapters are written; the remaining chapters are
stubs that name the question they answer and the figures they owe.

Two constants are not yet measured — collector throughput per core, which needs a reference
machine, and spans per request, which needs somebody's instrumented application. The observability
model shows both as missing rather than guessing, which is the behaviour the rest of the book is
about.

## Licence

Prose and figures: [CC BY-NC 4.0](LICENSE). Code, models and tooling:
[Apache 2.0](LICENSE-CODE).
