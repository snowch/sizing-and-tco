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

Which quantities size a system, and which only look as though they do?

The people who own the service tell you what it has to do. Before you can multiply any of it into a
number of machines, you write each quantity down with a unit.
The first distinction is between a rate and a level. That matters because sizing the storage for
data you keep for a retention period from the rate it arrives, without multiplying by the period,
gives you the wrong answer.

This chapter writes the first nodes of the model the rest of the book uses. By the end, you have a
model file of eight quantities. The toolkit reads it, checks every unit, and works out the demand at
the end of your purchase cycle.

## The material

### Four kinds of quantity: flows and stocks get confused

:::{div}
:class: definition

**A flow** is a rate. Requests per second, bytes per second, dollars per year. It has time
underneath it. You cannot store one and you cannot run out of one. Adding two of them means
something only if they cover the same period.
:::

:::{div}
:class: definition

**A stock** is a level. Terabytes held, requests in flight. It is how much there is right now. You
*can* run out of a stock: a disk fills, memory fills.
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
:::

A quantity's unit says which of the four kinds it is. Because of that, the toolkit can check every
formula by its units, and every node in this book must declare a unit. A flow has time in its
denominator (per second), a duration has time in its numerator (years), a stock and a ratio have
none.

The commonest error in sizing turns a flow into a stock by multiplying it by a plain number
instead of by an amount of time. Requests a second times five is still requests a second: five
times as many of them, arriving just as fast, and not one of them stored anywhere. Requests a
second times five *seconds* is requests, which is a thing you can hold. The plain number changes
how much; only the duration changes what kind.

A spreadsheet shows the same digits either way and cannot tell you
which kind they are. The toolkit refuses a formula whose units do not produce the node's declared
unit. Problem 2.2 asks you to avoid this error. [Appendix D](#appendix-d-units) shows how
units combine and cancel, on a page of examples the toolkit works out itself.

### Writing down the first quantities

A model is a file of named quantities, each with a unit and a source. A spreadsheet can hold both:
a source in a comment or column, a unit in a header or cell format. But nothing forces you to fill
them in, and nothing checks that you have. Without a required place, facts stay in the head of
whoever built the sheet and leave with that person. The facts lost include where a value came
from, what version of what you measured it against, whether it is a vendor's claim, or whether it
was agreed by people who have since left. When `=B4*C7` multiplies a count of hosts by a request
rate, formulas ignore units and do not track sources. You get a number; nothing tells you it is
neither bytes nor requests, and nothing tells you which inputs were guesses.

The model is one text file in YAML. A change to it shows up line by line, and you can review it
like code. This chapter adds a few nodes at a time, each when you have learned what it needs.

The people who own the service give you two figures: how many requests arrive in the busy hour, and
how much data the service holds today. Neither was measured; both are their estimates. Start with
the first one:

```{literalinclude} ../models/web_service/stages/01-demand_inputs_single/model.yaml
:language: yaml
:start-at: peak_request_rate_t0:
:end-at: range: [500, 40000]
```

```{iframe} /models/web_service_demand_inputs_single-reference.html
:width: 100%

One input: the busy-hour request rate.
```

Blue means input: a number the model is given rather than works out. How many requests arrive in
the busy hour depends on your users, so it is outside your control, and this node has no bar down
its left edge. An input you choose, like the horizon later in this chapter, has that bar. Open the
Inputs box to see the slider: it exists because this node declares the `range` quoted above. Click
the node to open Details, which shows that the busy-hour figure is an assumption, and why.

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

Look at the lines in the two files quoted above. Four matter most: `kind`, `unit`, `value`
and `provenance`. `kind` says what sort of node it is: `input` is a number the model is given.
`unit` lets the toolkit tell a level from a rate and check every formula. `value` is the number a
spreadsheet would have held. `provenance` records where the value came from and what kind of source
it is. A source is optional and unchecked in a spreadsheet, but here the build refuses an input without
one, and you can read it in the viewer's Details panel. A
number without provenance is a rumour.
[ch03](#where-the-numbers-come-from) explains the three kinds of source.

Three lines are optional: `label`, `note` and `range`. `label` reads better in a table than
`stored_data_t0` does. `note` answers what a reader of the file would otherwise have to ask you; the
note on `stored_data_t0` explains why it stays a single number when the busy-hour figure will not.
`range` sets how far the slider can drag the value. [Appendix A](#appendix-a-dsl-reference) lists
every line a node can have.

### Adding growth and time

The two inputs describe the workload today, on day one. You buy hardware to last years. Both the request rate and the data held grow. The model needs to
know how fast they grow, and how long you are buying for.

Here are three more quantities:

```{literalinclude} ../models/web_service/stages/03-demand_inputs_all/model.yaml
:language: yaml
:start-at: annual_growth:
:end-before: outputs:
```

```{iframe} /models/web_service_demand_inputs_all-reference.html
:width: 100%
Five inputs, and none worked out from another yet.
```

**Five inputs, and no arithmetic yet.** All five nodes are blue: numbers the model is given. Dragging
any slider leaves the others alone, because nothing is worked out from anything yet.

`annual_growth` is the factor demand multiplies by each year; a factor above one means growth.
`horizon` is how long until you buy again: the refresh cycle you size for, and your choice.
`one_year` is a year; you do not choose it, it is true by definition. It is there because growth
compounds, so the horizon becomes an exponent, and an exponent must be a pure number.

`horizon / one_year` divides the duration by a year and leaves a pure number of years. A spreadsheet
holds the horizon as a bare number, which works until a colleague types the horizon in months into
the same cell. Growth then compounds over twelve times as many periods, and nothing warns you. The
toolkit converts months to years before dividing, so the answer stays right.

### Computing what you need: deriving the horizon as an exponent

The file now has five inputs. Next, the toolkit works out its first quantity from a formula over
two of them, the horizon and one year:

```{literalinclude} ../models/web_service/stages/04-demand_horizon_exponent/model.yaml
:language: yaml
:start-at:   horizon_periods:
:end-before: outputs:
```

```{iframe} /models/web_service_demand_horizon_exponent-reference.html
:width: 100%
The first derived node.
```

**Hollow means derived.** `horizon_periods` is an outline because the toolkit works it out from the
formula `horizon / one_year`. The `kind: derived` line says its value is not stated, only computed.
The toolkit checked that the formula gives a pure number before accepting it. Drag the horizon slider and `horizon_periods` changes
with it. Click the node to see the formula in Details.

### Growing the demand to the horizon

Now take the two quantities you started with, the rate and the stock at day one, and grow them
to the end of the purchase cycle. That takes two more derived quantities:

```{literalinclude} ../models/web_service/stages/05-demand/model.yaml
:language: yaml
:start-at:   peak_request_rate:
:end-at:     formula: stored_data_t0 * annual_growth ** horizon_periods
```

`peak_request_rate` is the flow at the horizon; `stored_data` is the stock at the horizon. Both
multiply the day-one value by the growth factor raised to `horizon_periods`, the number of years
from day one to the horizon.

You now have eight quantities: three outside your control (busy-hour
rate, data held, growth factor), one you choose (horizon), one true by definition (`one_year`), and
three the toolkit computes (`horizon_periods`, `peak_request_rate`, `stored_data`).

### The demand side, complete

Here is the complete demand model. Dragging an input moves only the nodes its arrows lead to. Try
*annual growth factor*: *peak request rate at horizon* and *records held at horizon* move with it.
Drag *records held, day one* instead and the request rate stays put. Click a hollow node to read its
formula, a blue one to see where its value came from.

```{iframe} /models/web_service_demand-reference.html
:width: 100%
The complete eight-node demand model.
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

Every input in the file looks the same, but they describe two different things. Some show what is
outside your control: what your users send and how much data they create. The rest show what you
have decided. Separate them first, in any model, including this one:

```{include} _generated/what-a-workload-is-service.md
```

The table groups the inputs as the file does, on each input's `decided:` line, and the build
refuses a file that leaves one out. A year is true by definition because it is a year whoever
asks.

Look at the "Outside your control" group. Each is a single number you cannot change. You do not
decide a growth rate, yet the file states one as flatly as the horizon. **An input you gave a single
value to, and cannot control, is an assumption you have stopped noticing.**
[ch04](#peak-mean-and-growth) replaces that single number with a spread: how low and how high growth
might turn out.

The decisions are the only inputs you can change. Arguing over a number outside your control does
not change it; measuring it narrows it.

The *Claim* column shows how much the person who wrote each number down was claiming. **●** means
traceable to a measurement or a definition. **◐** means supplied by the vendor selling it. **○**
means an assumption.

### What the file computes, and what kind of model it is

Every number in the demand model above came from running this file.
[`sizing`](#appendix-a-dsl-reference), the toolkit, reads the file, checks that every formula
produces the unit its node declares, and works each node out from its dependencies. That is all
running a model means. The table that follows shows what it produced:

```{include} _generated/what-a-workload-is-stage.md
```

The table shows the request rate and data held at the horizon, worked out from five inputs and a
growth formula. The arithmetic is right, and you should not act on it, for the reason
[ch01](#point-estimates) gave: every input was a single figure, and none is known that precisely.
Now the inputs are in a file you can open and change.

The toolkit has already decided what kind of model this is, too:

```{include} _generated/what-a-workload-is-stage-shape.md
```

No one typed the last row of the table: the loader works it out from the kinds of node in the
file. The file has no measured constant and no declared limit, so what you have is a **definitional
model**: a structure no one doubts, with uncertain numbers in it. It stops being one when a later
chapter adds a measured node or a ceiling to the file. [ch01](#point-estimates)'s problem 1.3 asks you to name those nodes in three model
descriptions.

### The same split, on a model that is finished

Here is the same table for a finished model of a different system: an observability platform,
carrying metrics, logs and traces:

```{include} _generated/what-a-workload-is-observability.md
```

% word-ok: a scrape interval is a length of time and a sampling rate is a trace setting
Read the *What you decide* group. Four of them are the knobs the platform gives you: scrape
interval, retention, trace sampling rate, and the fraction of log lines you keep. The rest are the
fleet you buy to run it, and the horizon. [Appendix F](#appendix-f-observability-model) shows what
turning all four down saves.

Now read the *Outside your control* group. Notice what is *not* among the decisions: the number of
label values. A label is a tag on each metric, such as the endpoint or the status code, and each
distinct value multiplies the number of series the platform stores. It dominates the model, and no
platform knob reaches it: turn all four down and the label count stays where it was. The only lever
is the application code that emits the labels, which belongs to the developers who wrote the
application, not the team running the platform. [ch08](#regime-changes) is about that distinction.

### A workload can be described badly in three ways

**Averaged.** A daily mean is the one number nobody experiences. [ch04](#peak-mean-and-growth) is
about which number in a demand curve sizes you, and it is not that one.

**In the wrong units.** A count of users is not a workload; it is a fact about a licence agreement.
What sizes a system is what those users cause: requests, bytes, queries. The translation from users
to requests needs a measured constant: requests per user. It changes whenever users change how they
use the product, so it needs re-measuring.

**As a single point in time.** A workload that does not state a growth rate is a workload stated
for today, and nobody buys infrastructure for today.

### What the demand side leaves out

Two of the rows in the web service table above are the workload proper: how fast requests arrive,
and how much is held. What is not in the file yet is what each request *costs*: how much processor
time it takes. It is not here because it is not a fact about the workload. It is a fact about one
build of the software on one kind of machine, so it must be measured on that machine before the next
chapters' arithmetic can run. That processor time, the arrival rate, and a count of machines are
what [ch05](#littles-law) through [ch07](#when-adding-servers-stops-helping) build on. The demand
side says what is asked of the system. How the system responds, slowing down as it fills for
instance, is what those chapters add.

## What this cannot tell you

**Whether the quantities are the right ones.** A workload description is a model of demand, and
like every model it leaves things out. The web service model has no notion of requests that differ
from each other: a busy hour of cheap reads and one of expensive writes are the same number in
it. The observability model has no notion of query shape. Each omission is defensible, and each
one is a place the answer could be wrong in a way nothing here would show.

**Where the numbers come from.** Every figure in the tables above is an input the model's author
wrote down. This chapter marked each one's claim, but has not shown how to judge a claim or improve
one. [ch03](#where-the-numbers-come-from) does, and whether you can trust these answers depends on
it.

**Whether a peak is a peak.** "The busy hour" is a phrase, not a measurement. Whether your peak
lasts an hour, a minute, or comes once a year is a property of your traffic. Size for too long a
peak and you pay for hosts that sit idle; size for too short a peak and the service falls over when
the real peak arrives.

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
- **A model is a file of named quantities, each with a unit and a source.** A spreadsheet can hold
  both, but does not require either and does not check them. The file requires both on every input,
  and the toolkit checks every formula against the units.
- **Growth compounds, so the horizon has to become a pure number.** Dividing the duration by a
  declared year is what turns it into an exponent, and a spreadsheet does that silently until
  a colleague types months.
- **Separate what is outside your control from what you decided.** An input given a single value
  that you cannot control is an assumption you have stopped noticing.
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

[ch03](#where-the-numbers-come-from) answers the question this chapter kept deferring: once you have
written a quantity down, what are you claiming about it?

[ch04](#peak-mean-and-growth) is the other one: demand moves, so which value of it sizes you?
