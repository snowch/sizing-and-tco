---
title: "What a workload is"
short_title: "ch02 What a workload is"
---

(what-a-workload-is)=
# ch02 · What a workload is

## The question

Which quantities actually size a system, and which only look as though they do?

Somebody has told you what the system has to do. Before any of it can be multiplied into a number
of machines, it has to be written down in a form that cannot quietly mean two things. The first
distinction that matters is between a rate and a level. That sounds like pedantry, right up until
somebody sizes a retention store from a rate.

This chapter writes the first nodes of the model the rest of the book uses. By the end of it you
will have a file that runs.

## The material

### Three kinds of quantity, and two of them get confused

**A flow is a rate.** Requests per second, bytes per second, dollars per year. It has time
underneath it. You cannot store one and you cannot run out of one. Adding two of them means
something only if they cover the same period.

**A stock is a level.** Terabytes held, series alive, requests in flight. It is how much there is
right now. You *can* run out of one, and that is usually what a ceiling is about.

**Everything else is a ratio, a count or a price.** A replication factor, a compression ratio, a
cost per terabyte. These have no time in them at all. They are the constants of a sizing chain.

The unit tells you which is which. That is why the toolkit can check it, and why every node in
this book declares one. A flow has time in its denominator. A stock does not. A duration has time
in its numerator, and is none of the three.

The commonest error in sizing is turning a flow into a stock by multiplying it by a number instead
of by an amount of time. A spreadsheet accepts it. The toolkit does not, and problem 2.2 is
exactly that.

Here is the check, drawn. In the top row the seconds cancel, and a rate becomes an amount. In the
bottom row nothing cancels, so the answer is still a rate, and that is the formula the toolkit
refuses.

```{image} _figures/what-a-workload-is-units.svg
:alt: A rate times a duration is an amount; a rate times a plain number is still a rate
:width: 100%
```

### The whole of it, before any of it is written down

Here is the demand side of the model this book builds, as a graph. Eight quantities: four you
were given, one a definition, three computed. Drag *annual growth factor* and watch *peak request
rate at horizon* and *records held at horizon* move together. That is a flow, a stock and one
exponent, and it is the whole of this chapter.

```{iframe} /models/web_service_demand-reference.html
:width: 100%
The demand side, with a slider on every input. Click a node to see what fed it.
```

### Turning the workload into a file

That graph was drawn from a file, and the file is what you will actually write.

The workload you have been given is the one this book carries all the way through: a busy hour of
requests today and some amount of data held today, both growing at some rate, over the life of
whatever gets bought.

You could put that in a spreadsheet, and most people do. A cell holds a value and nothing else. It
does not hold the fact that the value was measured last March against version 2.4 of something.
It does not say that the value is a vendor's claim nobody has checked, or that it was agreed in a
meeting by people who have since left. Those facts live in the head of whoever built the sheet,
and they leave when that person does. Nor does a cell have a unit. `=B4*C7` is as valid as any
other product, and multiplying series by requests gives a number that looks exactly like a number
of bytes.

So a model here is a YAML file of named quantities, each with a unit and a source. It diffs and
reviews like code. One file. What follows is three pieces of the same one, in the order you would
write them. The whole thing is eighty lines by the end of this chapter.

The first two nodes are the rate and the level you were given: what arrives, and what
accumulates.

```{literalinclude} ../models/web_service/stages/01-demand/model.yaml
:language: yaml
:start-at: peak_request_rate_t0:
:end-before: annual_growth:
```

Four lines in each of those are the argument of this book. The rest are convenience. `kind` and
`unit` let the toolkit tell a level from a rate. `value` is the number a spreadsheet would have
held on its own. `provenance` is the line a cell has nowhere to put. A number with no source is a
rumour, so the field is mandatory from the very first node.
[ch03](#where-the-numbers-come-from) is about what that costs and what it buys.

`label` and `range` are neither. A label reads better in a table than `stored_data_t0` does. A
range is how far a slider may drag the value on the interactive version of this model. Both are
optional. [Appendix A](#appendix-a-dsl-reference) lists everything a node may carry, which is
longer than what a node needs.

Growing them over the horizon takes one exponent and one thing that is easy to miss:

```{literalinclude} ../models/web_service/stages/01-demand/model.yaml
:language: yaml
:start-at: annual_growth:
:end-before: peak_request_rate:
```

`horizon / one_year` looks like ceremony and is not. Growth compounds, so the horizon has to be an
exponent, and an exponent has to be a pure number. Five years is a duration. Five is a number.
Dividing the duration by a declared year is how the first becomes the second. A spreadsheet does
this silently and correctly, right up to the quarter when somebody types a horizon in months into
the same cell.

Then the two quantities at the end, which are the first in this book that are *computed* rather
than stated:

```{literalinclude} ../models/web_service/stages/01-demand/model.yaml
:language: yaml
:start-at: peak_request_rate:
:end-before: outputs:
```

That is the whole of the demand side. Here it is, with the toolkit that reads it: this
repository's, not a copy. Press **Run**, then change a number and watch the total move. Change
`stored_data`'s formula to multiply the request rate by a count of periods, and the toolkit
refuses, for the reason at the top of this chapter.

```{iframe} /playground/what-a-workload-is/
:width: 100%
The file above, running. The first press fetches a Python runtime; after that a check takes milliseconds.
```

### The demand and the decisions

A model's inputs are two different kinds of thing wearing the same clothes. Some describe what the
world is doing to you. The rest describe what you have decided to do about it. Separating them is
the first thing worth doing to any model, including this one:

```{include} _generated/what-a-workload-is-service.md
```

Every quantity is filed under *what you decide*, and one of them is the growth rate. Nobody
decides a growth rate.

The table is not wrong about the model. The model is wrong, and the table shows you the only
signal it has: whether somebody gave the quantity a shape instead of a single number. A shape says
*the world settles this one, and here is how much it varies*. One number says *I chose this*.
Nothing in the file has a shape yet, so everything reads as a choice.
[ch04](#peak-mean-and-growth) gives the growth rate one, and this table splits in two for the
first time.

That is worth more here than a correct table would have been, because the failure is the useful
one. **An input you gave a single value to, and cannot actually control, is an assumption you
have stopped noticing.** A model that files its inputs this way finds them by construction. The
busy hour on day one is sitting in the same list, and that one is not a decision either.

Once the table does separate, the half worth arguing about is *what you decide*, because it is the
half anybody can change. Most sizing conversations are spent on the other one.

The *Claim* column asks something else: how much the person who wrote each number down was
claiming. **●** means traceable to a measurement or a definition. **◐** means supplied by whoever
is selling it. **○** means somebody's assumption. [ch03](#where-the-numbers-come-from) is about
what that difference is worth.

### What it says, and what the toolkit calls it

Nothing so far has run. The file is a description. What reads it is
[`sizing`](#appendix-a-dsl-reference), the toolkit, and one command points it at every model in
the repository:

```bash
make models
```

That parses each file, refuses any formula whose units do not work out, evaluates the graph in
dependency order, and writes what it found to `bench/results/`. That directory is where every
figure in this book comes from, including the next one. Every table about the service is computed
from this file as the chapter you are in has left it, so you can reproduce any of them from what
you have already read. For the eight nodes above:

```{include} _generated/what-a-workload-is-stage.md
```

A number, out of a handful of numbers and a multiplication. The arithmetic is right, and you
should not act on it, for the reason [ch01](#point-estimates) gave: every figure that went in was
a single figure, and not one of them is known that precisely. Here that stops being an argument
and becomes a file you are holding. [ch04](#peak-mean-and-growth) takes the first of those
figures apart.

The toolkit has already decided what kind of model this is, too:

```{include} _generated/what-a-workload-is-stage-shape.md
```

The last row is not a label anybody typed. The loader works it out from what is in the file.
Nothing here has a measured constant or a declared limit in it, so what you have is a **cost
model**: a structure nobody doubts, with uncertain numbers in it. It does not stay one. What
changes it is something added to the file, not a chapter announcing it. That is why
[ch01](#point-estimates)'s second problem is to find the stage where it happens.

### The same split, on a model that is finished

Here is the table doing what it is for. This is a different system: an observability platform,
carrying metrics, logs and traces. Every input in its model has been given either a shape or a
value, so both lists are populated:

```{include} _generated/what-a-workload-is-observability.md
```

Read the decisions. Scrape interval, retention, sampling rate, how many log lines you keep: those
are the four knobs an observability platform gives you.
[Appendix F](#appendix-f-observability-model) shows what turning all of them down actually buys.

Then read the demand, and notice what is *not* in the decisions: the number of label values. It
dominates the whole model and it is not a knob. That is [ch08](#regime-changes)'s subject.

### A workload can be described badly in three ways

**Averaged.** A daily mean is the one number nobody experiences. [ch04](#peak-mean-and-growth) is
about which number in a demand curve sizes you, and it is not that one.

**In the wrong units.** "Ten thousand users" is not a workload. It is a fact about a licence
agreement. What sizes a system is what those users cause: requests, bytes, series, queries. The
translation between the two is a measured constant, and usually the shakiest number in the model.

**As a single point in time.** A workload that does not state a growth rate is a workload stated
for today, and nobody buys infrastructure for today.

### What the demand side leaves out

Two of the rows in the table above are the workload proper: how fast requests arrive, and how much
is held. What is not in the file yet is what each request *costs*: how much of a processor's time
it takes. That quantity, with the arrival rate and a count of machines, is what
[ch05](#littles-law) through [ch07](#when-adding-servers-stops-helping) are built on. It is not
here because it is not a fact about the workload. It is a fact about one build of the software on
one kind of machine. Somebody has to measure it, and [ch05](#littles-law) says what that changes.
The demand side describes what is asked of the system. How the system behaves under it is a
distinction this table cannot draw, and the next part exists to make it.

## What this cannot tell you

**Whether the quantities are the right ones.** A workload description is a model of demand, and
like every model it leaves things out. The web service model has no notion of requests that differ
from each other: a busy hour of cheap reads and one of expensive writes are the same number in
it. The observability model has no notion of query shape. Each omission is defensible, and each
one is a place the answer could be wrong in a way nothing here would show.

**Where the numbers come from.** Every figure in the tables above is an input somebody wrote down.
Some are measured, most are not, and this chapter has said nothing about the difference.
[ch03](#where-the-numbers-come-from) is about that difference, and how much any of this is worth
depends on it.

**Whether a peak is a peak.** "The busy hour" is a phrase, not a measurement. Whether your busy
hour is an hour, a minute or a Tuesday in November is a property of your traffic, and sizing for
the wrong one is expensive in both directions.

**How the demand quantities move together.** Every table above lists them separately, as though
request rate and log volume were unrelated. They are not. Treating them as unrelated makes every
interval in the book too narrow ([ch14](#correlation-and-convergence)).

## Problems

Five, in `tests/what_a_workload_is/`. The first four have tests. The last does not, and says why.

**2.1 — Levels and rates.**
Classify every node in the observability model as a stock, a flow or neither, by reading what it
means. The test classifies the same nodes by their declared units. Where your reading and the
model's units disagree, one of them is wrong. Finding out which is the exercise.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_1_stocks_and_flows.py
```

**2.2 — Turn a rate into a volume.**
Add a node giving terabytes a day of telemetry. A rate times a pure number is still a rate, and
the toolkit will keep saying so until something in the formula carries a duration.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_2_daily_volume.py
```

**2.3 — The smallest model that builds.**
Write a model file of your own with one input and one derived node that passes the loader, the
dimensional pass and every rule in `scripts/verify-models.py`. Read the rules before you start;
the refusals are the point.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_3_smallest.py
```

**2.4 — Break it on purpose, in a way that still loads.**
Write a second model that loads cleanly and is wrong about units. Not a typo: those fail
immediately and teach nothing. Write a node that declares a unit its own formula cannot produce.
A spreadsheet cannot see that class of error at all.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_4_broken.py
```

**2.5 — Your own workload, written down.** No test: this is about a system you run, and there is
no oracle for it.

Take something you operate and write down the quantities that describe what it has to do. Not the
metrics you happen to collect: the quantities somebody would need to size it. Give each one a
unit. Then sort them: which are rates, which are levels, which are neither.

Two things to look for when you have finished. Is there a quantity you could not give a unit to?
That is usually two quantities sharing a name, and splitting them is the work. And is there
anywhere you have sized a store from a rate, a retention volume derived from a per-second figure
with no duration anywhere in the chain? That is the error this chapter exists to prevent. It is
much easier to find in your own notes than to believe in the abstract.

A good answer fits on one page, has a unit against every line, and leaves you less sure about at
least one quantity than you were before you wrote it down.

## Where to go next

[ch03](#where-the-numbers-come-from) is the question this chapter kept deferring: once you have
written a quantity down, what are you actually claiming about it?

[ch04](#peak-mean-and-growth) is the other one: demand moves, so which value of it sizes you?
