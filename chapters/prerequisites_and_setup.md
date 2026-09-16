---
title: "Prerequisites and setup"
short_title: "ch00 Prerequisites and setup"
---

(prerequisites-and-setup)=
# ch00 · Prerequisites and setup

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Prerequisites** | none |
| **What it produces** | What your machine can do, and what it may therefore not be asked for |
| **Built from** | `logs-line-bytes`, `storage_cluster-reference` |
:::

## The question

What do I need installed, and how do I check that a figure in this book still says what it says
here?

The second half is the reason this chapter exists at all. A book of numbers you cannot re-derive
is a book of assertions, and the difference between the two is one command.

## The material

### What you need

Python, Node, and about twenty minutes.

```bash
python3 -m pip install -r requirements.txt -r requirements-dev.txt
npm install -g "mystmd@$(node -p "require('./package.json').devDependencies.mystmd")"
python3 scripts/verify-setup.py
```

`python3 -m pip`, not a standalone tool install. `python3 -m pytest` has to work, and a `pytest`
installed by pipx or uv has its own environment and cannot import this repository's code.

Nothing here needs a datacentre, a cloud account or a licence. The one thing your laptop cannot
do is take a timing on the reference machine, and the toolkit refuses to pretend otherwise —
`verify-setup.py` says so, and every figure that would need one renders as a box saying it has not
been measured.

### What the commands do

```bash
make measure    # re-take every constant that a codec decides
make models     # evaluate and sample every model, and stamp what each one said
make figures    # re-render every table and diagram from the stamped results
make check      # everything CI runs
make book       # live preview at localhost:3000
```

`make check` is the one that matters. It is the same script CI runs, so the two cannot drift, and
it takes well under a minute. Run it before you believe anything.

### How to check a number in this book

Every figure on every page came out of a file under `bench/results/`. Pick one — the compression
ratio in the storage model, say — and follow it backwards:

```bash
python3 -c "import json; print(json.load(open('bench/results/storage-object-compression.json'))['produced_by'])"
python3 -m bench.run_corpus --check
```

The first prints the corpus, the codec and the implementation the figure belongs to. The second
re-derives it from scratch on your machine and fails if it has moved. That is the whole contract:
a number, what produced it, and a command that disagrees with you if the two have parted company.

### What is in the repository

```{include} _generated/prerequisites-and-setup-constants.md
```

Every constant, including the ones nobody has measured. A row saying *not yet measured* is not a
gap somebody forgot to fill; it is a figure this repository refuses to invent, and
[ch03](#where-the-numbers-come-from) is about why that refusal is worth the inconvenience.

A model is a file. Here is what one is made of:

```{include} _generated/prerequisites-and-setup-models.md
```

The last row is the classification the rest of the book turns on, and
[ch01](#reading-a-model) is about how the build arrives at it.

### The four targets, and what your machine may produce

A number in this book declares where it came from. There are four possibilities and only two of
them are things your laptop can do.

| Target | What it is | Can you produce one? |
|---|---|---|
| `corpus` | a codec or an encoder over a declared body of data | **yes**, and CI re-derives them all on every push |
| `model` | a model file, evaluated and sampled | **yes** |
| `rig` | a throughput or a latency on the declared reference machine | only on that machine |
| `estate` | an observation of a system somebody runs | never by a machine; a person takes it |

The split is not bureaucracy. A compression ratio is a property of a codec and some bytes, so
anybody can check it. A throughput is a property of the computer that produced it, so nobody can
check yours — which is why this repository will not let you record one from the wrong machine
even by accident.

## What the model says

```{include} _generated/prerequisites-and-setup-constants.md
```

## What this cannot tell you

**Whether your machine gives the same answers as the one that produced these figures.** The
corpus constants should, because a codec is deterministic — but a different Python, a different
compression library, or a processor that takes a different instruction path can move a figure in
its last digits. `make check` uses a tolerance far tighter than anything this book prints and far
looser than that noise, and the tolerance is a judgement rather than a fact.

**Whether the tools are the right versions.** `verify-setup.py` checks that things are present,
not that they are the versions the pins name. A dependency resolved differently is the commonest
reason a fresh checkout disagrees with CI, and the honest fix is to read `requirements.txt` rather
than to trust a tick.

**Anything about the models themselves.** Every check in this chapter is about whether the
machinery runs. A model can pass every one of them and still be a bad description of your system,
which is what the remaining twenty-two chapters are for.

## Problems

Two, in `tests/prerequisites_and_setup/`. Both are about the toolchain rather than about sizing,
because everything the rest of the book claims rests on the thing that refuses a bad model on your
machine being the same thing that refuses it in CI.

**0.1 — The smallest model that builds.**
Write a model file with one input and one derived node that passes the loader, the dimensional
pass and every rule in `scripts/verify-models.py`. Read the rules before you start; the refusals
are the point.

```bash
python3 -m pytest tests/prerequisites_and_setup/test_problem_1_smallest.py
```

**0.2 — Break it on purpose, in the one way that matters.**
Write a second model that loads cleanly and is wrong about units. Not a typo — those fail
immediately and teach nothing. A node that declares a unit its own formula cannot produce, which
is the class of error a spreadsheet cannot see at all.

```bash
python3 -m pytest tests/prerequisites_and_setup/test_problem_2_broken.py
```

## Where to go next

[ch01](#reading-a-model) is the model file itself: four node kinds, what declaring each one
commits you to, and why the build is allowed to refuse your arithmetic.

`AUTHORING_GUIDE.md` in the repository is the rules this book is written under, if you would
rather see them stated than inferred.
