# The conformance suite

What this book's toolkit says about a fixed set of model files, written down so that another
implementation of the same rules can be held to it. The model builder
([`design/model-builder.md`](../design/model-builder.md)) is one: its rules engine is JavaScript,
and it may not release while any case here gets a different answer from its engine.

The suite is generated from the toolkit in this repository, so it cannot disagree with it, and
`make check` regenerates it and fails if the committed fixtures are not what the toolkit says now.
A rule the book changes therefore arrives at the builder as failing cases, never as a surprise to
a reader.

The generator, the cases and the codes were written in the builder's repository against a pinned
commit of this one, and moved here so the book publishes its own answers.

## Running it

```bash
python3 conformance/generate.py          # rewrite fixtures/ from the toolkit as it is now
python3 conformance/generate.py --check  # fail if fixtures/ is not what the toolkit says now
```

The fixtures have sorted keys and no timestamps, so the same tree always writes the same bytes.
`--check` compares numbers to a part in a trillion, because a point value can differ in its last
bit between processors.

## What is here

| Path | What it is |
|---|---|
| `generate.py` | Asks the toolkit about every case and writes `fixtures/` |
| `cases/invalid/<name>/` | Hand-written models, one per refusal the loader and `verify-models.py` know |
| `cases/edge/<name>/` | Hand-written models the book accepts, each pinning down one exact behaviour |
| `probes/units.txt` | Unit strings, each read as the book's Pint registry reads it |
| `probes/formulas.txt` | Formulas, each parsed to the book's tree or refused the book's way |
| `probes/yaml.txt` | YAML documents, with the typed Python values PyYAML builds from each |
| `fixtures/` | Generated. Committed, so a runner needs no Python and no network |

A case is a directory with `model.yaml`, `scenarios/*.yaml`, and a `case.yaml` saying what it is
for. A case that needs a stamped result the book does not have carries it in `results/`, which
the toolkit reads before `bench/results/`, as it does for a reader's own measurements
(Appendix A). The reference models and every stage under `models/web_service/stages/` are read in
place.

`case.yaml`'s `expect` lists the codes the case exists to show. The generator stops if the
toolkit no longer says them, so a case cannot drift into testing something else, or nothing.

## The fixtures

`manifest.json` names the format version the toolkit reads (`dsl`), the fixture layout's own
version, the toolkit's versions (Python, numpy, Pint, PyYAML), every code the generator knows,
the currencies a model may price in, and the case list.

`units.json` is Pint's registry reduced to a table (every unit's symbols, aliases, factor to base
units and dimensions; every prefix; the currencies), with the verdict on each probe.

`formulas.json` is the list of allowed functions and the verdict on each formula probe.

`yaml.json` is each YAML probe's value as PyYAML builds it, with every Python type kept (`3` and
`3.0` differ, and so do `True` and `1`), and the book's model reader's verdict under `read`: it
refuses a key written twice.

`results.json` is every stamped measurement in `bench/results/` a `measured` node can name, with
the implementation it was measured on.

`tornado/<case>.json` is `tornado()` for every output of a case at its reference scenario.

`sampling/<case>.json` is the sampled figures for every scenario of a case at its seed, and how
far each moves across sixteen other seeds. Draw for draw another sampler cannot match this one,
so it is held to these by distribution.

`products.json` is the list of product names no chapter, model or figure may use
(`tests/test_book.py`). `outline.json` is the chapter list by slug.

`cases/<group>/<name>.json`, one per case:

| Field | What the toolkit said |
|---|---|
| `files`, `results` | The inputs: the model, scenario and result files as text |
| `load` | `ok`, or the refusal: `code`, the `node` and `field` it names, the exception and message |
| `verify` | Every `verify-models.py` problem, each with `code`, `rule`, `node`, `part`, `scenario`, `cause`; and `crashed` if the verifier fell over |
| `model` | Classification, evaluation order, outputs, unmeasured constants, correlations |
| `nodes` | Per node: kind, unit, dimensions, conversion factors, what blocks it, and its fields |
| `scenarios` | Per scenario: every node's value at the point, and each ceiling's value, limit, margin and verdict; or the error |

## Codes

A message is classified by pattern into a code, so an engine is compared on *what* failed rather
than on the wording. A message that matches no pattern, or more than one, stops the generator: a
rule the book adds must be given a code here before the suite can be regenerated. The codes are
listed in `generate.py` (`PROBLEMS`, `REFUSALS`, `CAUSES`) and in `manifest.json`.

Every code has a case except `classification.definitional-with-ceilings`, which cannot happen: a
model with a ceiling is conditional by definition.
