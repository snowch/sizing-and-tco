---
title: "Introduction"
short_title: Introduction
---

(preface)=
# Introduction

*How to size a system, cost it, and know how much to trust the answer.*

## You have been asked for a number

Somebody has asked you how big the system needs to be. How many machines, how much storage, how
much it will cost to run for the next three years — and they are going to spend real money on
whatever you tell them.

You can do the arithmetic. That is rarely the hard part. What comes out is one number, and that
number says nothing at all about how much of it you would actually bet.

**How big, how much, and how wrong could I be?**

Three questions, and the first two are arithmetic. **Sizing** is how much hardware a stated
workload needs, and where it stops coping. **Total cost of ownership** is what that hardware
costs over the years you keep it, which is not the same as what it costs to buy. Most people can
do both.

This book teaches the third: how to find which input your answer rests on, how far the answer
moves when that input moves, and what it would cost to find out. Almost nobody is taught this,
and it is what decides whether anybody should act on your number.

## Why point estimates lie

A **point estimate** is the number you get by choosing one value for every input and doing the
arithmetic once. It is what a spreadsheet gives you, and it is what almost every sizing
conversation is about. The tables in this book put it in a column of that name.

Point estimates do not lie by being wrong. They lie by being *silent*.

Take a storage cluster with a stated workload and size it that way. This book has a model that
does exactly that, and a model here is a text file of named quantities — how much data arrives,
how well it compresses, how many copies you keep, what a drive holds — each one feeding the next
until the chain reaches a number of machines. It recommends a node count. Buy that many.

Now let every input be as uncertain as it honestly is — the growth rate is a forecast, the
compression ratio was measured on somebody else's data, the price is a quote that expires — and
ask the same model the same question. It no longer gives one answer.

```{include} chapters/_generated/preface-storage-outputs.md
```

Read the *nodes the model recommends* row. Its point estimate is a real number, correctly
computed. Beside it is the **90% interval** — the range nine runs in ten landed in, once every
input was allowed to vary as far as it honestly might — and it spans most of an order of
magnitude. Nothing in the first calculation was wrong. It
simply had no way to mention that it was a bet.

The italic line under that table appears under every one in this book, and it is a link. It names
the stamped result the figure was rendered from — `storage_cluster-reference` is the storage model
at its reference scenario — and following it gets you the file itself: every input, the seed, the
sample count, the conditions the run held under, and a hash of the code that did the arithmetic.
Change that code and the hash changes, and the build refuses to publish a figure that no longer
matches what the repository computes. The link is there so you can check the table instead of
trusting it.

% number-ok: settings this book chose, not figures it measured. Stated once because they never vary, and tests/test_book.py fails if they do.
Every model run in this book draws 100,000 samples from seed 20260916, which is why neither
appears under the tables. A test fails if that ever stops being true.

```{image} chapters/_figures/preface-tco-distribution.svg
:alt: The five-year total cost as a distribution, with the point estimate marked on it
:width: 100%
```

The red line is where the point estimate falls. Everything else is the same model, told the truth
about its own inputs.

The method that produced the interval is [ch12](#monte-carlo)'s, not this page's. It is no use to
you until you have built a model, got a number out of it, and felt that you could not defend the
number.

## Why the interval was that wide

Because that was not a cost model. It was a sizing model, and the two fail differently. This is
the distinction the rest of the book is built on, and the one the toolkit encodes.

**A cost model has a deterministic structure with uncertain parameters.** Its relationships are
accounting identities and physics: watts times hours times price, capital plus running cost over
a horizon, a total divided by a denominator. Nothing in that structure is in doubt. Only the
inputs are uncertain, cost scales roughly in proportion to them, and sampling the inputs is
genuinely sufficient. A cost model can be wrong because a price was wrong. It is rarely wrong
because the system it describes started behaving differently.

**A sizing model has the same structure and adds two things.**

*Measured constants.* Bytes per sample after compression. Spans per request. Throughput per
collector core. These are empirical, they belong to a particular implementation at a particular
version, they have measurement error, and none of them is a fact about the world. A chain of
multiplications built on them inherits every one of those properties, and a model that treats
them as constants hides them all.

*Non-linear ceilings.* The queueing knee, where response time climbs long before a device is
busy. Rebuild under failure, where losing one node costs capacity you were using. Cardinality
explosions, where one label multiplies a series count by a number nobody chose. A working set
spilling out of memory. These are regime changes, and **a chain of multiplications cannot model
a regime change**. It will happily report that a system is running at several times its own
limit, which is not a description of anything that can happen.

So a sizing model needs headroom rules, not just a number. That distinction is the argument of the
book, so the toolkit enforces it rather than asserting it: a model with a measured constant or a
declared ceiling in it **is** a sizing model, a model with neither **is** a cost model, and
`scripts/verify-models.py` holds the two to different rules. A sizing model that declares a limit
with no margin does not build.

## Why you should believe any of it

You have just been shown a wide interval and invited to act on it. The rule underneath this book
is that nothing is asserted here that the repository could check instead. That rule shows up in
three ways.

**Every number says where it came from.** No figure is typed into the prose. Each one comes from
a stamped result recording what produced it, the conditions it holds under, and a hash of the code
that made it. When a quoted figure stops matching what the repository computes, the build fails.

**Every model is a file, not a spreadsheet.** Every quantity in it declares a unit, so the build can refuse a model that multiplies the
wrong two things. Every input declares whether it is a fact, a vendor's claim or somebody's
assumption, and an uncertain one has to say what shape its uncertainty has and why that shape
rather than another. Every measured constant names the measurement behind it.
[ch02](#where-the-numbers-come-from) says what those distinctions are worth;
[Appendix A](#appendix-a-dsl-reference) is the file format that holds them.

**Every chapter ends by saying what it cannot tell you.** A section with that name is required,
and the tests fail a chapter that leaves it out. In a book about estimates it is usually the most
useful part of the chapter.

One consequence of those rules shows up on the pages. When a constant has not been measured, the
node that needs it has no value, and neither does anything downstream of it. Those figures render
as *not yet measured* and the affected chain is named — never a placeholder, and never a number
borrowed from a different stack. [Appendix F](#appendix-f-observability-model) publishes one of
those figures, which is a deliberate choice and is argued there.

## Who this book is for

A self-study text and a toolkit, for an engineer who has been asked how big something needs to
be, or what it will cost, and who wants to give an answer they would still defend a year later.

You should be comfortable with code and with arithmetic. You are assumed to know **nothing**
about statistics. [ch12](#monte-carlo) and [ch13](#correlation-and-convergence) introduce the
six words you need — distribution, sample, percentile, interval, correlation,
convergence — one at a time, each one arriving because a model has just raised a question that
needs it. Where a statistical term has a plain-English equivalent, this book uses the plain one
first and names the term second.

No vendor is named anywhere in this book, and no product is recommended. Three models carry it,
all written so that the structure is the point and the numbers are yours to replace: a scale-out
storage cluster, which is sized and costed end to end; an observability platform, which is the one
with a hole in it where a measurement should be; and a request-serving tier, which is the only one
of the three that is not a chain of multiplications, and therefore the one Part II is built on.

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
The toolkit is complete, all three models run end to end, and every chapter and appendix is
written.

**[Download the whole book as a PDF](/sizing-and-tco.pdf)** — every chapter and appendix in one
file, built from the same source as this site, so the two cannot disagree about what a page says.

Two constants are not yet measured — collector throughput per core, which needs a reference
machine, and spans per request, which needs somebody's instrumented application. The observability
model shows both as missing rather than guessing, which is what the rest of the book asks of any
model.

```{include} chapters/_generated/build.md
```
:::
