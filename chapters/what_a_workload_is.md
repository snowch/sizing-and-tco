---
title: "What a workload is"
short_title: "ch02 What a workload is"
---

(what-a-workload-is)=
# ch02 · What a workload is

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

Which quantities actually size a system, and which only look as though they do?

Somebody has told you what the system has to do. Before any of it can be multiplied into a number
of machines, it has to be written down in a form that cannot quietly mean two things. The first
distinction that matters is between a rate and a level. That sounds like pedantry until somebody
sizes a retention store from a rate.

This chapter writes the first nodes of the model the rest of the book uses. By the end of it you
will have a file that runs.

## The material

### Four kinds of quantity, and two of them get confused

:::{div}
:class: definition

**A flow** is a rate. Requests per second, bytes per second, dollars per year. It has time
underneath it. You cannot store one and you cannot run out of one. Adding two of them means
something only if they cover the same period.
:::

:::{div}
:class: definition

**A stock** is a level. Terabytes held, series alive, requests in flight. It is how much there is
right now. You *can* run out of one, and that is usually what a ceiling is about.
:::

:::{div}
:class: definition

**A duration** is a length of time. A horizon, a retention period, the time one request spends in
the system. It is what turns one of the first two into the other: a flow kept up for a duration is
a stock, and a stock used up over a duration is a flow.
:::

:::{div}
:class: definition

**Everything else is a ratio, a pure number or a price.** A replication factor, a compression ratio,
a cost per terabyte. These have no time in them at all. They are the constants of a **sizing
chain**: the string of multiplications that runs from a workload to a number of machines.
::::

The unit tells you which is which. That is why the toolkit can check it, and why every node in
this book declares one. A flow has time in its denominator, a duration has it in its numerator,
and a stock and a ratio have none.

The commonest error in sizing turns a flow into a stock by multiplying it by a plain number
instead of by an amount of time. Requests a second times five is still requests a second: five
times as many of them, arriving just as fast, and not one of them stored anywhere. Requests a
second times five *seconds* is requests, which is a thing you can hold. The plain number changes
how much; only the duration changes what kind.

That is why a retention store sized from a rate comes out wrong rather than merely imprecise. A
spreadsheet gives the same digits either way and cannot say which quantity they are. The toolkit
refuses it, and problem 2.2 is that error. [Appendix D](#appendix-d-units) shows how units combine and cancel, on a page of
examples the toolkit works out itself.

### Writing down the first quantities

A model is a file of named quantities, each with a unit and a source. A spreadsheet cell holds a
value and nothing else. It does not hold the fact that the value was measured last March against
version 2.4 of something. It does not say that the value is a vendor's claim nobody has checked,
or that it was agreed in a meeting by people who have since left. Those facts live in the head of
whoever built the sheet, and they leave when that person does. Nor does a cell have a unit.
`=B4*C7` is as valid as any other product, and multiplying series by requests gives a number that
looks like a number of bytes.

A model in YAML diffs and reviews like code. It is one file. This chapter builds it a piece at a
time, as concepts appear.

You are given two facts about your workload: how many requests arrive in the busy hour, and how
much data you hold. Start with the first one:

```{literalinclude} ../models/web_service/stages/01-demand_inputs_single/model.yaml
:language: yaml
:start-at: peak_request_rate_t0:
:end-at: range: [500, 40000]
```

```{iframe} /models/web_service_demand_inputs_single-reference.html
:width: 100%

One input. Click the node to see where its value came from. Open *Inputs* and drag the slider,
and the graph recomputes as you drag.
```

Blue means input: a number the model is given rather than works out. The world sets the busy hour,
not you, so this node has no bar down its left edge. An input you do choose, like the horizon later
in this chapter, has one. Open the Inputs box to see the slider: it exists because this node
declares the `range` quoted above. Click the node and Details shows that the busy-hour figure is an
assumption, and why.

Now add the second one:

```{literalinclude} ../models/web_service/stages/02-demand_inputs_initial/model.yaml
:language: yaml
:start-at: stored_data_t0:
:end-at: range: [1, 200]
```

```{iframe} /models/web_service_demand_inputs_initial-reference.html
:width: 100%

Interactive viewer: two independent inputs. Drag a slider to change its number only.
```

**These two are independent.** When you drag one slider, only that node's number changes. Its row
in the Outputs list updates; the other node's row is greyed out because it does not move. No edges
connect these nodes yet. Once you add arithmetic later in this chapter, dragging one input will
move others.

Four lines in each node matter most: `kind`, `unit`, `value` and `provenance`. `kind` and `unit`
let the toolkit tell a level from a rate. `value` is the number a spreadsheet would have held.
`provenance` records where the value came from and what kind of source it is. A spreadsheet cell
has no place for provenance, but you can read it in the quoted file above and in the viewer's
Details panel. A number without provenance is a rumour, so you must provide it from the first
node. [ch03](#where-the-numbers-come-from) shows the three source kinds, what each lets a reviewer
do, and how to turn an assumption into a measurement.

Three lines are optional: `label`, `note` and `range`. `label` reads better in a table than
`stored_data_t0` does. `note` answers questions you might have when reading the file. The note on
`stored_data_t0` above explains why it is a single number when the busy hour will not be. `range`
sets how far the slider can drag the value. [Appendix A](#appendix-a-dsl-reference) lists
everything a node may carry.

### Adding growth and time

You have measured the workload today. But infrastructure is bought for years, not days. The
quantity grows. You need to say how fast, and how long you are buying for.

Here are three more quantities:

```{literalinclude} ../models/web_service/stages/03-demand_inputs_all/model.yaml
:language: yaml
:start-at: annual_growth:
:end-before: outputs:
```

```{iframe} /models/web_service_demand_inputs_all-reference.html
:width: 100%
Interactive viewer: all five inputs. Notice that no derived quantities exist yet — the model shows only what you choose or define.
```

**Five inputs, and no arithmetic yet.** All five nodes are blue: numbers the model is given. Dragging
any slider leaves the others alone, because nothing is worked out from anything yet.

`annual_growth` is what it says. `horizon` is your purchase cycle — the refresh window you are
sizing for. `one_year` is not a choice. It is here because growth compounds exponentially, and an
exponent must be a pure number.

That last point is easy to miss and crucial. `horizon / one_year` looks like ceremony and is not.
Five years is a duration — something with time in it. Five is a number — dimensionless. Growth
compounds, so the horizon has to be an exponent, and an exponent must be a pure number. Dividing
the duration by a declared year is how the first becomes the second. A spreadsheet does this
silently and correctly, until the quarter when somebody types a horizon in months into the same
cell.

### Computing what you need: deriving the horizon as an exponent

You have given the toolkit five quantities. Now it computes one, not from direct measurement but
from a formula applied to the five you gave:

```{literalinclude} ../models/web_service/stages/04-demand_horizon_exponent/model.yaml
:language: yaml
:start-at:   horizon_periods:
:end-before: outputs:
```

```{iframe} /models/web_service_demand_horizon_exponent-reference.html
:width: 100%
Interactive viewer: the first derived node. Drag the horizon slider and watch horizon_periods compute instantly. Click horizon_periods to see its formula.
```

**Hollow means derived.** One node is now an outline with nothing inside: `horizon_periods`. The
toolkit works it out from a formula applied to the blue nodes. Drag the horizon slider and it
changes instantly. Click it to see the formula: `horizon / one_year`. The toolkit checked that the unit was correct before accepting it. A spreadsheet would just give you a number and say nothing.

`kind: derived` means this quantity is not stated — it is computed. The toolkit reads the formula,
checks that it produces the unit the node declares, works it out, and stores the result. This is
the first quantity in the book that you do not measure or decide: the toolkit makes it from the
others.

The formula `horizon / one_year` is unit division: a duration divided by a duration produces a
pure number. That number is the exponent for growth. Change the horizon value and watch
`horizon_periods` change with it.

### Growing the demand to the horizon

Now take the two quantities you started with — the rate and the stock at day one — and grow them
to the end of the purchase cycle. That takes two more derived quantities:

```{literalinclude} ../models/web_service/stages/05-demand/model.yaml
:language: yaml
:start-at:   peak_request_rate:
:end-at:     formula: stored_data_t0 * annual_growth ** horizon_periods
```

`peak_request_rate` is the flow at the horizon. `stored_data` is the stock at the horizon. Both
use the same growth formula: the initial value, times the growth factor raised to an exponent (the
number of years that have passed).

That completes the demand side. You have written eight quantities: four you choose or measure,
one you define (one_year), three the toolkit computes (horizon_periods, and the two projections).

### The graph, running

Drag a slider. Everything downstream changes instantly—watch which nodes move when you change each one. That shows you the dependencies. Click a derived node and read its formula. Click an input node and see where it came from. The colours and arrows are the language. The sliders and clicks are how you read it.

### The demand side, complete

Here it is all together. Drag *annual growth factor* and watch *peak request rate at horizon*
and *records held at horizon* move with it.

```{iframe} /models/web_service_demand-reference.html
:width: 100%
An interactive reference of the eight-node demand model, ready to explore.
```

From here on, a chapter quotes only the part of the file it is about, and the viewer holds the
rest. Click a node and open *In the file* under Details to see its lines. On a screen wide enough
for the graph and both panels side by side, press **Expand** and choose **Model file** to read the
whole file, with the node you clicked marked.

The toolkit also checks the file before it works anything out. Change `stored_data`'s formula to
multiply the request rate by a plain number and it refuses: the node holds terabytes, and a rate
times a plain number is still a rate. The formula is wrong, not imprecise. Problem 2.4 has you
write a mistake of that kind and watch it caught.

### The demand and the decisions

A model's inputs are two different kinds of thing wearing the same clothes. Some describe what the
world is doing to you. The rest describe what you have decided to do about it. Separating them is
the first thing to do to any model, including this one:

```{include} _generated/what-a-workload-is-service.md
```

Three quantities are the world's: the busy hour, the data you hold, and how fast both grow. One is
yours: the horizon, which is when you plan to buy again. A year is a year whoever asks, so it is
true by definition. The file says which is which on every input, in its `decided:` line, and the
build refuses a file that leaves one out.

Now look at the world's half. Every quantity in it is a single number, and none of them is yours to
set. Nobody decides a growth rate, yet the file states one as flatly as the horizon beside it.
**An input you gave a single value to, and cannot control, is an assumption you have stopped
noticing.** [ch04](#peak-mean-and-growth) replaces the growth rate's single number with a spread:
how low and how high the world might settle it.

The half worth arguing about is *what you decide*, because it is the half anybody can change. Most
sizing conversations are spent on the other one.

The *Claim* column asks something else: how much the person who wrote each number down was
claiming. **●** means traceable to a measurement or a definition. **◐** means supplied by whoever
is selling it. **○** means somebody's assumption. [ch03](#where-the-numbers-come-from) is about
what that difference is worth.

### What the file computes, and what kind of model it is

You have seen it run already: every number on the graph above came from running this file.
[`sizing`](#appendix-a-dsl-reference), the toolkit, reads the file, checks that every formula
produces the unit its node declares, and works each node out from the ones it depends on. That is
all running a model is, and its numbers are the next table:

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
Nothing here has a measured constant or a declared limit in it, so what you have is a
**definitional model**: a structure nobody doubts, with uncertain numbers in it. It does not stay one. What
changes it is something added to the file, not a chapter announcing it. That is why
[ch01](#point-estimates)'s second problem is to find the stage where it happens.

### The same split, on a model that is finished

Here is the same table for a finished model of a different system: an observability platform,
carrying metrics, logs and traces:

```{include} _generated/what-a-workload-is-observability.md
```

% word-ok: a scrape interval is a length of time and a sampling rate is a trace setting
Read the decisions. Four of them are the knobs an observability platform gives you: scrape
interval, retention, sampling rate, and how many log lines you keep. The rest are the fleet you buy
to run it.
[Appendix F](#appendix-f-observability-model) shows what turning all of them down buys.

Then read the world's half, and notice what is *not* among the decisions: the number of label values.
It dominates the model, and no knob on the platform reaches it. Turn all four of them down and
the label count sits exactly where it was. The only lever is the code that emits the labels, and
that belongs to whoever wrote the application rather than to whoever runs the platform — which is
[ch08](#regime-changes)'s subject.

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
it takes. It is not here because it is not a fact about the workload. It is a fact about one build of the
software on one kind of machine, which means somebody has to go and measure it before any of the
next part's arithmetic can run. That quantity, the arrival rate and a count of machines are what
[ch05](#littles-law) through [ch07](#when-adding-servers-stops-helping) are built on.
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
range this book reports too narrow ([ch14](#correlation-and-convergence)).

## Key takeaways

:::{div}
:class: takeaways

- **A flow is a rate, a stock is a level, and the unit tells them apart.** A flow has time
  underneath it. A stock is how much there is now. Ratios, counts and prices have no time in them at
  all.
- **The commonest sizing error turns a flow into a stock by multiplying it by a plain number.** A
  rate times a number is still a rate. Only a duration makes it an amount, and the toolkit refuses
  the other.
- **A model is a file of named quantities, each with a unit and a source.** A spreadsheet cell holds
  a value and nothing about it. The file holds where the value came from and what it is measured in.
- **Growth compounds, so the horizon has to become a pure number.** Dividing the duration by a
  declared year is what turns it into an exponent, and a spreadsheet does that silently until
  somebody types months.
- **Separate what the world does to you from what you decided.** An input given a single value that
  you cannot control is an assumption you have stopped noticing.
:::

## Problems

Five, in `tests/what_a_workload_is/`. The first four have tests. The last does not, and says why.

**2.1 — Levels and rates.**
Classify every node in the observability model as a stock, a flow or neither, by reading what it
means. The test classifies the same nodes by their declared units. Where your reading and the
model's units disagree, one of them is wrong. Finding out which is the exercise.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_1_stocks_and_flows.py -m problem
```

**2.2 — Turn a rate into a volume.**
Add a node to the observability model giving terabytes a day of telemetry. A rate times a pure
number is still a rate, and the toolkit will keep saying so until something in the formula
carries a duration.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_2_daily_volume.py -m problem
```

**2.3 — The smallest model that builds.**
Write a model file of your own with one input and one derived node that passes the loader, the
dimensional pass and every rule in `scripts/verify-models.py`. Read the rules before you start;
the refusals are the point.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_3_smallest.py -m problem
```

**2.4 — Break it on purpose, in a way that still loads.**
Write a second model that loads cleanly and is wrong about units. Not a typo: those fail
immediately and teach nothing. Write a node that declares a unit its own formula cannot produce.
A spreadsheet cannot see that class of error at all.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_4_broken.py -m problem
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
written a quantity down, what are you claiming about it?

[ch04](#peak-mean-and-growth) is the other one: demand moves, so which value of it sizes you?
