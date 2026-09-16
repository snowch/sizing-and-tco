# Authoring Guide

How to write a page of *Sizing and TCO* without breaking the three things that make the book worth
reading: numbers that say where they came from, models the build re-runs, and problems that cannot
lie about whether you solved them.

## Quick start

```bash
python3 -m pip install -r requirements.txt -r requirements-dev.txt
npm install -g "mystmd@$(node -p "require('./package.json').devDependencies.mystmd")"
pre-commit install

make machine   # what this computer is, and what it may measure
make book      # live preview at localhost:3000
make check     # exactly what CI runs
```

`python3 -m pip`, not a standalone tool install: `python3 -m pytest` has to work, and a pipx or uv
`pytest` has its own environment and cannot import `sizing`.

## The order to write in

Not the order the chapter is read in.

1. **The problems, and their tests.** Before any prose. Make each one fail, and read the failure —
   it is the first thing a reader will see, and it should tell them what to do rather than what
   went wrong. Mark the reader's assertions `@pytest.mark.problem`.
2. **The scaffolding tests.** Unmarked, beside the problems: the oracle is real, the cases are not
   all the same case, the fixture still contradicts the observation. CI runs these and deselects
   the problems. The book is responsible for handing the reader a problem that works.
3. **The model.** Into `models/<name>/model.yaml`, with a scenario. `make verify` must pass before
   anything is written about it.
4. **The runner and the figures.** A stamped result, and an entry per figure in
   `bench/figures.py`.
5. **The chapter**, to serve all of the above.

Writing the prose first produces a chapter that explains what you meant to model.

## The seven-part shape

PLAN.md §5, and it is not negotiable — the repetition is what makes twenty-three chapters read as
one book. `python3 scripts/new-chapter.py <slug>` generates the shape with the question,
prerequisites and owed figures already filled in from `bench/outline.py`.

The section that matters most is the fifth: **What this cannot tell you**. It is the easiest to
skip and the one that makes the other six believable. For a chapter with a model in it, it must
name **what the model's structure omits** — because that is the error no amount of sampling can
see, and a chapter that only lists its input uncertainties has described the easy half.

## Five rules that are not negotiable

### Never type a number into prose

Numbers come from `bench/results/*.json`. Declare the figure in `bench/figures.py`, render it, and
include the fragment:

```bash
python3 scripts/render-figures.py           # write the fragments and diagrams
python3 scripts/render-figures.py --check   # fail if a committed one is stale
```

````markdown
```{include} _generated/monte-carlo-ceilings.md
```
````

`scripts/verify-numbers.py` scans every published page for a figure carrying a cost, size or
speed unit and fails the build. If it is a definition rather than a measurement — the name of an
interval convention, say — put `% number-ok: <reason>` on the line before, so the exemption and
its reason are visible in review.

The check will catch you. It caught the outline's own chapter question, which had a node count in
it, on the day it was written.

### Never paste code into prose

Quote it from the working tree, so it cannot drift:

````markdown
```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def triangular_ppf
:end-before: def lognormal_ppf
```
````

Anchor on `:start-at:` / `:end-before:` **text**, never `:lines:` — line numbers rot on the first
edit above them, and `tests/test_book.py` fails a page that uses them. Model files are quoted the
same way.

### Never invent a figure you have not measured

There is usually nothing to do here, because the state propagates: a `measured` node with no
stamped result has no value, everything downstream of it has no value, and the tables render
*not yet measured* with the responsible constants named. Write the prose around it as though the
numbers were there, so that landing them is a one-command change rather than a rewrite.

`pending=` in `bench/figures.py` remains for the case the graph cannot see: a figure whose whole
result file does not exist because the experiment has not been run on the machine it needs.
`verify-numbers.py` fails if a pending figure's result has landed, so a measurement that arrives
cannot be left marked as missing.

### Never let a target answer another one's question

A `corpus` result may carry no figure with time in its units; `bench.stamp` checks it
dimensionally and refuses. A `rig` measurement is refused on any machine that is not the one
declared in `rig/machine.yml`. An `estate` observation must disclose the system and the window,
because nothing else can check it.

If you want a rough idea of how fast something is and you are not on the rig: that number
describes your laptop.

### Never let a model hide what it is

Every input carries a provenance kind and a non-empty source. Every ceiling carries a headroom and
a reason. Every measured constant carries a standard error and the implementation it belongs to.
`scripts/verify-models.py` checks all of it, and the checks exist because each one is a thing that
is invisible from inside a spreadsheet and expensive from outside one.

State what *changes* on a different stack, not merely that something does. "Assumes zstd" is a
warning. "A different codec moves this constant and nothing else in the chain" is useful.

## Figures

Two kinds, both declared in `bench/figures.py` and both rendered by `scripts/render-figures.py`:

| Kind | What it is | Where it comes from |
|---|---|---|
| `Table` | A markdown table | one stamped result, via a renderer in `bench/tables.py` |
| `Diagram` | An SVG | a function in `bench/diagrams.py`, drawn deterministically |

Diagrams are drawn by code, as SVG, deterministically. Not matplotlib: its output embeds font
paths and a version, so `--check` would fail on an upgrade that changed nothing visible, and a
check people learn to ignore is worse than no check.

Every figure must show a mechanism. If it would still make sense with the labels removed, it is
decoration.

### When to draw one

| Draw it | Write it |
|---|---|
| What depends on what: a model's graph, a chain of multiplications | Why it depends on it |
| How uncertain something is: a distribution, an interval, a tornado | What you would do about it |
| Two arrangements of the same model, side by side | Which one you should prefer, and when |
| Where a ceiling sits relative to a plan | What breaks when it is crossed |

The conditions line under a figure is not optional garnish. A figure makes a claim, and that line
is where the claim is bounded — *this corpus, this codec*, *this scenario, this seed*. A figure
with no stated conditions is the visual form of a number with no provenance.

## Problems

A problem is a stub the reader edits and a test that passes only when they are right.

- Put the stub and its test in `tests/<chapter-slug>/`. The stub's docstring is the problem
  statement; the chapter's Problems section is the invitation.
- Make failure messages teach. `assert measured == expected` tells a reader nothing; "if your
  ratio is near 1.0 you are probably measuring the interval width, which does not shrink" tells
  them where to look.
- **Derive the expected answer at test time**, from the problem's own terms — the parameters of a
  distribution, a law, an observation the model does not contain. Never store it.
- Write an unmarked scaffolding test beside each problem asserting that it is answerable and not
  trivially answerable. CI runs those. One of ours failed on the day it was written, because the
  "observed" figure was inside the interval the reader was supposed to be unable to reach.
- Never write the answer anywhere in the repository. The test is the answer key, and it runs.

## Definition of done

- [ ] Problems written **first**, each failing for the right reason, marked `problem`
- [ ] Scaffolding tests beside them, unmarked, proving the problems are answerable
- [ ] Model merged, passing `make verify`
- [ ] Every figure declared in `bench/figures.py` and rendered from a stamped result
- [ ] *What this cannot tell you* written, naming what the structure omits
- [ ] Cross-references and citations resolve; `./scripts/ci-check.sh` clean
- [ ] `[DRAFT]` removed

Not when it reaches a length. There is no page target: judge a section at a time.
