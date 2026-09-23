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

## The six-part shape

`bench.outline.CHAPTER_SHAPE`, PLAN.md §5, and it is not negotiable — the repetition is what makes
every chapter read as one book. `python3 scripts/new-chapter.py <slug>` generates the shape with
the question already filled in from `bench/outline.py`, and `tests/test_book.py` fails a chapter
that grows a seventh heading or loses one. A section a chapter needs and the shape does not have
is a subsection of **The material**.

**Key takeaways** follows the material: a short list of what the reader should carry away. Each
item opens with its claim in bold and says why in a sentence or two. Nothing in it is new. Every
claim was made, and shown, in the material, and the page's outline lists the heading, so a reader
can go straight to it.

The section that matters most is the fourth: **What this cannot tell you**. It is the easiest to
skip and the one that makes the other five believable. For a chapter with a model in it, it must
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

## What no check can catch

Every rule above has a script behind it. Nothing in this section does. Each of these was written,
reviewed, published, and found only when somebody read the page again slowly — so this is a
reading list rather than a lint, and the sentences quoted are the real ones.

The heading deliberately does not say how many. A section called "Seven things" would be an
instance of the first item.

### A claim about the repository's own state

The most reliable way to publish something false. It is true when written and rots silently,
because no check looks at prose describing the repository.

| Published | Actually |
|---|---|
| "all three models run end to end" | the observability model cannot compute three of its thirteen outputs |
| "This page has leaned on three of them loosely" | it leans on one |
| "the one machine this book takes its timings from" | no `rig` result exists and `rig/machine.yml` is absent |

**If the repository can compute it, generate it.** `bench.tables.unmeasured_constants` is the
worked example: it walks every model for a measured node with no result and writes the sentence,
so the count cannot drift and a constant cannot be named after somebody measures it. Declare that
kind of fragment with `computed_from=` rather than a `result`.

If you cannot generate it, ask what makes it true and whether that will still hold in a year. A
status report in a finished book usually answers nothing the reader asked.

### A word that means two things on one page

"Run" meant one trial of the arithmetic, the whole batch of trials, and the stamped execution of a
model — within twenty lines of the introduction, and never defined.

The fix was not a better sentence. It was saying once, before the word appeared, what the thing
was: *the arithmetic done over and over, every answer kept*. After that the page could say "nine
of those answers in ten" and mean something.

Watch for a word this book uses technically — run, node, sample, model, stage, target, figure,
constant — and check it means one thing per page.

### A definite reference to something the reader has not met

> This part starts the web service

*The* web service. The reader has met no service, and you cannot start one anyway. The
definite article is the tell: it promises the reader already has this, and a reader who does not
assumes they missed something.

### A term doing work before it is defined

Page one used "model" from the Source line onwards and then ran a whole taxonomy on it — cost
model, sizing model, which kind you have decides what you are exposed to — with nothing having
said what a model is here.

A term that carries an argument must be defined before the argument, on the same page, in the
plain-English form. The book's rationed vocabulary (PLAN.md) is about which terms are allowed;
this is about where they arrive.

### A table nobody chose

The introduction's outputs table had eight rows because `outputs_table` rendered every output the
model declared, in the model file's own order. It was byte-identical to ch12's. Six of the rows
were a chapter's subject arriving up to nineteen chapters early, and two of them were ceilings
shown without a limit, a verdict or a breach probability — the three columns that make a ceiling
row mean anything.

Ask of every figure: **did somebody choose these rows for this page, or is this the renderer's
default?** A renderer that takes the whole result is right for the chapter that earned it and
wrong everywhere else.

### The same argument twice, far apart

A paragraph under the introduction's first table explained the Source line and why you could trust
it. Eighty lines later, the section that exists to make that argument made it again in one
sentence. The near one was longer, interrupted the table from the figure that paid it off, and
was the one to cut.

Duplication over a screen's distance is invisible while writing and obvious while reading.

### A number spelled as a word

`verify-numbers.py` scans digits, so "seven nodes", "five inputs and two computed" and "fifteen
petabytes" all pass. They are figures typed into prose exactly as much as `7` would be.

Small counts of things on the page — "two rows", "three questions" — are fine. A quantity the
repository measured is not, whichever way you spell it.

## How to read for these

Not while writing. Take a finished page and read it as somebody who has read every page before it
and none after — which is the only way a reader ever arrives — and stop at:

- every sentence stating a fact about this repository
- every word used technically, checked against its other uses on the page
- every "the" in front of a noun the page has not introduced
- every figure, asking who chose its rows
- every paragraph, asking whether the page has already said this

Then read it once more against `STYLE.md`, sentence by sentence. Its final test is the one that
matters: could a competent engineer understand this paragraph on the first reading? If not,
split the sentence or the paragraph. The introduction was rewritten that way, and it is the
example to hold a page against.

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
- **The page runs the test too.** Under each tested problem the chapter page shows the stub's
  function, editable, and Check runs the chapter's own test file under Pyodide over exactly the
  files `sizing.playground.toolkit.problem_files` lists. So a test imports what it grades from
  the chapter's `stubs.py` by name, names every model file and result it reads as a quoted path
  or a literal `load_result("...")`, and `tests/test_problems.py` fails when one is missing. The
  `python3 -m pytest tests/... -m problem` line under the problem is how the page finds the
  test. It is drawn as a one-line note under the Check, for a reader at a desk, not as a block.
  The marker is part of the form: it runs the reader's tests and deselects the scaffolding
  beside them, which is what the Check counts, so a desk and the page give the same verdict.
  Without it a reader is told four of six tests pass before they have typed anything.
- **The form follows what the chapter taught.** A stub takes plain numbers, arrays, dicts or a
  callable the test builds; the test does the loading and evaluating, so the reader never
  drives the toolkit's Python API, which no chapter teaches. Where the chapter taught the model
  file, the artefact is a file: a fragment or a fixture under `tests/<slug>/` that the test names
  in a module-level `EDITABLE` tuple, shows whole and editable in the page, and writes back
  before pytest runs. Ship it with the work left in it, and check that in `tests/test_problems.py`
  rather than in the problem's own test, which the page runs over the reader's copy.

## Definition of done

- [ ] Problems written **first**, each failing for the right reason, marked `problem`
- [ ] Scaffolding tests beside them, unmarked, proving the problems are answerable
- [ ] Model merged, passing `make verify`
- [ ] Every figure declared in `bench/figures.py` and rendered from a stamped result
- [ ] *Key takeaways* written, each claim in bold and each one made in the material first
- [ ] *What this cannot tell you* written, naming what the structure omits
- [ ] Edited against `STYLE.md`: short sentences, one idea per paragraph, the point stated first,
      and its closing checklist run over the page
- [ ] Cross-references and citations resolve; `./scripts/ci-check.sh` clean
- [ ] `[DRAFT]` removed

Not when it reaches a length. There is no page target: judge a section at a time.
