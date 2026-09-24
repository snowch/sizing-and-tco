---
title: "Running the toolkit"
short_title: "Appendix H · Running the toolkit"
---

(appendix-h-running-the-toolkit)=
# Appendix H · Running the toolkit

:::{note} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | The make targets, how to check a figure against the repository, and what is in it |
| **Source** | `Makefile`, `scripts/ci-check.sh`, `bench/results/` |
:::

Nothing in this book needs to be run to be read. This page is for the point where you want to
check a figure rather than trust it, or run a problem, or point the toolkit at your own numbers.

## Installing it

The problems run in their chapters and need nothing. At a desk they need Python and nothing
else. Building the book needs Node as well, for the parser that resolves its cross-references:

```bash
git clone https://github.com/snowch/sizing-and-tco.git
cd sizing-and-tco
python3 -m pip install -r requirements.txt -r requirements-dev.txt
npm install -g "mystmd@$(node -p "require('./package.json').devDependencies.mystmd")"
```

## What the commands do

```bash
make measure    # re-take every constant that a codec decides
make models     # evaluate and sample every model, and stamp what each one said
make figures    # re-render every table and diagram from the stamped results
make check      # everything CI runs
make book       # live preview at localhost:3000
```

Run `make check` before you believe anything. It is the same script CI runs, so the two cannot
drift, and it takes well under a minute.

% number-ok: settings this book chose, not figures it measured. Stated once because they never vary, and tests/test_book.py fails if they do.
Every model run in this book draws 100,000 samples from seed 20260916. Neither appears under the
tables, because a constant repeated under ninety figures is not information, and a test fails if
a run ever uses a different one, so that this sentence cannot quietly stop being true.

`python3 -m pip`, not a standalone tool install. `python3 -m pytest` has to work, and a `pytest`
installed by pipx or uv has its own environment and cannot import this repository's code.

## How to check a number in this book

Every figure on every page came out of a file under `bench/results/`. Pick one, say how well the
web service's records compress, and follow it backwards:

```bash
python3 -c "import json; print(json.load(open('bench/results/records-compression.json'))['produced_by'])"
python3 -m bench.run_corpus --check
```

The first prints the corpus, the codec and the implementation the figure belongs to. The second
re-derives it from scratch on your machine and fails if it has moved. That is the whole contract:
a number, what produced it, and a command that fails when the two have parted company.

The pages you are reading were built from this commit, which is where to point a checkout when a
figure and the repository disagree:

```{include} ../chapters/_generated/build.md
```

Your laptop cannot take a timing on the reference machine, and the toolkit will not pretend it
can: `verify-setup.py` says so, and every figure that would need such a timing renders as a box
saying it has not been measured. [ch03](#where-the-numbers-come-from) is about why.

## What is in the repository

```{include} ../chapters/_generated/appendix-h-running-the-toolkit-constants.md
```

Every constant, including the ones nobody has measured. A row saying *not yet measured* is not a
gap somebody forgot to fill; it is a figure this repository refuses to invent.

A model is a file. Here is what each one is made of:

```{include} ../chapters/_generated/appendix-h-running-the-toolkit-models.md
```

The last row says whether the build classifies the model as a definitional model or a conditional
one. It works that out from the file, since a `measured` node or a `ceiling` makes it conditional,
and [ch06](#queueing-and-the-knee) is where the reader's own model crosses that line.

## Running your own model

If you have a model of your own, point the toolkit at it in two ways.

At a desk, with Python:

```bash
python3 -m sizing.playground.driver /path/to/your/model.yaml
```

The output is a JSON fixture, suitable for the browser as a `window.__MODEL__` payload. Feed it to the interactive viewer and you will see your model's structure, dependencies, inputs and outputs.

In your browser:

Visit the [custom model viewer](#custom-model-viewer) below. Paste your model file, and the viewer shows your model's structure, dependencies, and what each node computes. You can inspect the graph and click each node to see its definition. If anything is wrong — a formula will not typecheck, or a provenance is missing — the page says so.

(custom-model-viewer)=
### The custom model viewer

```{iframe} /models/custom-model-viewer.html
:width: 100%
:height: 600px
```

The viewer runs the real `sizing.dsl` machinery, unmodified, in your browser. What you paste is parsed the same way `make check` parses the book's own models. Every error it rejects is one the toolkit will reject at the desk.

## What this cannot tell you

**Whether your machine gives the same answers as the one that produced these figures.** The
corpus constants should agree, because a codec is deterministic. But a different Python, a
different compression library, or a processor that takes a different instruction path can move a
figure in its last digits. `make check` allows a tolerance looser than that noise and tighter than
anything this book prints, so the noise passes and a real change does not. Where to put that
tolerance is a judgement, not a fact.

**Whether the tools are the right versions.** `verify-setup.py` checks that things are present,
not that they are the versions the pins name. A dependency resolved differently is the commonest
reason a fresh checkout disagrees with CI, and the honest fix is to read `requirements.txt` rather
than to trust a tick.

**Anything about the models themselves.** Every check on this page is about whether the machinery
runs. A model can pass every one of them and still be a bad description of your system. The
chapters are about that.
