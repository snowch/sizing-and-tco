---
title: "Introduction"
short_title: Introduction
---

(preface)=
# Introduction

*How to size a system, cost it, and know how much to trust the answer.*

## What this book is about

Somebody asks how big the system needs to be. How many machines, how much storage, how much it
will cost to run for the next three years — and they are going to spend real money on whatever you
tell them.

**How big, how much, and how wrong could I be?**

Three questions, and the first two are arithmetic. **Sizing** is how much hardware a stated
workload needs, and where it stops coping. **Total cost of ownership** is what that hardware costs
over the years you keep it, which is not the same as what it costs to buy. The arithmetic for both
is within anybody's reach.

This book teaches the third: how to find which input your answer rests on, how far the answer
moves when that input moves, and what it would cost to find out. Almost nobody is taught this, and
it is what decides whether anybody should act on your number. [ch01](#what-one-number-hides) is
where that starts, and it starts by showing you what a single number leaves out.

## How it goes about it

**You build one model, and it lasts the whole book.** A model here is the quantities that went
into a number and the arithmetic joining them, written down in a file. Each quantity gets a name,
a unit, and a note saying where its value came from. Each computed quantity gets a formula
referring to the others by name. Nothing more exotic than that: the file is the model, and you can
read the whole of one in a sitting.

It starts in [ch02 · What a workload is](#what-a-workload-is) as what arrives and what
accumulates, and already refuses a formula whose units do not work out — the error a spreadsheet
accepts without comment, and the one that sizes a retention store from a rate.
Later chapters add to it as they earn the right to: where each number came from, what the hardware
can hold, where it stops coping, what it costs to run.
[ch12 · The sizing model](#the-sizing-model) is where it produces a node count, and
[ch18 · The five-year model](#the-five-year-model) is where it produces a cost. Every storage
figure in this book is computed from that file at whatever stage the chapter has reached, so an
early table cannot show you something that chapter has not built yet.

**Nothing is asserted here that the repository could check instead.** That rule shows up in three
ways, and it is the reason to believe any of the numbers you are about to be shown.

*Every number says where it came from.* No figure is typed into the prose; every one is computed.
The italic line under each table links to the file it came from — `storage_cluster-reference`
names which model was run and under which assumptions, and the file holds every input it used —
so you can check a number instead of trusting it.

*Every model is a file, not a spreadsheet.* Every quantity in it declares a unit, so the build can
refuse a model that multiplies the wrong two things. Every input declares whether it is a fact, a
vendor's claim or somebody's assumption, and an uncertain one has to say what shape its
uncertainty has and why that shape rather than another. Every measured constant names the
measurement behind it. [ch03](#where-the-numbers-come-from) says what those distinctions are
worth; [Appendix A](#appendix-a-dsl-reference) is the file format that holds them.

*Every chapter ends by saying what it cannot tell you.* A section with that name is required, and
the tests fail a chapter that leaves it out. In a book about estimates it is usually the most
useful part of the chapter.

One consequence of those rules shows up on the pages. When a constant has not been measured, the
quantity that needs it has no value, and neither does anything computed from it. Those figures
render as *not yet measured* and the affected chain is named — never a placeholder, and never a
number borrowed from a different stack. [Appendix F](#appendix-f-observability-model) publishes
one of those gaps, which is a deliberate choice and is argued there.

## Who it is for, and what you need to know

A self-study text and a toolkit, for an engineer who has been asked how big something needs to be,
or what it will cost, and who wants to give an answer they would still defend a year later.

You should be comfortable with code and with arithmetic. You are assumed to know **nothing** about
statistics. [ch13](#monte-carlo) and [ch14](#correlation-and-convergence) are where the six words
you need — distribution, sample, percentile, interval, correlation, convergence — get defined
properly, each arriving because a model has just raised a question that needs it. Where a
statistical term has a plain-English equivalent, this book uses the plain one first and names the
term second.

No vendor is named anywhere in this book, and no product is recommended. Three models carry it,
all written so that the structure is the point and the numbers are yours to replace: a scale-out
storage cluster, which is sized and costed end to end; an observability platform, which is the one
with a hole in it where a measurement should be; and a request-serving tier, whose behaviour under
load is not a chain of multiplications at all, which is why the chapters on ceilings are built on
it.

Every chapter ends with problems, and most of them are tests you run: they fail until you have
solved them, and the answer is nowhere in the repository. Some have no test at all, because they
are about a system you actually run and there is no oracle for judgement — those say instead what
a good answer contains and what would falsify it. Every chapter ends with one of those.

## What you will need

To read it and run its models, nothing. [ch02](#what-a-workload-is) and
[ch03](#where-the-numbers-come-from) carry the model file running in the page: press **Run**,
change a number, and try to multiply a rate by a count of periods to see the build refuse it.
That is this repository's own loader and unit checker, fetched as a Python runtime and run in
your browser, so what the page does and what `make check` does cannot come apart. The finished
models in [Appendix E](#appendix-e-storage-model) and
[Appendix F](#appendix-f-observability-model) have a slider against every input; those are
evaluated by a small JavaScript version, which `tests/test_viewer.py` runs against Python's
answers for every node of every model before it ships.

The book is a website and is meant to be read as one: the models are the point, and they are
things you drag. The prose reads on any screen; the models want a tablet held sideways or
anything larger, and say so when they have less. Once you have opened it, the whole book works
with no network — your browser keeps it — and if you press **Resample** or **Run** once while
online, the Python runtime those fetch is kept too.

To do the problems, a checkout. They are tests, and a test needs an interpreter. Python, Node for
the book build, and about twenty minutes:

```bash
git clone https://github.com/snowch/sizing-and-tco.git
cd sizing-and-tco

python3 -m pip install -r requirements.txt -r requirements-dev.txt
npm install -g "mystmd@$(node -p "require('./package.json').devDependencies.mystmd")"

make models     # evaluate every model and stamp what it said
make check      # exactly what CI runs
make book       # build the site and serve it
```

Nothing in this book needs a datacentre, a cloud account, or a licence.

:::{note} Where this book is
This site is the whole of it — there is no PDF, because the models are things you drag and paper
cannot hold one. The line below says which commit built the pages you are reading.

```{include} chapters/_generated/build.md
```
:::
