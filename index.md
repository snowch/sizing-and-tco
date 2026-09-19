---
title: "Introduction"
short_title: Introduction
---

(preface)=
# Introduction

*How to size a system, cost it, and know how much to trust the answer.*

## What this book is about

Somebody asks how big the system needs to be. How many machines, how much storage, and how much
it will cost to run for the next three years. They are going to spend real money on whatever you
tell them.

**How big, how much, and how wrong could I be?**

The first two questions are arithmetic.

**Sizing** means working out how much hardware a stated workload needs, and where that hardware
stops coping.

**Total cost of ownership** (TCO) means what that hardware costs over the years you keep it. That
is not the same as what it costs to buy.

Anybody can do the arithmetic for both.

## The question this book answers

The third question is the hard one, and it is the one this book teaches. To answer it you need
to know:

- which input your answer rests on;
- how far the answer moves when that input moves; and
- what it would cost to find out.

Almost nobody is taught this. It is what decides whether anybody should act on your number.

[ch01](#point-estimates) starts there. It shows you what a single number leaves out.

## How the model works

You build one model, and it lasts the whole book.

A model here is a YAML file: plain text you can read and edit. It holds the numbers that went
into an answer and the arithmetic that joins them. Each number has a name, a unit, and a note saying where its value came from. Each
computed number has a formula that refers to the others by name. That is all there is to it. You
can read a whole model in one sitting.

The model starts in [ch02 · What a workload is](#what-a-workload-is), with what arrives and what
accumulates. Later chapters add to it one piece at a time: where each number came from, what the
hardware can hold, where it stops coping, and what it costs to run.
[ch12 · The sizing model](#the-sizing-model) is where it produces a host count.
[ch18 · The five-year model](#the-five-year-model) is where it produces a cost.

Every figure about the service in this book is computed from that file as it stands at that
point in the book.

## Why a file, and not a spreadsheet

A spreadsheet cell holds a value and nothing about it.

- It does not tell you the unit. Multiply the wrong two cells and the result looks like any other
  number.
- It does not tell you where the number came from. A vendor's claim and a measurement sit in the
  same column, looking the same.
- It does not tell you how certain the number is. The spread is gone after the first
  multiplication.

Everything this book does depends on those three things being written down beside the number. A
file is where they can be. A file also diffs and reviews like code.

The toolkit checks the units of every formula. A rate times a duration is an amount, so
`requests per second × seconds = requests`. A formula that multiplies a rate by a count of periods
instead is refused. A spreadsheet accepts that calculation without complaining. The toolkit
refuses it. Here is the check, drawn: in the top row the seconds cancel; in the bottom row nothing
does.

```{image} chapters/_figures/what-a-workload-is-units.svg
:alt: A rate times a duration is an amount; a rate times a plain number is still a rate
:width: 100%
```

[ch02](#what-a-workload-is) writes the first node, at four lines a number. The **build**, the set
of checks that turns these files into this book, refuses a node that leaves out its unit or its
source.

## Every number can be checked

Every number in this book can be checked, and the page tells you how. That promise is kept in
three ways.

**Every number says where it came from.** No figure is typed into the prose. Every one is
computed. The italic line under each table links to the file it came from. For example,
`web_service-reference` names which model was run and under which assumptions, and that file
holds every input it used. You can check a number instead of trusting it.

**Every model is a file, not a spreadsheet.** Every number in it declares a unit, so the build can
refuse a model that multiplies the wrong two things. Every input says whether it is a fact, a
vendor's claim, or somebody's assumption. An uncertain input has to say what shape its
uncertainty has, and why that shape rather than another. Every measured constant names the
measurement behind it. [ch03](#where-the-numbers-come-from) explains what those distinctions are
worth. [Appendix A](#appendix-a-dsl-reference) describes the file format that holds them.

**Every chapter ends by saying what it cannot tell you.** Every chapter has a section with that
name. In a book about estimates, it is usually the most useful part of the chapter.

## Unknown numbers stay unknown

If a required number has not been measured, the model does not invent one.

When a constant has not been measured, the number that needs it has no value. Neither does
anything computed from it. Those figures show as *not yet measured*, and the page names the chain
of numbers that is affected. There is never a placeholder, and never a number taken from a
different system.

[Appendix F](#appendix-f-observability-model) publishes one of those gaps on purpose, and
explains why.

## Who this book is for

This is a self-study text and a toolkit. It is for an engineer who has been asked how big
something needs to be, or what it will cost, and who wants to give an answer they would still
defend a year later.

You should be comfortable with code and with arithmetic. You are assumed to know **nothing**
about statistics. The book needs six statistical words:

- distribution;
- sample;
- percentile;
- interval;
- correlation; and
- convergence.

[ch13](#monte-carlo) and [ch14](#correlation-and-convergence) define them properly. Each one
arrives only when a model has just raised a question that needs it. Where a statistical term has
a plain-English equivalent, the book uses the plain one first and names the term second.

No vendor is named anywhere in this book, and no product is recommended. Two models carry the
book. Both are written so that the structure is the point and the numbers are yours to replace:

- a web service and its data, on a fleet of Linux hosts. It is sized and costed end to end, and
  how it behaves under load is not a chain of multiplications at all; and
- an observability platform, which has a hole in it where a measurement should be.

Every chapter ends with problems. Most of them are tests you run: they fail until you have solved
them, and the answer is nowhere in the repository. Some have no test, because they are about a
system you actually run and nothing can mark your judgement. Those say what a good answer
contains and what would prove it wrong. Every chapter ends with one of those.

## What you need

To read the book and run its models: nothing.

[ch02](#what-a-workload-is) and [ch03](#where-the-numbers-come-from) carry the model file running
in the page. Press **Run**, change a number, and try to multiply a rate by a count of periods.
The build refuses it. That is the book's own loader and unit checker, fetched as a Python runtime
and run in your browser. What the page does and what the book was computed from cannot come
apart.

The finished models in [Appendix E](#appendix-e-web-service-model) and
[Appendix F](#appendix-f-observability-model) have a slider on every input. A small JavaScript
version evaluates those. It is checked against Python's answers for every node of every model
before it ships.

The book is a website, and it is meant to be read as one. The models are the point, and they are
things you drag. The prose reads on any screen. The models want a tablet held sideways, or
anything larger, and say so when they have less. There is no PDF, because paper cannot hold a
model you drag.

Once you have opened the book, it works with no network. Your browser keeps it. If you press
**Resample** or **Run** once while online, the Python runtime those fetch is kept too.

To do the problems, you need a checkout. The problems are tests, and a test needs an interpreter.
You need Python and a few minutes:

```bash
git clone https://github.com/snowch/sizing-and-tco.git
cd sizing-and-tco
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -m pytest tests/point_estimates/    # ch01's problems, which fail until they are solved
```

[Appendix H](#appendix-h-running-the-toolkit) has the rest: re-taking a measurement, re-running a
model, rebuilding the book, and checking any figure against the repository.

Nothing in this book needs a datacentre, a cloud account, or a licence.

## Where to start

[ch01](#point-estimates) shows what a single number leaves out. Read it first. Everything after
it is an answer to that.
