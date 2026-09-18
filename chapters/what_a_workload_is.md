---
title: "What a workload is"
short_title: "ch01 What a workload is"
---

(what-a-workload-is)=
# ch01 · What a workload is

## The question

Which quantities actually size a system, and which ones only look as though they do?

Somebody has told you what the system has to do. Before any of it can be multiplied into a number
of machines, it has to be written down in a form that cannot quietly mean two things — and the
first distinction that matters is between a rate and a level. That sounds like pedantry right up
until somebody sizes a retention store from a rate.

This chapter writes the first nodes of the model the rest of the book uses. By the end of it you
will have a file that runs.

## The material

### Three kinds of quantity, and two of them get confused

**A flow is a rate.** Requests per second, bytes per second, dollars per year. It has time
underneath it. You cannot store one, you cannot run out of one, and adding two of them is
meaningful only if they cover the same period.

**A stock is a level.** Terabytes held, series alive, requests in flight. It is how much there is
right now. You *can* run out of one, and that is usually what a ceiling is about.

**Everything else is a ratio, a count or a price** — a replication factor, a compression ratio, a
cost per terabyte. These have no time in them at all and they are the constants of a sizing chain.

The unit tells you which is which. That is why the build can check it, and why every node in this
book declares one. A flow has time in its denominator; a stock does not; a duration has time in
its numerator and is none of the three.

The commonest error in sizing is turning a flow into a stock by multiplying it by a number instead
of by an amount of time. It typechecks in a spreadsheet. It does not typecheck here, and problem
1.2 is exactly that.

### Turning the workload into a file

The workload you have been given is the one this book carries all the way through: some amount
of data held today, growing at some rate, over the life of whatever gets bought. You could put
that in a spreadsheet, and most people do. A cell holds a value. It
does not hold the fact that the value was measured last March against version 2.4 of something,
or that it is a vendor's claim nobody has checked, or that it was agreed in a meeting by people
who have since left. Those facts live in the head of whoever built the sheet, and they leave when
that person does. Nor does a cell have a unit: `=B4*C7` is as valid as any other product, and
multiplying series by requests gives a number that looks exactly like a number of bytes.

So a model here is a text file of named quantities, each with a unit and a source, that diffs and
reviews like code. One file. What follows is three pieces of the same one, in the order you would
write them, and the whole thing is eighty lines by the end of this chapter.

The first node is the level you were given.

```{literalinclude} ../models/storage_cluster/stages/01-demand/model.yaml
:language: yaml
:start-at: usable_capacity_t0:
:end-before: annual_growth:
```

Four of those lines are the argument of this book and the rest are convenience. `kind` and `unit`
are what let the build tell a level from a rate. `value` is the number a spreadsheet would have
held on its own. `provenance` is the line a cell has nowhere to put: a number with no source is a
rumour, and the field is mandatory from the very first node —
[ch02](#where-the-numbers-come-from) is about what that costs and what it buys.

`label` and `range` are neither. A label reads better in a table than
`usable_capacity_t0` does, and a range is how far a slider may drag the value on the interactive
version of this model. Both are optional, and [Appendix A](#appendix-a-dsl-reference) lists
everything a node may carry — which is longer than what a node needs.

Growing it over the horizon takes one multiplication and one thing that is easy to miss:

```{literalinclude} ../models/storage_cluster/stages/01-demand/model.yaml
:language: yaml
:start-at: one_year:
:end-before: peak_read_throughput:
```

`horizon / one_year` looks like ceremony and is not. Growth compounds, so the horizon has to be an
exponent, and an exponent has to be a pure number. Five years is a duration; five is a number.
Dividing a duration by a declared year is how the first becomes the second. A
spreadsheet does this silently and correctly, right until the quarter somebody types a horizon in
months into the same cell.

Then the level at the end, which is the first quantity in this book that is *computed* rather than
stated:

```{literalinclude} ../models/storage_cluster/stages/01-demand/model.yaml
:language: yaml
:start-at: usable_capacity:
:end-before: outputs:
```

That is the whole of the demand side. Here it is, and the toolkit that reads it — this
repository's, not a copy of it. Press **Run**, then change a number and watch the total move.
Change `usable_capacity`'s formula to multiply the read throughput by a count of periods, and it
refuses, for the reason at the top of this chapter.

```{iframe} /playground/what-a-workload-is/
:width: 100%
The file above, running. The first press fetches a Python runtime; after that a check takes milliseconds.
```


### The demand and the decisions

A model's inputs are two different kinds of thing wearing the same clothes. Some describe what the
world is doing to you. The rest describe what you have decided to do about it. Separating them is
the first thing worth doing to any model, including this one:

```{include} _generated/what-a-workload-is-storage.md
```

Every quantity is filed under *what you decide*, and one of them is the growth rate. Nobody
decides a growth rate.

The table is not wrong about the model. The model is wrong, and the table is showing you the only
signal it has: whether somebody gave the quantity a shape instead of a single number. A shape says
*the world settles this one, and here is how much it varies*; one number says *I chose this*.
Nothing in the file has a shape yet, so everything reads as a choice.
[ch03](#peak-mean-and-growth) gives the growth rate one, and this table splits in two for the
first time.

That is worth more here than a correct table would have been, because the failure is the useful
one. **An input you gave a single value to and cannot actually control is an assumption you have
stopped noticing**, and a model that files its inputs this way finds them by construction. Day-one
capacity is sitting in the same list, and that one is not a decision either.

Once the table does separate, the half worth arguing about is *what you decide*, because it is the
half anybody can change. Most sizing conversations are spent on the other one.

The *Claim* column is asking something else: how much the person who wrote
each number down was claiming. **●** traceable to a measurement or a
definition, **◐** supplied by whoever is selling it, **○** somebody's
assumption. [ch02](#where-the-numbers-come-from) is about what that difference is worth.

### What it says, and what the build calls it

Nothing so far has run. The file is a description; what reads it is
[`sizing`](#appendix-a-dsl-reference), and one command points it at every model in the
repository:

```bash
make models
```

That parses each file, refuses any formula whose units do not work out, evaluates the graph in
dependency order, and writes what it found to `bench/results/` — which is where every figure in
this book comes from, including the next one. For the seven nodes above:

```{include} _generated/what-a-workload-is-stage.md
```

A number, out of a handful of numbers and a multiplication. The arithmetic is right and you should
not act on it, for a reason this chapter cannot yet name: every figure that went in was a single
figure, and not one of them is known that precisely. [ch03](#peak-mean-and-growth) takes the first
of them apart.

The build has already decided what kind of model this is, too:

```{include} _generated/what-a-workload-is-stage-shape.md
```

The last row is not a label anybody typed. `sizing/dsl.py` works it out from what is in the file:
nothing here has a measured constant or a declared limit in it, so what you have is a **cost
model** — a structure nobody doubts, with uncertain numbers in it. It changes kind in
[ch08](#capacity), and it changes because two nodes get added rather than because a chapter says
so.

### The same split, on a model that is finished

Here is the table doing what it is for. This is a different system — an observability platform,
carrying metrics, logs and traces — and every input in its model has been given either a shape or
a value, so both lists are populated:

```{include} _generated/what-a-workload-is-observability.md
```

Read the decisions. Scrape interval, retention, sampling rate, how many log lines you keep —
those are the four knobs an observability platform gives you, and
[Appendix F](#appendix-f-observability-model) shows what turning all of them down actually buys.

Then read the demand, and notice what is *not* in the decisions: the number of label values. It
dominates the whole model and it is not a knob. That is [ch07](#regime-changes)'s subject.

### A workload can be described badly in three ways

**Averaged.** A daily mean is the one number nobody experiences. [ch03](#peak-mean-and-growth) is
about which number in a demand curve sizes you, and it is not that one.

**In the wrong units.** "Ten thousand users" is not a workload. It is a fact about a licence
agreement. What sizes a system is what those users cause: requests, bytes, series, queries. The
translation between the two is a measured constant and usually the shakiest number in the model.

**As a single point in time.** A workload that does not state a growth rate is a workload stated
for today, and nobody buys infrastructure for today.

### The smallest useful workload

Here is the whole demand side of a request-serving tier:

```{include} _generated/what-a-workload-is-service.md
```

Two of those rows are the workload proper: how fast requests arrive, and how much work each one
costs. [ch04](#littles-law) through [ch06](#when-adding-servers-stops-helping) are built on that
pair and a count of machines. The other three describe how the tier behaves under load rather than
what is asked of it, and each one is a chapter of Part II — which is the distinction this table
cannot draw and the next part exists to make.

## What this cannot tell you

**Whether the quantities are the right ones.** A workload description is a model of demand, and
like every model it omits things. The storage model has no notion of object size distribution, the
observability model has no notion of query shape, and the service tier has no notion of requests
that differ from each other. Each omission is defensible and each one is a place the answer could
be wrong in a way nothing here would show.

**Where the numbers come from.** Every figure in the tables above is an input somebody wrote down.
Some are measured, most are not, and this chapter has said nothing about the difference.
[ch02](#where-the-numbers-come-from) is about that difference, and how much any of this is worth
depends on it.

**Whether a peak is a peak.** "The busy hour" is a phrase, not a measurement. Whether your busy
hour is an hour, a minute or a Tuesday in November is a property of your traffic, and sizing for
the wrong one is expensive in both directions.

**How the demand quantities move together.** Every table above lists them separately, as though
request rate and log volume were unrelated. They are not, and treating them as though they were
makes every interval in the book too narrow ([ch13](#correlation-and-convergence)).

## Problems

Four, in `tests/what_a_workload_is/`.

**1.1 — Levels and rates.**
Classify every node in the observability model as a stock, a flow or neither — by reading what it
means. The test classifies the same nodes by their declared units. Where your reading and the
model's units disagree, one of them is wrong, and finding out which is the exercise.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_1_stocks_and_flows.py
```

**1.2 — Turn a rate into a volume.**
Add a node giving terabytes a day of telemetry. A rate times a pure number is still a rate, and
the build will keep saying so until something in the formula carries a duration.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_2_daily_volume.py
```

**1.3 — The smallest model that builds.**
Write a model file of your own with one input and one derived node that passes the loader, the
dimensional pass and every rule in `scripts/verify-models.py`. Read the rules before you start;
the refusals are the point.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_3_smallest.py
```

**1.4 — Break it on purpose, in a way that still loads.**
Write a second model that loads cleanly and is wrong about units. Not a typo — those fail
immediately and teach nothing. A node that declares a unit its own formula cannot produce. A
spreadsheet cannot see that class of error at all.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_4_broken.py
```

## Where to go next

[ch02](#where-the-numbers-come-from) is the question this chapter kept deferring: given that you
have written a quantity down, what are you actually claiming about it?

[ch03](#peak-mean-and-growth) is the other one: given that demand moves, which value of it sizes
you?
