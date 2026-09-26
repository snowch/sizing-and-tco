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

The problems run in their chapters and need nothing installed. At a desk you need Python 3.11 or
later. Install the toolkit's dependencies into a virtual environment of the repository's own,
because many operating systems' own Python refuses `pip install` with
`error: externally-managed-environment`.

```bash
git clone https://github.com/snowch/sizing-and-tco.git
cd sizing-and-tco
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 scripts/verify-setup.py
```

While the environment is active, `python3` is the environment's Python, so `python3 -m pytest` and
every `make` target use the packages you just installed. Activate it again in each new terminal with
`source .venv/bin/activate`. Use `python3 -m pip` and `python3 -m pytest`, not a `pytest` installed
as a standalone tool. A standalone `pytest` runs in an environment of its own and cannot
import this repository's code.

`python3 scripts/verify-setup.py` says whether the three Python packages the toolkit needs import,
and prints their versions. It also says whether `myst` and `node` are on your path, and whether this
machine may take a timing for the book. It fails only when one of the three Python packages is
missing.

Building the book needs Node as well, for the parser that resolves the book's cross-references. Only
a reader who wants to build the book needs it; the problems and the checks on the figures do not.

```bash
npm install -g "mystmd@$(node -p "require('./package.json').devDependencies.mystmd")"
```

It installs the version of MyST that `package.json` pins. CI installs Node 22.

## What the commands do

```bash
make help       # list every target, each with a line saying what it does
make measure    # re-take every constant that a codec decides
make models     # evaluate and sample every model, and stamp what each one said
make figures    # re-render every table and diagram from the stamped results
make problems   # run every chapter's problems; they fail until you solve them
make check      # everything CI runs
make book       # build the site and serve it at localhost:3000; run it again after an edit
```

To run one problem rather than all of them, use the command under that problem: `python3 -m pytest tests/<chapter>/<test file> -m problem`.

Run `make check` before you believe anything. It is the same script CI runs, so the two cannot drift. It re-runs every model and rebuilds every page, so it takes minutes. Without MyST installed, `make check` skips the book build and every check that reads it, and says so.

% number-ok: settings this book chose, not figures it measured. Stated once because they never vary, and tests/test_book.py fails if they do.
Every model run in this book draws 100,000 samples from seed 20260916. Neither appears under the tables, because a constant repeated under ninety figures is not information. A test fails if any run uses a different sample count or seed, so the sentence above cannot stop being true without the build failing.

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

Each model is a file. The table below counts the kinds of node in the web service model, this book's running example:

```{include} ../chapters/_generated/appendix-h-running-the-toolkit-models.md
```

The table's last row says whether the build classifies this model as a definitional model or a conditional one. The build works that out from the file: a `measured` node or a `ceiling` makes a model conditional. [ch06](#queueing-and-the-knee) is where this running example crosses that line; the chapter adds its first ceiling, and from then on it is conditional.

## Running your own model

A model file of your own can be checked, and worked out, in two places: at a desk with one command, or in the browser in the frame on this page. Both run the same checks the build runs on the book's own models.

Your file must be in the format the book's own model files use. It needs a `model:` name, a `nodes:` section and an `outputs:` list. [Appendix A](#appendix-a-dsl-reference) describes the format.

### At a desk

```bash
python3 scripts/verify-models.py path/to/your/model.yaml
```

The file can be anywhere; it does not have to be inside the repository. The command applies every rule the build applies to the book's models:

- every formula's result has the unit its node declares;
- every input says who decides it and where its number came from (a provenance kind and a source), and a `fact` cites something;
- every ceiling declares a headroom and a reason;
- every node feeds an output.

If the file breaks any rule, the command lists every problem at once and exits with an error. A file that will not load at all — a formula that names a node the file does not define, for instance — is reported the same way, as one problem.

If the file passes, the command prints how many nodes it has and whether it is a definitional model or a conditional one. Then, for each output, it prints the value with every input at its stated value or at the median of its distribution. Where an input is uncertain, it also prints the 5th and 95th percentiles of the output.

If a folder named `scenarios` sits beside the file, the command works out each scenario in it. Otherwise it works out the file as written. The command writes nothing: no file in the repository changes.

### In the browser

Paste a model file into the box in the frame below and press *Check*. The box opens with a small working model in the same format, which you can edit.

The page runs `scripts/verify-models.py` on what you pasted: the same rules, from the same file, as the desk command. The first press downloads a Python runtime, once; after that your browser keeps it. Nothing you paste is sent anywhere.

(custom-model-viewer)=

```{iframe} /models/custom-model-viewer.html
:width: 100%
```

If the toolkit refuses the file, the page lists every problem. The desk command would refuse the same file for the same reasons. If the file passes, the page says whether it is a definitional or a conditional model, shows each output's value and its 5th-to-95th range, and lists every node. Open a node to see what the file declares for it: its label, its value or distribution, where its number came from, its formula, and for a ceiling its limit, headroom and reason.

The page checks the pasted file alone, so it has no scenarios: it works the file out as written. For scenarios, use the desk command. The page draws no graph and has no sliders. Those are in the chapters' model viewers, built from results the book has stamped; a model of your own has no stamped result.

## Interactive viewer features

The toolkit's interactive viewers appear throughout the book. Each feature is introduced when the chapter needs it. This table lists them all and where they first appear.

| Feature | Introduced | What it does |
|---------|------------|--------------|
| **Nodes and edges** | [ch02](#what-a-workload-is) | Boxes are quantities; lines show what feeds what. Blue is an input, a number the model is given, and a bar down its left edge marks one you choose. Hollow grey is derived: the toolkit works it out. |
| **Sliders** | [ch02](#what-a-workload-is) | Open *Inputs* under the graph: one slider for each input that declares a range. Drag it and everything downstream updates as you drag. |
| **Click a node** | [ch02](#what-a-workload-is) | Opens *Details*: a derived node's formula, an input's value and source, and under *In the file* the node's own lines in the model file. |
| **Unit checking** | [ch02](#what-a-workload-is) | The toolkit validates every formula. A quantity with the wrong unit is rejected, not silently accepted like a spreadsheet. |
| **Provenance detail** | [ch03](#where-the-numbers-come-from) | Click an input node and *Details* names its provenance kind in words — fact, vendor claim or assumption — followed by its source. The book's provenance tables mark the same three kinds with ● for a fact, ◐ for a vendor claim and ○ for an assumption. |
| **Measured constants** | [ch09](#capacity) | Amber nodes: numbers measured on a named implementation. The file holds no number for one, only the name of the stamped result it comes from. |
| **Ceiling nodes** | [ch06](#queueing-and-the-knee) | Red nodes: limits past which the model changes regime, such as the queueing knee. A chain of multiplications cannot model these, and the build refuses one that declares no headroom below it. |
| **Model file** | [ch02](#what-a-workload-is) | On a wide screen, press *Expand* and choose *Model file* to read the whole file, with the node you picked marked. |
| **Problem Check** | Throughout | Embedded under chapter problems. Runs your solution against the toolkit's test suite. Passes only when solved. |

The colours mean the same in every model viewer in the chapters: blue for an input, hollow grey for derived, amber for a measured constant, red for a ceiling. Every one of those viewers has the same controls: drag a slider, click a node, expand the viewer. The checker above uses the same four colours down the left edge of each node and has none of those controls: it lists the nodes of a file and opens one when you click it. Once you can read one chapter's model, you can read any model in the book.

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
