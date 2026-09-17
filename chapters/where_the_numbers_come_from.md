---
title: "Where the numbers come from"
short_title: "ch02 Where the numbers come from"
---

(where-the-numbers-come-from)=
# ch02 · Where the numbers come from

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch01](#what-a-workload-is) |
| **What it produces** | The model's first vendor claim, every measured constant in the book, and a provenance census |
| **Built from** | `storage_cluster_provenance-reference`, `logs-line-bytes`, `metrics-sample-bytes`, `traces-span-bytes`, `storage-object-compression` |
:::

## The question

What is the difference between a number you measured, a number you were told, and a number you
decided?

Once they are all cells in the same column, none. That is the problem.

## The material

### Three claims, wearing the same clothes

Every input in this book declares which of three things it is.

**`fact`** — traceable to something. A stamped measurement, an invoice, a published specification.
The build refuses a `fact` whose source cites nothing, because an assumption wearing a better label
is worse than an assumption.

**`vendor_claim`** — stated by somebody selling it. Often true. Never checked here. It is coloured
differently in every figure it appears in and it is never quietly promoted, because the moment a
quoted throughput becomes "the throughput" in somebody's head, the model has acquired a fact it
never earned.

**`assumption`** — a decision this model makes. Naming it as one is what lets a reviewer argue
with it. An assumption nobody can find is not a weaker claim than a measurement; it is a stronger
one, because nothing can dislodge it.

### The first number somebody else supplied

Every quantity in [ch01](#what-a-workload-is)'s file came from you or from the application: how
much is held, how fast it grows, how long the cluster has to last. The next one does not. How much
a drive holds is decided by whoever sells it, and this is the form that takes:

```{literalinclude} ../models/storage_cluster/stages/02-provenance/model.yaml
:language: yaml
:start-at: drive_capacity:
:end-before: drives_per_node:
```

Two sentences of source, and the second one earns its place. *Decimal TB, not TiB* is the gap
between what a datasheet counts and what a filesystem counts, and it runs in the direction that
makes the cluster smaller than the spreadsheet promised ([Appendix D](#appendix-d-units)). Writing
that down is the whole of the discipline: the claim is recorded as a claim, and what is doubtful
about it is recorded beside it.

It takes one more decision — how many of those drives go in a chassis — to reach the first
quantity in the model that is about hardware rather than about data:

```{include} _generated/where-the-numbers-come-from-stage.md
```

```{include} _generated/where-the-numbers-come-from-stage-shape.md
```

Still a cost model. A vendor's claim is a claim about a number, and this book's distinction is not
about who said a number — it is about whether the arithmetic around it stops applying somewhere.
[ch08](#capacity) is where that changes.

### Three claims, counted

Here is the census of the observability model, which is finished and therefore has all three:

```{include} _generated/where-the-numbers-come-from-provenance.md
```

The tally at the bottom is the honest summary of any model, and for most models it is not
flattering. That is fine. Not knowing is not.

### A measured constant is not a fact about the world

A compression ratio is not a property of compression. It is a property of *some data* and *some
software at some version*, and it will move when either changes. So will bytes per sample, spans
per request, and throughput per core. This book calls those **measured constants** and gives them
their own node kind, and every one of them carries the implementation it belongs to:

```{include} _generated/where-the-numbers-come-from-constants.md
```

Read the last column. One of those constants was produced by an encoder that lives in this
repository: this book's own, byte-aligned, and therefore worse than a production format that packs
bits. The figure is correct and it is about that encoder. Anybody who copied it into a model of a
real system would be wrong by a factor nobody would ever find.

The method is what transfers. The number does not.

### Four targets, and only two of them are yours to take

| Target | What it is | Who can check it |
|---|---|---|
| `corpus` | a codec or an encoder over a declared body of data | anybody, and CI does, on every push |
| `model` | a model file evaluated and sampled | anybody with the repository |
| `rig` | a throughput or a latency, on the declared reference machine | whoever has that machine |
| `estate` | an observation of a system somebody runs | **nobody** |

The first two are cheap and the book is full of them. The third is refused on any machine that is
not the declared one, because a throughput measured on a shared CI runner is indistinguishable
from a real one once it is a number in a table.

The fourth cannot be checked by anybody at all.

### The target the build cannot check

An observation of a running system cannot be reproduced by anybody, including you, next Tuesday.
There is no corpus to re-run and no machine to re-run it on. The system has moved on.

So `estate` is held to the strictest disclosure rules in the book — what system, over what window,
observed when — and that disclosure is the *whole* of its verification. There is nothing else.
When a page uses one, it says so at the point of use rather than in a footnote, because a reader
is entitled to know which numbers on a page are the ones that rest on somebody's word.

This is not a hole in the scheme. It is the honest bottom of it. Some quantities are only
knowable by watching a real system, and pretending otherwise would be worse than admitting it.

### When nobody has measured it

```{include} _generated/where-the-numbers-come-from-measured.md
```

Two rows there say *not yet measured*. One needs a reference machine nobody has attached; the
other needs somebody's instrumented application.

The node has no value, so nothing downstream of it has a value either, and the state propagates
down the graph without anybody marking anything:

```{include} _generated/where-the-numbers-come-from-unmeasured.md
```

No placeholder. No estimate. No number borrowed from a different stack and quietly rounded. The
figures that depend on those constants are absent, and the box says which constants and what would
close them.

That is inconvenient on purpose. A placeholder is indistinguishable from a measurement after one
copy-paste, and every organisation has a capacity plan built on one.

### The rig, and why the book will not let you fake it

```{include} _generated/where-the-numbers-come-from-rig.md
```

The machine this was written on refuses to produce that figure. So does CI. Not by convention —
`bench.stamp.require_rig` compares the running processor and core count against a declared
reference machine and raises otherwise.

An environment variable would have been easier and would have let anybody stamp a laptop timing as
a reference measurement by typing four characters. A target you can set by accident is not worth
having.

### What a measurement is worth

One measurement is a number. It says nothing about how far it would move if you did it again, so
every constant in this book is measured over several independently generated shards and reported
as a mean with the standard error of that mean beside it.

That standard error becomes the measured node's uncertainty, and [ch12](#monte-carlo) propagates
it through the model like any other. A constant stamped without one is claiming to have been
measured exactly, and the build says so.

A standard error also tells you what more measuring would buy, which is usually less than people
expect. It falls as one over the square root of the count: halving it costs four times the work.
Problem 2.2 is that arithmetic, and it is worth doing *before* agreeing to a measurement campaign
rather than during one.

## What this cannot tell you

**Whether a corpus resembles your data.** Every constant above was measured over a body of data
this repository generates, and the generator's proportions are an assumption stated in the
stamped result. For the storage compression ratio, that mixture is the single largest source of
error in the figure — larger than the codec, larger than the shard-to-shard spread it reports.
The number has a standard error and the standard error is about the wrong thing.

**Whether a `vendor_claim` is true.** Nothing here checks one. They are marked so that a reader
can see how much of a model rests on them, and that is all. Where a vendor's number and a measured
one exist side by side, [Appendix F](#appendix-f-observability-model) shows both; where only the
claim exists, that is what you have.

**Whether an `estate` observation happened.** It is somebody's word, with a disclosure attached.
The book's position is that saying so plainly is better than the alternative, not that it is good.

**Whether an assumption is reasonable.** The provenance census counts them. It does not read them.
A model can be all assumptions, all sourced, all defensible-sounding, and completely wrong.

## Problems

Two, in `tests/where_the_numbers_come_from/`.

**2.1 — Take a constant, and stamp it so somebody else could check it.**
Pick a quantity a codec decides, measure it over a corpus you generate deterministically, and
produce a stamped payload that satisfies every rule in `bench.stamp.provenance_problems` — corpus,
codec, units with no time in them, and a standard error that came from somewhere.

```bash
python3 -m pytest tests/where_the_numbers_come_from/test_problem_1_measure.py
```

**2.2 — What would it cost to be more sure?**
Given a standard error at some number of shards, work out how many shards a target would need.
Halving your uncertainty costs four times the measuring, and knowing that before the campaign is
worth more than knowing it during one.

```bash
python3 -m pytest tests/where_the_numbers_come_from/test_problem_2_shards.py
```

## Where to go next

[ch03](#peak-mean-and-growth) is about the input that does the most damage in this book and is
the hardest to measure: a growth rate is a claim about the future, and no amount of provenance
discipline turns one into a measurement.

[ch12](#monte-carlo) is what to do with a standard error once you have one.
