---
title: "What a workload is"
short_title: "ch02 What a workload is"
---

(what-a-workload-is)=
# ch02 · What a workload is

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | none |
| **What it produces** | The demand side of the storage model, and the workload table for all three |
| **Built from** | `storage_cluster_demand-reference`, `storage_cluster-reference`, `observability-reference`, `service_tier-reference` |
:::

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
2.2 is exactly that.

### Writing the first one down

Take the workload above: some amount held today, growing at some rate, over the life of whatever
gets bought. The first node is the level you were given.

```{literalinclude} ../models/storage_cluster/stages/01-demand/model.yaml
:language: yaml
:start-at: usable_capacity_t0:
:end-before: annual_growth:
```

A `unit`, so the build knows this is a level and not a rate. A `value`, because somebody said so.
A `provenance`, because a number with no source is a rumour — that is
[ch03](#where-the-numbers-come-from)'s subject, and the reason the field is mandatory from the
very first node. The `range` is what a reader may drag it to on the published page.

Growing it over the horizon takes one multiplication and one thing that is easy to miss:

```{literalinclude} ../models/storage_cluster/stages/01-demand/model.yaml
:language: yaml
:start-at: one_year:
:end-before: peak_read_throughput:
```

`horizon / one_year` looks like ceremony and is not. Growth compounds, so the horizon has to be an
exponent, and an exponent is a pure number: five years cannot be one, but five can. Dividing a
duration by a declared year is how it becomes the count of periods the formula can use. A
spreadsheet does this silently and correctly, right until the quarter somebody types a horizon in
months into the same cell.

Then the level at the end, which is the first quantity in this book that is *computed* rather than
stated:

```{literalinclude} ../models/storage_cluster/stages/01-demand/model.yaml
:language: yaml
:start-at: usable_capacity:
:end-before: outputs:
```

That is the whole of the demand side:

```{include} _generated/what-a-workload-is-stage-shape.md
```

The last row is not a label somebody typed. `sizing/dsl.py` works it out from what is in the file,
and nothing here has a measured constant or a declared limit in it yet, so what the book has so far
is a **cost model** — structure nobody doubts, with uncertain numbers in it. It will change kind in
[ch09](#capacity), and it will change because the file changed rather than because a chapter said
so.

### What it says, and what that is worth

```{include} _generated/what-a-workload-is-stage.md
```

A number, out of a handful of numbers and a multiplication. The arithmetic is right and you should
not act on it, for a reason this chapter cannot yet name: every figure that went in was a single
figure, and not one of them is known that precisely. [ch04](#peak-mean-and-growth) takes the first
of them apart.

### The demand and the decisions

A model's inputs are two different kinds of thing wearing the same clothes. Some describe what the
world is doing to you. The rest describe what you have decided to do about it. Separating them is
the first thing worth doing to any model you inherit:

```{include} _generated/what-a-workload-is-storage.md
```

The *Claim* column is how much the person who wrote each number down was claiming, and the three
marks run through every figure in the book: **●** something traceable to a measurement or a
definition, **◐** a figure supplied by whoever is selling it, **○** somebody's assumption.
[ch03](#where-the-numbers-come-from) is about what the difference is worth.

Everything above the second heading is something you can argue about and cannot choose. Everything
below is a choice somebody made and could unmake. A sizing conversation should be about the second
list. Most are about the first.

The heuristic that produced that split is crude and worth knowing: a quantity somebody gave a
distribution to is one they think the world decides, and a quantity with a single value and a
slider is one they think they decide. Splitting a model this way is far better than not splitting
it, and where the heuristic is wrong the wrongness is interesting. An input you gave a single
value to and cannot actually control is an assumption you have stopped noticing.

### The same split, on a system with three of everything

```{include} _generated/what-a-workload-is-observability.md
```

Read the decisions. Scrape interval, retention, sampling rate, how many log lines you keep —
those are the four knobs an observability platform gives you, and
[Appendix F](#appendix-f-observability-model) shows what turning all of them down actually buys.

Then read the demand, and notice what is *not* in the decisions: the number of label values. It
dominates the whole model and it is not a knob. That is [ch08](#regime-changes)'s subject.

### A workload can be described badly in three ways

**Averaged.** A daily mean is the one number nobody experiences. [ch04](#peak-mean-and-growth) is
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

Two quantities describe what the world does — how fast requests arrive, and how much work each
one costs. Everything else in [ch05](#littles-law) through [ch07](#when-adding-servers-stops-helping)
is derived from those two and a count of machines. A workload description that cannot be reduced
this far usually contains something that is not a workload.

## What this cannot tell you

**Whether the quantities are the right ones.** A workload description is a model of demand, and
like every model it omits things. The storage model has no notion of object size distribution, the
observability model has no notion of query shape, and the service tier has no notion of requests
that differ from each other. Each omission is defensible and each one is a place the answer could
be wrong in a way nothing here would show.

**Where the numbers come from.** Every figure in the tables above is an input somebody wrote down.
Some are measured, most are not, and this chapter has said nothing about the difference.
[ch03](#where-the-numbers-come-from) is about that difference, and how much any of this is worth
depends on it.

**Whether a peak is a peak.** "The busy hour" is a phrase, not a measurement. Whether your busy
hour is an hour, a minute or a Tuesday in November is a property of your traffic, and sizing for
the wrong one is expensive in both directions.

**How the demand quantities move together.** Every table above lists them separately, as though
request rate and log volume were unrelated. They are not, and treating them as though they were
makes every interval in the book too narrow ([ch14](#correlation-and-convergence)).

## Problems

Two, in `tests/what_a_workload_is/`.

**2.1 — Levels and rates.**
Classify every node in the observability model as a stock, a flow or neither — by reading what it
means. The test classifies the same nodes by their declared units. Where your reading and the
model's units disagree, one of them is wrong, and finding out which is the exercise.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_1_stocks_and_flows.py
```

**2.2 — Turn a rate into a volume.**
Add a node giving terabytes a day of telemetry. A rate times a pure number is still a rate, and
the build will keep saying so until something in the formula carries a duration.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_2_daily_volume.py
```

## Where to go next

[ch03](#where-the-numbers-come-from) is the question this chapter kept deferring: given that you
have written a quantity down, what are you actually claiming about it?

[ch04](#peak-mean-and-growth) is the other one: given that demand moves, which value of it sizes
you?
