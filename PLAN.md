# PLAN.md — the argument

`bench/outline.py` holds the book's shape as data. This file holds the reasoning: what each part
is for, which decisions are settled, and what the conventions are. When the two disagree, the
outline is right about *what* and this file is right about *why*.

## 1. The question

**How big, how much, and how wrong could I be?**

The third clause is the book. Working out that a service needs some number of hosts is arithmetic.
Knowing what that number is worth — which input it rests on, how far it moves when that input
moves, and what it would take to find out — is the skill that decides whether anybody should act
on it.

## 2. The distinction everything rests on

Taught in [ch01](#what-one-number-hides), demonstrated by the reference models, and enforced by
`scripts/verify-models.py`.

It used to be stated in the front matter, which is where the book this repository was
bootstrapped from put its definitions. That left the idea seven chapters depend on sitting in a
preface, with no problems, nothing the reader could run against it, and no *What this cannot tell
you* — none of which front matter can have. The introduction now says what the book is and points
at the chapter.

**A cost model** has a deterministic structure with uncertain parameters. Its relationships are
accounting identities and physics. Cost scales roughly in proportion to its inputs. Monte Carlo
over the inputs is sufficient. It can be wrong because a price was wrong; it is rarely wrong
because it changed shape.

**A sizing model** has the same structure and adds two things:

- **Measured constants** — empirical, stack- and version-specific, with measurement error and
  provenance. A chain of multiplications built on them inherits all of that.
- **Non-linear ceilings** — the queueing knee, rebuild under failure, cardinality explosion, a
  working set spilling past memory. Regime changes, which a chain of multiplications cannot
  represent at all.

So a sizing model needs headroom rules, not just a number. In the DSL that distinction is
structural: a model with a `measured` node or a `ceiling` node **is** a sizing model, a model with
neither **is** a cost model, and the two are held to different rules by the build. A thesis the
repository does not enforce is a paragraph.

**Sizing comes before cost in the book because cost consumes sizing's output.** Parts I–III
produce a number; Part IV establishes what it is worth; Part V prices it.

## 3. Why Monte Carlo is where it is

Part IV sits between sizing and cost, and not at the front, because the method is not useful until
the reader has a number they cannot defend and can feel that they cannot defend it.
[ch12](#the-sizing-model) produces that number. [ch13](#monte-carlo) opens on it.

It is two chapters rather than one because the natural seam is real: [ch13](#monte-carlo) ends
having assumed that every input moves on its own, and [ch14](#correlation-and-convergence) opens
on exactly that. Each gets its own *What this cannot tell you* — [ch13](#monte-carlo)'s is about the shapes
you chose, [ch14](#correlation-and-convergence)'s is about structural error — and neither section would have survived being merged.

## 4. Settled decisions

**Python, Pint and YAML, exporting JSON to a static browser page.** Squiggle was considered and
rejected: no units, so the build cannot refuse a dimensional error; Monte Carlo is a builtin the
reader cannot read; and node kind, provenance and stamped backing have nowhere to live. marimo was
considered and rejected as a foundation: its DAG is a notebook dependency graph, not a domain
model, so the DSL would still have to exist underneath — and a Pyodide bundle is tens of megabytes
on a book page.

**Pint at build time only.** Unit-bearing arrays across a hundred nodes and a hundred thousand
samples are slow, and a units library in the middle of `sizing/mc.py` would be answering a
question nobody asked. Formulas are checked dimensionally, the conversion factor is recorded, and
the evaluator works in plain `float64`. Units are a gate, not a tax.

**Dimensional analysis is not enough; conversion is required.** `USD/TB/year` and `USD/TB/month`
have identical dimensions and differ by twelve. A check that compared only dimensionality would
have published the running example's unit cost twelve times too large and passed.

**The browser gets the evaluator, and on request the first sampler — never a second one.**
Sliders recompute point values instantly, because a point is arithmetic, and the two evaluators
are pinned to each other by `tests/test_viewer.py`, which runs the JavaScript over values Python
computed for every node of every model. Nothing written in JavaScript recomputes an interval: a
second sampler would be a second answer nobody had verified. When a reader wants the interval for
inputs they have moved, the page runs `sizing.mc` itself, under Pyodide, with the same seed — and
first shows them that with nothing moved it gives back the stamped result to a part in a billion.
A moved slider is a scenario override: the input is held rather than drawn, and what comes back
is the doubt left in everything else, which is [ch19](#which-input-is-the-answer)'s question
asked by hand.

**Four targets, and only two of them are measurements this repository can take.** `corpus` and
`rig`. An `estate` observation is taken by a person with access to a running system and reviewed
by a human being; that is much weaker than the other two and the pages that use one say so. The
fourth, `model`, is not a measurement of anything outside the repository at all — it is what a
model file said when the build ran it, and keeping it separate is what stops the other three
going soft.

**The running example is a web service and its data, on a fleet of Linux hosts.** It replaced a
scale-out storage cluster, for two reasons that editing could not fix. Not everyone in the book's
audience has sized a storage cluster; everyone in it has sized a service and the machines it runs
on. And the cluster sat too close to systems the author works on for a reader who knows that to
take *vendor-neutral by construction* on trust — neutrality has to be true of the example, not
only of the words.

The host is the unit and the fleet is what gets costed. Requests arrive and data accumulates; the
host's spec sheet is the first number somebody else supplied; growth gets its shape. Part II stops
being a side model: Little's law, the knee, what more cores buy and a working set outgrowing memory
are stages of the same file, so the reader watches the graph grow through the ceilings rather
than switching models to meet them — and the model becomes a sizing model when the first ceiling
arrives, in Part II, not when the measured constant does. Capacity is disk, with the stored
records' compression as the measured constant. Three chains ask for a host count and one binds.
A host dies and the survivors absorb its load, which is a better headroom rule than rebuild. N
hosts over five years with power and a per-core licence carry Part V, and the same fleet has two
honest unit costs, per request and per stored terabyte. It subsumes the request-serving tier;
the observability platform keeps its job as the model with a hole in it.

One constant in it is a rate. CPU time per request belongs to the `rig` target and no rig is
declared, so until one is, it is held as a labelled claim whose source says what a rig would
replace it with — the honesty the service tier's throughput already has. The day a machine is
declared in `rig/machine.yml`, that node becomes measured, and the running example is the first
model in the book measured end to end. The storage cluster could never have been: nobody has one
to hand, and everybody has a host.

The switch landed in three moves, so that `main` was never half-swapped: the new model was built
beside the old until every stage loaded, classified and stamped; every chapter, figure,
experiment and test moved in one change; the old models go in a third, which NEXT_STEPS.md
carries.

**No vendor is named, anywhere.** A measured constant names the *implementation* it belongs to —
which for the metrics encoder is this repository's own — because that is what makes it a
measurement rather than a claim.

## 5. The five-part chapter shape

Every chapter, every time. The repetition is what makes the book read as one book. The headings
live in `bench.outline.CHAPTER_SHAPE` and `tests/test_book.py` holds every chapter to them.

1. **The question** — one paragraph. What this chapter answers, and why the previous one leaves it
   open.
2. **The material** — the body. Short sections. Code and models quoted from the working tree, and
   generated fragments included where the prose needs them.
3. **What this cannot tell you** — **mandatory**, and for a chapter with a model in it, it must
   name what the *structure* omits.
4. **Problems** — each a stub under `tests/<chapter-slug>/` with a test that passes only when
   solved, or, where the reader's own system is the subject and no oracle exists, a statement of
   what a good answer contains and what would falsify it. CLAUDE.md invariant 5.
5. **Where to go next** — primary sources via `@citekey`.

Two sections have gone, both inherited from the book this was bootstrapped from and neither
missed. A collapsed table at the top gave prerequisites, outputs and sources: a reader does not
open it, every figure already carries its own source line, and for sixteen chapters the
prerequisite was "the previous one". A trailing **What the model says** collected the generated
fragments: twenty-one chapters were written and twenty of them put those fragments where the
argument needed them instead, which reads better. The data behind both stays in
`bench/outline.py`, where the tests can check it.

## 6. Conventions

- British English, direct, active voice, short sentences. No "in this chapter we will".
- Statistics vocabulary is rationed to six words: distribution, sample, percentile, interval,
  correlation, convergence. Each arrives because a model raised a question, never as a definition.
  Plain English first, the term second.
- Every figure carries its conditions. Every number carries its provenance.
- Mathematics only where it predicts something the reader then checks.
- Length follows the material. There is no page target, deliberately.
- Identity is the slug; a chapter's number is derived from `bench/outline.py` and never typed into
  a filename, an anchor, a test directory or a figure id.

## 7. What is not modelled, on purpose

Named here so that nobody has to guess whether it was forgotten.

- **Tax, depreciation schedules and discount rates.** They are jurisdiction- and
  company-specific, they change the answer a great deal, and a book that guessed at them would be
  giving financial advice. [ch21](#a-tco-for-finance) says what to hand to somebody who does know.
- **Procurement reality.** Lead times, minimum orders, the discount you get for asking. Real, and
  not a modelling problem.
- **Risk appetite.** The book produces a probability that a ceiling is breached. What probability
  is acceptable is a decision, and [ch21](#a-tco-for-finance) is about presenting it rather than
  making it.
- **Fitting distributions to data.** Nothing in this repository reads a dataset and tells you what
  shape it is. Choosing a shape is an editorial act with provenance attached, and a function that
  guessed it would produce a model whose central assumption nobody ever wrote down.
