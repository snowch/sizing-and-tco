---
title: "What a workload is"
short_title: "ch02 What a workload is"
---

(what-a-workload-is)=
# ch02 · What a workload is

## The question

Which quantities size a system, and which only look as though they do?

The people who own the service tell you what it has to do. Before you can multiply any of it into a
number of machines, you write each quantity down with a unit.

The first distinction is between a rate, which says how fast something arrives, and a level, which
says how much of it there is. This distinction matters because confusing them leads to sizing
errors. Suppose you keep data for a retention period and calculate its storage need from the rate it
arrives, without multiplying by the period. You get the wrong answer: you have a rate, not an amount
of storage.

This chapter writes the first nodes of the model the rest of the book uses. By the end, you have a
model file of eight quantities. The toolkit reads it, checks every unit, and works out the demand at
the end of your purchase cycle.

## The material

### Four kinds of quantity

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
formula by its units, and every node in this book declares a unit.

% word-ok: bytes per sample is a unit, the size of one stored data point
- A flow has time in its denominator: per second, per month. Examples: requests per second,
  megabytes per second.
- A duration has time in its numerator: years, days, seconds.
- A stock names an amount, with no *per* in its unit: hosts, terabytes, series, requests.
- Everything else is a ratio, a pure number or a price. It has no unit, or has *per* followed by
  something other than time: terabytes per node, bytes per sample, series per host.

A count that multiplies something else has no unit—it is a pure number, not a stock. A replication
factor counts copies; the number of values a label takes multiplies the number of series. A price
per month has time in its denominator, so it is a flow of money: storage at so much per terabyte per
month.

One error in sizing turns a flow into a stock by multiplying it by a plain number instead of by
an amount of time. Requests a second times five is still requests a second: five times as many of
them, arriving just as fast, and not one of them stored anywhere. Requests a second times five
*seconds* is requests, which you can hold. The plain number changes how much; only the duration
changes what kind.

A spreadsheet shows the same digits either way and cannot tell you
which kind they are. The toolkit refuses a formula whose units do not produce the node's declared
unit. Problem 2.2 asks you to avoid this error. [Appendix D](#appendix-d-units) shows how
units combine and cancel, on a page of examples the toolkit works out itself.

### Writing down the first quantities

A model is a file of named quantities, each with a unit and a source. A spreadsheet can hold both: a
source in a comment or a column, and a unit in a header or a cell format. Nothing forces you to fill
them in, and nothing checks that you have. Without a required place for them, four facts stay in
the head of whoever built the sheet and leave with that person:

- where a value came from;
- which version of what you measured it against;
- whether it is a vendor's claim;
- whether it was agreed by people who have since left.

When `=B4*C7` multiplies a count of hosts by a request rate, the result has a unit nobody wants:
hosts times requests per second. What you need is requests per second per host, which is the rate
divided by the hosts. A spreadsheet shows a number either way; nothing flags the error, and nothing
tells you which inputs were guesses. The toolkit refuses a formula whose units do not produce the
declared unit, so it would reject this multiplication on a node declared in requests per second per
host.

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

Look at the two nodes quoted above. Each line names a key, the word before the colon, and gives its value. Five keys in each node matter most: `kind`, `decided`, `unit`,
`value` and `provenance`. `kind` says what sort of node it is: `input` is a number the model is
given. `decided` says who settles the number—`outside` for your users or the world, `you` for your
choice, `definition` for things true whoever asks; both nodes here are `outside`. `unit` lets the
toolkit tell a level from a rate and check every formula. `value` is the number a spreadsheet would
have held.

:::{div}
:class: definition

**`provenance`** records where the value came from and which of three kinds of source it is:
`fact`, `vendor_claim` or `assumption`; both nodes here are `assumption`, the service owners'
estimates.
:::

The bar on an input marked `you` comes from the `decided` field. In a spreadsheet a source is
optional and nobody checks it, but here the build refuses an input without a `decided` key or a
`provenance` source. You can read the source in the viewer's Details panel. A number without
provenance is a rumour.

Three keys are optional: `label`, `note` and `range`. `label` reads better in a table than
`stored_data_t0` does. `note` answers what a reader of the file would otherwise have to ask you; the
note on `stored_data_t0` explains why it stays a single number when the busy-hour figure will not.
`range` sets how far the slider can drag the value. [Appendix A](#appendix-a-dsl-reference) lists
every key a node can have.

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
Interactive viewer: five inputs, none derived from another. Drag a slider to change its number only.
```

**All five nodes are blue and independent.** They are numbers the model is given. Dragging any
slider leaves the others alone, because no node is worked out from another yet.

`annual_growth` is the factor demand is multiplied by each year; a factor above one means growth. The horizon is the time until the next refresh: the period you are sizing for. It is your choice.

### The first derived quantity

In this model, each year's demand is the previous year's multiplied by `annual_growth`. Over the horizon, the model applies it again and again, once for every year; to do that, it must know how many times to apply the factor. The horizon is a length of time in years, but the model needs a count: a plain number with no unit. You can multiply something a number of times, but not a span of time; a horizon of five years means five multiplications, so the model needs the five, not the years. Dividing the horizon by one year cancels the years, leaving a plain number; the divisor is one year because the factor is applied yearly, and dividing by a month would count months when the factor is not applied monthly. That number is `horizon_periods`, the toolkit's first quantity worked out from others:

```{literalinclude} ../models/web_service/stages/04-demand_horizon_exponent/model.yaml
:language: yaml
:start-at:   horizon_periods:
:end-before: outputs:
```

```{iframe} /models/web_service_demand_horizon_exponent-reference.html
:width: 100%
The first derived node.
```

**Hollow means derived.** `horizon_periods` is drawn as an outline because the toolkit works it out
from the formula `horizon / one_year`. The `kind: derived` key says its value is not stated, only
computed. The toolkit checked that the formula's units give the unit the node declares,
`dimensionless`. Drag the horizon slider and `horizon_periods` changes with it. Click the node to
see the formula in Details.

#### Why this matters in practice

The same horizon can be written in different units. The toolkit keeps the unit with the number, so it converts before it counts.

```{include} _generated/what-a-workload-is-three-ways.md
```

The spreadsheet's arithmetic is not the problem. What a cell holding a bare number cannot say is whether it means months, years or something else. Unless the unit is stored somewhere else, every formula that reads the cell carries a hidden assumption about it.

### Growing the demand to the horizon

This model assumes growth compounds: each year the factor multiplies the previous year's demand. When the factor is greater than one, each year's increase is larger than the previous year's. Not every workload grows this way; [ch04](#peak-mean-and-growth) shows how to tell from your own history.

% number-ok: an illustration of what a growth factor is, not a figure from the book's model
If demand grows by 20% a year, the factor is 1.2, and each year's demand is the previous year's multiplied by 1.2.

The calculator below, *Growth, one year at a time*, starts from a round demand, so the arithmetic is easy to follow. Drag the horizon and watch the row of boxes under the sliders, which works from the horizon to the future demand one step at a time.

::::{div}
:class: explorer what-a-workload-is-growth
::::

On the calculator's chart, each chip is one multiplication by the growth factor. There is one chip for each year of the horizon, so the number of chips is `horizon_periods`. Writing the factor out once per year gets long. Mathematics has a short form for repeating multiplication: an exponent, the small raised number in that row of boxes. That number tells how many times the factor is applied, and it is `horizon_periods`. The label above the raised number writes the same thing in code, with `**`, which means raised to the power of.

**An exponent is a count, not a length of time, so it has no unit.**

A `grown` node is not a new idea: it grows a quantity from a starting value over the horizon. Its shape, which you choose when you define the node, determines how it grows: the pattern the growth follows over the years. The toolkit provides three ready-made shapes, each a formula it fills in so you do not write it: `compound` multiplies by the growth factor each year, `linear` adds the same amount each year, and `levelling` grows like `compound` at first before slowing as it nears a ceiling it never passes. [ch04](#peak-mean-and-growth) draws all three side by side in a calculator, and says how to tell which one your workload follows. The two nodes in this model use `compound`, the pattern the calculator drew: each multiplies its starting value by the growth factor once per year. The demand model has two quantities to grow, the busy-hour request rate and the data held, each from its day-one value to the horizon:

```{literalinclude} ../models/web_service/stages/05-demand/model.yaml
:language: yaml
:start-at:   peak_request_rate:
:end-before: outputs:
```

`peak_request_rate` is the request flow at the horizon, in requests per second; `stored_data` is the data held at the horizon, in terabytes. Each key is a piece from the calculator: `start` is the day-one value, `rate` is the growth factor, `over` is the count of years, and `shape: compound` says the factor multiplies each year. From these, the toolkit works out the start times `annual_growth ** horizon_periods`, the exponent from the calculator's row of boxes. The shape is written as a word so you can see it and argue with it. [ch04](#peak-mean-and-growth) says when another shape works better.

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

The toolkit checks the file before it works anything out. If a `derived` node declared in terabytes has a formula multiplying the request rate by a plain number, the toolkit refuses: a rate times a plain number is still a rate, not terabytes. The formula is wrong, not imprecise. Problem 2.4 has you write a mistake of that kind and watch it caught.

### The demand and the decisions

Every input in the file looks the same, but they are one of three kinds: what is outside your
control, what you have decided, and what is true by definition. Outside your control are what your
users send and how much data they create. Separate them first, in any model, including this one:

```{include} _generated/what-a-workload-is-service.md
```

The table groups the inputs by each input's `decided` key. Here is the horizon input as the model file writes it, to show the two keys the table reads:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at:   horizon:
:end-before:   one_year:
```

Its `decided: you` puts the horizon under *What you decide*, and the other values are `outside` for *Outside your control* and `definition` for *True by definition*. A year is true by definition because it is a year whoever asks. The second key the table reads is `provenance`, which says how each value is known. The Claim column's symbol comes from the `kind` under `provenance`: ● marks a fact, ◐ marks a vendor's claim, and ○ marks an assumption. The horizon has `kind: assumption`, so it carries ○.

:::{important}
A value you cannot control, such as the growth rate, looks as settled as a decision you made, such
as the horizon. Two keys answer two different questions: `decided` says who settles the number;
`provenance` says how well it is known. They are independent. In the table above, annual growth
factor and horizon sit in different groups, and both carry ○.

A ○ under *Outside your control* is a number to go and measure. Here all three are. Measuring
narrows how far off the value could be; arguing about it does not. The horizon's ○ is settled by
deciding, not by measuring: its source says it is the refresh cycle the fleet is bought against.
An input under *What you decide* is yours to change; your choice shapes the plan. One under *Outside your control* is not yours to change; only the world or a measurement can move it, and typing a different number changes only the answer on paper.
:::

### What the file computes, and what kind of model it is

Every number in the demand model above came from running this file through the toolkit. The toolkit is a program called `sizing`. Running a model means handing it the file. `sizing` does three things, in this order. First, it reads the file. Second, it checks the units of every formula: a node declared in terabytes must come out in terabytes, or it refuses the file. Third, it works out each derived or grown node from the nodes it names, starting from the inputs. A node is only worked out once everything it uses has a value. The table that follows shows what it produced:

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
chapter adds a measured node or a ceiling to the file. [ch01](#point-estimates)'s problem 1.3 gives
you three model descriptions and asks which kind each one is.

### The same split, on a model that is finished

The second model describes an observability platform: the system that collects what your running services report about themselves, stores those reports and answers questions about them. The platform keeps three kinds of report. Metrics are numbers counted over time, such as how many requests each endpoint served. Logs are lines of text that the code writes. Traces record the path one request took through your services. Here is the same table for its model:

```{include} _generated/what-a-workload-is-observability.md
```

:::{note} The platform's terms
:class: dropdown

% word-ok: a sample here is one stored reading of a series, and a scrape interval is a length of time
- **metric names per host:** How many different metrics each host sends out. Each series is one metric name, on one host, for one combination of label values, so the series total is hosts times metric names times label combinations.
- **one sample per series:** Each collection cycle, the platform takes one sample, one stored reading, from every series. The scrape interval controls how many samples each series adds per day, and samples are what the store holds.
- **extra accidental label values:** Label values that turn up by accident, like a user's identity in a label. Nothing caps them, so they can multiply the series without limit.
- **lines per request:** How many log lines the application writes for each request it serves.
- **queries per second:** How many questions the platform answers each second, from dashboards and alerts.
- **series per query, before labels:** How many metric-and-host combinations one dashboard panel or alert covers. Each label multiplies it, because a query that matches a label reads every series behind it.
- **collector throughput, as quoted:** How many megabytes per second one collector core can process, as the supplier states it. The mark ◐ shows this is a supplier claim, not a measurement.
- **query scan rate, as quoted:** How many series one query node can read each second while answering questions, as the supplier states it. The mark ◐ shows this is a supplier claim, not a measurement.
:::

The *At the reference point* column shows the one value the model uses for each input. For an input
stated as one number, it is that number. Many of this model's inputs are declared as a spread
instead; for those, the column shows the middle of the spread, with half the values below it and
half above. For example, *different endpoint label values* is a count, so any real value of it is a whole number. The model declares this count as a spread, from low to high, because the exact count has not been measured. The middle of that spread can fall between two whole numbers, so the column shows a fraction: not a real count, but the middle of the range of counts the model allows.

% word-ok: a scrape interval is a length of time and a sampling rate is a trace setting
Six rows of *What you decide* are settings you control on the platform itself, falling into four kinds. The scrape interval is how often the platform collects the metrics. You choose how long it keeps each of metrics, logs and traces—three separate retention periods. You choose what share of your requests it records a full trace for—the trace sampling rate. And you choose what share of the log lines it keeps. The rest of *What you decide* is the machines you buy to run it: cores in the collectors that receive the metrics, logs and traces; nodes in the store that hold them, and the usable terabytes on each node; and nodes in the query layer that answer questions. And the horizon. [Appendix F](#appendix-f-observability-model) shows how much smaller the platform gets if you collect metrics less often, keep them for less time, keep fewer log lines and record fewer traces.

When a service reports a metric to the observability platform, it attaches labels. A label is a tag saying, for example, which endpoint handled the request or what status code it returned. The platform keeps a separate running count for every combination of label values, called a series. Each new label multiplies the number of series it stores; each new value of a label adds another set of them. The grid below draws this for one metric on one host.

::::{div}
:class: explorer what-a-workload-is-label-grid
::::

One input decides how many series this platform stores, and how much each query has to read, more than any other: how many different values each label takes. The table lists these under *Outside your control*, not *What you decide*, as *different endpoint label values* and *different status label values*.

None of the platform's settings can change how many label values there are. Turn every setting down as far as it goes and that number stays the same. The only way to change it is to change the application code that attaches the labels. That code belongs to the developers who wrote the services, not to the team that runs the platform.

The figure below draws, from the model's own formulas, what each setting, each label count and each machine reaches:

```{image} _figures/what-a-workload-is-settings-reach.svg
:alt: The platform's settings reach ingest and storage but not the series queries read; the label counts reach all three; the machines you buy add only to capacity
:width: 100%
```

### A workload can be described badly in three ways

**Averaged.** A daily mean is the one number no user of the service experiences. The web service
model uses the busy-hour request rate, not the daily mean.

**In the wrong units.** A count of users is not a workload; it is a fact about a licence agreement.
What sizes a system is what those users cause: requests, bytes, queries. The translation from users
to requests needs a measured constant: requests per user. It changes whenever users change how they
use the product, so it needs re-measuring.

**As a single point in time.** A workload that does not state a growth rate is a workload stated
for today, and hardware is bought to last years, so it sizes a fleet for a moment that will have
passed.

### What the demand side leaves out

Two rows of the web service's inputs table in *The demand and the decisions*, the busy-hour request
rate and the records held on day one, are the workload itself. What the file does not hold yet is
what each request costs: how much processor time it takes. That is not a fact about the workload,
but a fact about one build of the software on one kind of machine. It belongs to a measurement taken
on that machine. Until one is taken, the model holds it as an assumption, and its source says which
measurement would replace it. That processor time, the arrival rate and a count of machines are what
[ch05](#littles-law) through [ch07](#when-adding-servers-stops-helping) build on. The demand side
says what is asked of the system, and how the system responds (such as slowing down as it fills) is
what those chapters add.

## What this cannot tell you

**Whether the quantities are the right ones.** A workload description is a model of demand, and
like every model it leaves things out. The web service model has no notion of requests that differ
from each other: a busy hour of cheap reads and one of expensive writes are the same number in
it. The observability model has no notion of query shape. Each omission is defensible, and each
one is a place the answer could be wrong in a way nothing here would show.

**Where the numbers come from.** Every input in the tables above is a number the model's author
wrote down, and every output is worked out from them. This chapter marked each one's claim, but has not shown how to judge a claim or improve
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
  underneath it; a stock is how much there is now, with no *per* in its unit. Ratios, prices and
  pure numbers like replication factors have no time in them at all.
- **One sizing error turns a flow into a stock by multiplying it by a plain number.** A rate times
  a number is still a rate. Only a duration makes it an amount, and the toolkit refuses the other.
- **A model is a file of named quantities, each with a unit and a source.** A spreadsheet can hold
  both, but does not require either and does not check them. The file requires both on every input,
  and the toolkit checks every formula against the units.
- **Growth compounds, so the horizon has to become a pure number.** Dividing the duration by a
  declared year turns it into an exponent with no unit. A spreadsheet does no division—it takes the
  bare number as years, so when a colleague types months, growth compounds over the wrong number of
  periods with no warning.
- **Separate what is outside your control from what you decided.** A value for something you
  cannot control looks like a decision and stops being questioned.
:::

## Problems

Five, in `tests/what_a_workload_is/`. The first four have tests. The last does not, and says why.

**2.1 — Levels and rates.**
Classify every node in the observability model as a stock, a flow or neither, by reading what each
means: its label, its note, or its name. The table above shows only the inputs;
[Appendix F](#appendix-f-observability-model) lists the rest, each with its label and unit. The test classifies each node by the rule under *Four
kinds of quantity*, using its declared unit. Every unit in this model typechecks, so where your
answer and a unit disagree, your reading missed something the unit records. Find what it missed
before you change your answer. A failed Check lists the nodes that disagree, each with its unit.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_1_stocks_and_flows.py -m problem
```

**2.2 — Turn a rate into a volume.**
Write the formula for a node called `daily_ingest`, which the page shows with its unit `TB` and an
empty formula. It should give the telemetry that arrives in one day, metrics and logs only, as an
amount in terabytes. Start from `known_ingest`, the rate at which metrics and logs arrive together
in megabytes a second. Traces are left out because the traces chain has no value—spans per request
has not been measured. A rate times a plain number is still a rate, and the toolkit refuses the
formula until something in it carries a length of time. The test adds every node you declare to the
observability model and makes `daily_ingest` an output. Any input you add must have a `decided` key
and a provenance with a source, like every input in the book.

```bash
python3 -m pytest tests/what_a_workload_is/test_problem_2_daily_volume.py -m problem
```

**2.3 — The smallest model that builds.**
Write a model file of your own with one input and one derived node. It must pass the loader, the
unit check, and every rule the build applies to a model. [Appendix A](#appendix-a-dsl-reference)
lists the keys a file needs, under *The file*; the keys a node can have, under *The node
kinds*; and the rules the build applies, under *What the build checks*. Read them before you
start: the refusals are the point. At a desk, the same rules appear at the top of
`scripts/verify-models.py`.

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

**2.5 — Your own workload.** No test: this is about a system you run, and there is
no oracle for it.

Take something you operate and write down the quantities that describe what it has to do. Not the
metrics you happen to collect: the quantities you would need to size it. Give each one a
unit. Then sort them: which are rates, which are levels, which are neither.

Two things to look for when you have finished. Is there a quantity you could not give a unit to?
That is usually two quantities sharing a name, and splitting them is the work. And is there
anywhere you have sized a store from a rate, a retention volume derived from a per-second figure
with no duration anywhere in the chain? That is the error this chapter exists to prevent. It is
much easier to find in your own notes than to believe in the abstract.

A good answer fits on one page, has a unit against every line, and leaves you less sure about at
least one quantity than you were before you wrote it down.

To write it as a model file rather than notes, [Your own model](#your-own-model) describes a tool
that asks for each key in turn.

## Where to go next

[ch03](#where-the-numbers-come-from) answers the question this chapter kept deferring: once you have
written a quantity down, what are you claiming about it?

[ch04](#peak-mean-and-growth) takes up the other question this chapter raised: demand moves, so
which value of it sizes the fleet?
