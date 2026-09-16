---
title: "Sizing and TCO"
short_title: Preface
---

(preface)=
# Sizing and TCO

*Capacity planning, sizing and total cost of ownership, modelled as code.*

## What this book is

A self-study text and a toolkit, built around one question and one rule about answering it.

The rule first: nothing is asserted here that the repository could check instead. Three things
follow from it.

**Every number says where it came from.** No figure is typed into the prose. Each one comes from
a stamped result recording what produced it, the conditions it holds under, and a hash of the code
that made it. When a quoted figure stops matching what the repository computes, the build fails.
Where a measurement has not been taken, the page says so in a box rather than showing a
plausible-looking placeholder.

**Every model is a file, not a spreadsheet.** A model here is a graph of named quantities in a
text file. Every quantity declares a unit, so the build can refuse a model that multiplies the
wrong two things. Every input declares whether it is a fact, a vendor's claim or somebody's
assumption, and an uncertain one has to say what shape its uncertainty has and why that shape
rather than another. Every measured constant names the measurement behind it. The build re-runs
all of it, and the figures in these pages are what it computed.

**Every chapter ends by saying what it cannot tell you.** A section with that name is required,
and the tests fail a chapter that leaves it out. In a book about estimates it is usually the most
useful part of the chapter.

## The question this book keeps asking

**How big, how much, and how wrong could I be?**

The third part is what the book is for. Working out how many nodes a cluster needs is arithmetic,
and most people can do it. Knowing how much to trust the answer — which input it rests on, how far
it moves when that input moves, and what it would take to find out — is a different skill, and it
is the one that decides whether anybody should act on it.

## Why point estimates lie

Not because they are wrong. Because they are *silent*.

Take a storage cluster with a stated workload and size it the usual way: take the expected value
of every input, multiply along the chain, and read off the answer. The model in this book does
exactly that, and recommends a node count. Buy that many.

Now let every input be as uncertain as it honestly is — the growth rate is a forecast, the
compression ratio was measured on somebody else's data, the price is a quote that expires — and
ask the same model the same question. It no longer gives one answer. It gives a distribution, and
the number you were about to act on sits somewhere in it.

```{include} chapters/_generated/preface-storage-outputs.md
```

The row that matters is the node count. The point estimate is a real number, correctly computed,
and the interval beside it spans most of an order of magnitude. Nothing in the first calculation
was wrong. It simply had no way to mention that it was a bet.

```{image} chapters/_figures/preface-tco-distribution.svg
:alt: The five-year total cost as a distribution, with the point estimate marked on it
:width: 100%
```

The red line is where the point estimate falls. Everything else is the same model, told the truth
about its own inputs.

That is the whole motivation, and this book does not teach the method until
[ch13](#monte-carlo) — because the method is not useful until you have a model that has produced
a number you cannot defend, and you can feel that you cannot defend it.

## A TCO and a sizing are not the same problem

The distinction the rest of the book is built on, and the one the toolkit encodes.

**A TCO has a deterministic structure with uncertain parameters.** Its relationships are
accounting identities and physics: watts times hours times price, capital plus running cost over
a horizon, a total divided by a denominator. Nothing in that structure is in doubt. Only the
inputs are uncertain, cost scales roughly in proportion to them, and sampling the inputs is
genuinely sufficient. A cost model can be wrong because a price was wrong. It is rarely wrong
because it changed shape.

**Sizing has the same known structure and adds two things.**

*Measured constants.* Bytes per sample after compression. Spans per request. Throughput per
collector core. These are empirical, they belong to a particular implementation at a particular
version, they have measurement error, and none of them is a fact about the world. A chain of
multiplications built on them inherits every one of those properties, and a model that treats
them as constants is hiding the most interesting thing about itself.

*Non-linear ceilings.* The queueing knee, where response time climbs long before a device is
busy. Rebuild under failure, where losing one node costs capacity you were using. Cardinality
explosions, where one label multiplies a series count by a number nobody chose. A working set
spilling out of memory. These are regime changes, and **a chain of multiplications cannot model
a regime change**. It will happily report that a system is running at some
multiple of a limit, which is not a description of anything that can happen.

So a sizing model needs headroom rules, not just a number. And because that distinction is the
argument of the book, the toolkit makes it structural rather than rhetorical: a model with a
measured constant or a declared ceiling in it **is** a sizing model, a model with neither **is** a
cost model, and `scripts/verify-models.py` holds the two to different rules. A sizing model that
declares a limit with no margin does not build. The front matter's central claim is something
this repository checks, not something you have to take on trust.

## How the numbers work

Four kinds of number, and each is allowed to claim something different.

| | What it is | What checks it |
|---|---|---|
| `fact` | Traceable to a stamped measurement, an invoice or a published specification | The build, which refuses a `fact` that cites nothing |
| `vendor_claim` | Stated by someone selling it. Often true, unverified here | Nothing. It is marked in every figure it appears in and never promoted |
| `assumption` | A decision this model makes | A reviewer, which is why the source string has to say enough to argue with |
| *measured* | An empirical constant with a standard error and a named implementation | A runner that CI re-executes on every push |

Numbers come from four targets, and the split runs through everything. Three of them are
measurements — something outside this repository was asked a question. The fourth is not:

- **`corpus`** — a deterministic measurement over a declared body of data with a named codec.
  Reproducible on any machine, re-derived by CI on every push, and never allowed to carry a rate
  or a duration. How fast a codec ran is a property of the computer that ran it.
- **`rig`** — a throughput or latency figure, taken natively on a declared reference machine and
  refused anywhere else.
- **`estate`** — an observation of a running system. Reproducible by nobody, checkable by
  nobody, and therefore held to the strictest disclosure rules in the book. Where a chapter uses
  one, it says so at the point of use.
- **`model`** — computed from a model file here. No machine and no data were involved, so it is
  evidence about what this book's own models say and about nothing else. Every figure that comes
  out of a model run or a sweep is stamped this way, and its fingerprint covers the sampler and
  the evaluator — so a change to the method invalidates the claim, which is the point.

When a constant has not been measured, the node that needs it has no value, and neither does
anything downstream of it. Those figures render as *not yet measured* and the affected chain is
named — never a placeholder, and never a number borrowed from a different stack.
[Appendix F](#appendix-f-observability-model) has one on a published page, which is a deliberate
choice and is argued there.

## Who it is for

An engineer who has been asked how big something needs to be, or what it will cost, and who
wants to give an answer they would still defend a year later.

You should be comfortable with code and with arithmetic. You are assumed to know **nothing**
about statistics. [ch13](#monte-carlo) and [ch14](#correlation-and-convergence) introduce the
six words you need — distribution, sample, percentile, interval, correlation,
convergence — one at a time, each one arriving because a model has just raised a question that
needs it. Where a statistical term has a plain-English equivalent, this book uses the plain one
first and names the term second.

No vendor is named anywhere in this book, and no product is recommended. The two worked models
are a scale-out storage cluster and an observability platform, and both are written so that the
structure is the point and the numbers are yours to replace.

## What you will need

Python, Node for the book build, and about twenty minutes:

```bash
python3 -m pip install -r requirements.txt -r requirements-dev.txt
npm install -g "mystmd@$(node -p "require('./package.json').devDependencies.mystmd")"

make models     # evaluate every model and stamp what it said
make check      # exactly what CI runs
make book       # live preview at localhost:3000
```

Nothing in this book needs a datacentre, a cloud account, or a licence. The one thing it cannot
do on your laptop is take a `rig` measurement, and it refuses to pretend otherwise.

:::{note} Where this book is
The toolkit is complete, both reference models run end to end, and every chapter and appendix is
written.

**[Download the whole book as a PDF](/sizing-and-tco.pdf)** — every chapter and appendix in one
file, built from the same source as this site, so the two cannot disagree about what a page says.

Two constants are not yet measured — collector throughput per core, which needs a reference
machine, and spans per request, which needs somebody's instrumented application. The observability
model shows both as missing rather than guessing, which is the behaviour the rest of the book is
about.
:::
