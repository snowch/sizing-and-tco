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
number tells you nothing about how much you would be willing to stake on it.

**How big, how much, and how wrong could I be?**

Three questions, and the first two are arithmetic. **Sizing** is how much hardware a stated
workload needs, and where it stops coping. **Total cost of ownership** is what that hardware
costs over the years you keep it, which is not the same as what it costs to buy. The arithmetic
for both is within anybody's reach. Knowing where that arithmetic stops describing the system is
not, and it is a good part of what follows.

This book teaches the third: how to find which input your answer rests on, how far the answer
moves when that input moves, and what it would cost to find out. Almost nobody is taught this,
and it is what decides whether anybody should act on your number.

## Why point estimates lie

A **point estimate** is the number you get by choosing one value for every input and doing the
arithmetic once. It is what a spreadsheet gives you, and it is what almost every sizing
conversation is about. The tables in this book put it in a column of that name.

Point estimates do not lie by being wrong. They lie by being *silent*.

Think about what went into one. To size a storage cluster you need to know how much data arrives,
how fast that grows, how well it compresses, how many copies you keep, what a drive holds and
what a drive costs. Six numbers, and you know none of them exactly. The growth rate is a
forecast. The compression ratio was measured on somebody else's data. The price is a quote that
expires.

Pick the middle of each, multiply along the chain, and you get one number. The arithmetic is
right. But you never had six numbers — you had six ranges, and you threw the ranges away at the
first step. Worse, multiplying uncertain quantities does not average their doubt out. It compounds
it: each one can be wrong in the same direction as the others, and the answer stretches further
than any single input does.

So the honest answer to *how big* is not a number. It is a range, with some values in it far more
likely than others. You get one by doing the arithmetic over and over — each time picking a
different value for every input, from the spread that input honestly has — and keeping every
answer that comes out. Here is that for a real sizing problem, this book's worked example, a
storage cluster: the single number first, and then the answers:

```{include} chapters/_generated/preface-storage-outputs.md
```

Read the first row. Its point estimate is a real number, correctly computed — and beside it the
**90% interval**, the range nine of those answers in ten fell into, spans most of an order of
magnitude. Nothing in the first calculation was wrong. It simply had no way to mention that it was
a bet.

Why nine in ten, rather than the smallest and largest answers? Because the smallest and largest
are not properties of the problem. They are properties of how many answers you collected: collect
ten times as many and the largest gets larger, every time, because you gave the unlucky
combinations more chances to turn up. The ends drift. The middle settles, and settles quickly
enough to be worth quoting. Ninety per cent is then a convention, and this book uses the same one
everywhere so that two figures can be compared.

```{image} chapters/_figures/preface-tco-distribution.svg
:alt: The five-year total cost as a distribution, with the point estimate marked on it
:width: 100%
```

Each bar counts how many of those answers landed on a given five-year total — the table's second
row, drawn — and the red line is where the single-number answer falls.

The method that produced the interval is [ch12](#monte-carlo)'s, not this page's. It is no use to
you until you have built a model, got a number out of it, and felt that you could not defend the
number.

## What a model is in this book

The quantities that went into that number, and the arithmetic joining them, written down in a
file. Each quantity gets a name, a unit, and a note saying where its value came from. Each
computed quantity gets a formula referring to the others by name. Nothing more exotic than that:
the file is the model, and you can read the whole of one in a sitting.

You build this one. It starts in [ch01 · What a workload is](#what-a-workload-is) as what
arrives and what accumulates — a file that runs, and that cannot yet tell you anything you did
not type into it. Later chapters add to it as they earn the right to: where each number came from,
what the hardware can hold, where it stops coping, what it costs to run.
[ch11 · The sizing model](#the-sizing-model) is where it produces the node count in the table
above, and [ch17 · The five-year model](#the-five-year-model) is where it produces the cost.
The storage figures in this book are computed from that file at whatever stage the chapter has
reached, so an early table cannot show you something that chapter has not built yet.

## The error an interval cannot show

Almost all of that width came from one input. The growth rate is a forecast, it compounds over
five years, and it moves the answer further than everything else in the model put together.
Finding that out rather than guessing it is [ch18](#which-input-is-the-answer)'s subject, and
it is the most useful thing you can do with a model you already have.

Letting inputs vary and watching what happens is honest work, and most of this book is about
doing it well. But it can only ever report the doubt somebody wrote down. There is a second kind
of error it cannot see at all, and which of two kinds of model you have decides whether you are
exposed to it.

**A cost model has a deterministic structure with uncertain parameters.** Its relationships are
accounting identities and physics: watts times hours times price, capital plus running cost over
a horizon, a total divided by a denominator. Nothing in that structure is in doubt. Only the
inputs are uncertain, cost scales roughly in proportion to them, and sampling the inputs is
genuinely sufficient. A cost model can be wrong because a price was wrong. It is rarely wrong
because the system it describes started behaving differently.

**A sizing model has the same structure and adds two things.**

*Measured constants.* How many bytes a stored measurement takes once it is compressed. How many
records one request leaves behind when a system is traced. How much work a single processing core
gets through in a second. These are empirical, they belong to a particular implementation at a
particular version, they have measurement error, and none of them is a fact about the world. A
chain of multiplications built on them inherits every one of those properties, and a model that
treats them as constants hides them all.

*Non-linear ceilings.* The queueing knee, where response time climbs steeply while a device still
has capacity to spare. Rebuild under failure, where losing one machine costs capacity you were
using. A new field attached to a measurement, which multiplies how many separate things you have
to store by however many values that field turns out to take. A working set outgrowing memory.
These are regime changes, and **a chain of multiplications cannot model a regime change**. It will
happily report that a system is running at several times its own limit, which is not a description
of anything that can happen.

So a sizing model has to say how much room it keeps below each limit, and why, rather than only
producing a number. This repository enforces that rather than asking for it: a model with a
measured constant or a declared limit in it **is** a sizing model, one with neither **is** a cost
model, and the build holds the two to different rules. A sizing model that names a limit and keeps
no room below it does not build.

## Why you should believe any of it

You have just been shown a table and asked to take its numbers seriously. The rule underneath this
book is that nothing is asserted here that the repository could check instead. That rule shows up
in three ways.

**Every number says where it came from.** No figure is typed into the prose; every one is
computed. The italic line under each table links to the file it came from —
`storage_cluster-reference` names which model was run and under which assumptions, and the file
holds every input it used — so you can check a number instead of trusting it.

**Every model is a file, not a spreadsheet.** Every quantity in it declares a unit, so the build
can refuse a model that multiplies the wrong two things. Every input declares whether it is a
fact, a vendor's claim or somebody's assumption, and an uncertain one has to say what shape its
uncertainty has and why that shape rather than another. Every measured constant names the
measurement behind it. [ch02](#where-the-numbers-come-from) says what those distinctions are
worth; [Appendix A](#appendix-a-dsl-reference) is the file format that holds them.

**Every chapter ends by saying what it cannot tell you.** A section with that name is required,
and the tests fail a chapter that leaves it out. In a book about estimates it is usually the most
useful part of the chapter.

One consequence of those rules shows up on the pages. When a constant has not been measured, the
quantity that needs it has no value, and neither does anything computed from it. Those figures
render as *not yet measured* and the affected chain is named — never a placeholder, and never a
number borrowed from a different stack. [Appendix F](#appendix-f-observability-model) publishes
one of those figures, which is a deliberate choice and is argued there.

## Who this book is for

A self-study text and a toolkit, for an engineer who has been asked how big something needs to
be, or what it will cost, and who wants to give an answer they would still defend a year later.

You should be comfortable with code and with arithmetic. You are assumed to know **nothing**
about statistics. [ch12](#monte-carlo) and [ch13](#correlation-and-convergence) are where the six
words you need — distribution, sample, percentile, interval, correlation, convergence — get
defined properly, each arriving because a model has just raised a question that needs it. One of
them, *interval*, has already appeared on this page, defined at the point it was needed. That is
how the rest arrive too. Where a statistical term has a plain-English equivalent, this book uses
the plain one first and names the term second.

No vendor is named anywhere in this book, and no product is recommended. Three models carry it,
all written so that the structure is the point and the numbers are yours to replace: a scale-out
storage cluster, which is sized and costed end to end; an observability platform, which is the one
with a hole in it where a measurement should be; and a request-serving tier, whose behaviour under
load is not a chain of multiplications at all, which is why the chapters on ceilings are built on
it.

## What you will need

Python, Node for the book build, and about twenty minutes:

```bash
git clone https://github.com/snowch/sizing-and-tco.git
cd sizing-and-tco

python3 -m pip install -r requirements.txt -r requirements-dev.txt
npm install -g "mystmd@$(node -p "require('./package.json').devDependencies.mystmd")"

make models     # evaluate every model and stamp what it said
make check      # exactly what CI runs
make book       # live preview at localhost:3000
```

Nothing in this book needs a datacentre, a cloud account, or a licence.

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
