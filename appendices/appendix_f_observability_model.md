---
title: "The observability model, in full"
short_title: "Appendix F · Observability model"
---

(appendix-f-observability-model)=
# Appendix F · The observability model, in full

:::{note} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | The book's sizing exemplar, including what is not yet measured |
| **Model** | `models/observability/model.yaml` |
| **Built from** | `observability-reference`, `observability-knobs_turned_down` |
:::

Metrics, logs and traces, for an estate stated in [ch02](#what-a-workload-is)'s terms. Vendor
neutral: nothing on this page names a product, and the structure is what transfers.

This is the book's **second model**, and it shows what [Appendix E](#appendix-e-web-service-model)
does not. Three multiplicative chains run through it: metrics, logs and traces. They share inputs
at two points. The growth factor feeds all three, and the request rate feeds logs and traces, so
they rise and fall together even where you declare no correlation between them. Label cardinality,
a product of three uncertain counts of label values, drives the active series count and the query
path. The logs chain does not use it.

% word-ok: a scrape interval is a length of time, and sampling traces keeps some and drops the rest
The control knobs set how much telemetry you keep and for how long: the scrape interval, the
retention period for each signal, the fraction of log lines retained and the trace sampling rate.
None of them is money. Three tiers (ingest, store and query) carry four ceilings between them, and no
single number summarises them.

It is a **conditional model**: it has measured constants and ceilings, and a model with either is
conditional ([ch01](#point-estimates)). So `scripts/verify-models.py` holds it to stricter rules:
every ceiling must declare its headroom and say why. Two of its measured constants have not been
measured, on purpose: spans per request, which the traces chain needs, and collector throughput per
core as measured, which one of the two ingest ceilings needs. The next section says what each needs.

## What is not yet measured

```{include} ../chapters/_generated/appendix-f-observability-model-unmeasured.md
```

Spans per request belongs to one instrumented application at one version. No body of data in this
repository contains it, so a `corpus` measurement cannot derive it. No machine produces it, so a
`rig` measurement cannot take it either. It is an `estate` observation: taken on a system you run.
Nobody can repeat it, and nobody can check it, so its stamp must record the system, the window it
covers and the date.

Nobody has taken it. So the traces chain has no value, and every table below shows the traces
chain's rows as *not yet measured*. Why leave it empty rather than filling in a plausible figure? An
invented figure would print in every table below exactly like a measured one, and nothing on the
page would tell you which was which.

The model declares collector throughput per core twice, on purpose. Once it is the vendor's quoted
figure, a claim in the file. It gives the ceiling *ingest utilisation, quoted* a value. Once it is a
measurement that has not been taken, which leaves the ceiling *ingest utilisation, measured* in the
ceilings table, under *The four ceilings, one of which cannot be computed*, showing *not yet
measured*.

This measurement is a different kind from spans per request. It is a `rig` measurement: a
throughput, taken on the book's declared reference machine and refused on any other. Whoever has
that machine can take it again and check it.
[ch03 · Where the numbers come from](#where-the-numbers-come-from) explains how the book records a
vendor's figure as a claim and keeps it apart from a measurement.

## The graph

```{iframe} /models/observability-reference.html
:width: 100%
The model, live: move an input and every node recomputes. A node with a dashed border and a dash
(—) in place of its value cannot be computed yet.
```

Two nodes are drawn dashed because they are the unmeasured constants themselves: *spans per
request* and *collector throughput per core, measured*. Every node that depends on either of them
is drawn dashed too. Click on a dashed node and Details names the constant it is waiting for. The
dashed nodes answer the question: "What would measuring this one thing give a value to?" The
toolkit works that out from the graph; nobody wrote the list. The graph is wider than the page.
Scroll it sideways, or press **Expand** to open it at full width.

## Every formula

The graph above, as text: every derived quantity and every ceiling, with the formula the file
gives it. The table is rendered from the file, so it cannot disagree with it.

```{include} ../chapters/_generated/appendix-f-observability-model-formulas.md
```

## The three chains

```{include} ../chapters/_generated/appendix-f-observability-model-outputs.md
```

Metrics are cheap in bytes and expensive in series. Logs are the reverse. The traces rows read
*not yet measured* because the traces chain needs spans per request, which has not been measured.
The model does not say where traces would fall between the other two.

Look hardest at the active series count. It is driven by label cardinality, and label cardinality
is the product of three counts of label values: the endpoint label, the status label and the
accidental label. The table below gives each count's range and the range of the product, with the
top of each range divided by the bottom, so you can compare how wide they are.

```{include} ../chapters/_generated/appendix-f-observability-model-spread.md
```

The product's range is wider than the widest of its three counts, which is the accidental label.
It is much narrower than if you multiplied the three counts' spreads together. The reason: the
model draws the three counts independently. A high draw of one usually meets middling or low draws
of the others, so they partly cancel. The chart below shows the product's spread, with the point
estimate marked on it.

```{image} ../chapters/_figures/appendix-f-observability-model-cardinality.svg
:alt: Label cardinality as a distribution — a product of uncertain counts
:width: 100%
```

## The four ceilings, one of which cannot be computed

```{include} ../chapters/_generated/appendix-f-observability-model-ceilings.md
```

The four ceilings sit on three tiers: two on ingest, one on the query path, one on the retention
store. Two mechanisms, not three, hold them up. Both ingest ceilings and the query ceiling rest on
queueing, where response time climbs long before anything is fully busy
([ch06](#queueing-and-the-knee)). The store ceiling rests on rebuild: losing a node costs capacity
you were using ([ch11](#headroom-and-failure-domains)). The table's *Headroom* column holds two
margins: one for the three queueing ceilings and a smaller one for the store. The margins look
alike only because both are percentages. That is the argument for declaring headroom per ceiling
rather than one margin for the whole model.

Two of the three ceilings that can be computed divide a total with traces left out. The quoted
ingest ceiling divides the ingest of metrics and logs only. The store ceiling divides the data
stored for metrics and logs only. The query ceiling does not involve traces in its formula. Each
ceiling carries its reason in the model file, in a `because` key. Here are the two ingest ceilings
as the file writes them:

```{literalinclude} ../models/observability/model.yaml
:language: yaml
:start-at:   quoted_pipeline_utilisation:
:end-before:   # -- output two
```

The first `because` says the quoted ceiling is understated twice over: its numerator leaves out
traces, and its denominator is a vendor's claim. The second ceiling divides the total with traces
by the measured capacity, and it cannot be computed because both halves wait on a measurement. Its
row reads *not yet measured* in the table above. The store ceiling's `because` says the same of
stored data: a verdict of ok there means ok with traces ignored. [ch20](#the-missing-node) is about
what it costs to forget.

## What moves the answer

```{image} ../chapters/_figures/appendix-f-observability-model-tornado-chart.svg
:alt: Which input moves the active series count most
:width: 100%
```

```{include} ../chapters/_generated/appendix-f-observability-model-tornado.md
```

The accidental label is at the top of the tornado: the label nobody planned, added during an
incident and never removed. [ch08](#regime-changes) sets this apart from a threshold: the accidental
label makes label cardinality a wide product of counts, which a chain of multiplications can hold,
and not a regime change.

Each bar swings one input from the low end of its band to the high end, with every other input
held at its point value. Only inputs the model draws at random get a bar: those given a
distribution in the file (a `distribution` key), and the measured constants, which carry a
standard error. An input given as one number has no bar, however much it matters. Two of those
multiply the active series count directly: *hosts* and *metric names per host*. Each is given as
one value (`value:`), with no distribution, so neither appears in the tornado. A slider range does
not make an input uncertain. The last row of the table counts the inputs that do have a spread but
do not reach the active series count at all. The chart gives the same count.

## Turning the knobs

```{include} ../chapters/_generated/appendix-f-observability-model-scenarios.md
```

% word-ok: a scrape interval is a length of time, and sampling traces keeps some and drops the rest
The model has six knob inputs of four kinds: the scrape interval, a retention period for each of
the three signals, the fraction of log lines kept and the trace sampling rate. The right-hand
column is the same model with one knob of each kind turned down, the metrics retention being the
one adjusted. Its [interactive page](/models/observability-knobs_turned_down.html) has every slider
already moved. The scenario file sets them like this:

```{literalinclude} ../models/observability/scenarios/knobs_turned_down.yaml
:language: yaml
:start-at: overrides:
```

Ingest and storage fall a long way when you compare the rows for ingest and for storage, metrics
and logs only, across the two columns. Two ceilings went over their hard limit in a large share of
the model's futures, and in the right-hand column they almost never do: the quoted ingest ceiling
and the store ceiling. Read the last two rows. So the knobs rescued two ceilings that were at risk.

**The query ceiling does not move at all.** Its row and its chance of going over the limit read the
same in both columns. So do the active series count and label cardinality. The reason is in the
formulas: none of the four knobs appears in the chain behind the query ceiling. The query path's
load is queries a second times series per query, and series per query is a base count times label
cardinality. A query has to walk past every series that a label multiplied. Two things move the
query ceiling: the size of the query tier, which is a decision you make, and fewer label values.
Fewer label values means changing the application that emits the label, which is a conversation
with whoever added it.

## Where the inputs came from

```{include} ../chapters/_generated/appendix-f-observability-model-provenance.md
```

```{include} ../chapters/_generated/appendix-f-observability-model-measured.md
```

## What this cannot tell you

**The log store fills at the busy-hour rate.** The log chain starts from the request rate, and the
request rate in this model is the busy hour across the estate, not the daily mean. Logs stored is
logs ingest times the retention period. So the model fills the log store as if every hour of the
retention period were the busy hour. The model has no ratio between the busy hour and the mean,
which the web service model carries ([ch04](#peak-mean-and-growth)). So it cannot say by how much
the log store is oversized. The metrics chain does not have this fault: a scrape takes one value
from each series on a timer, whatever the traffic.

% word-ok: a sample here is one reading a scrape takes, a counting unit, not one of the model's draws
**The store holds nothing but compressed data.** Every stored figure is ingest times retention, and
nothing else. The model has no term for anything a store keeps beside the compressed data, such as
indexes. The bytes per sample, per line and per span were measured with this repository's own
encoder and a general-purpose compressor, not with any store's own format. The *Measured against*
column of the table above says which for each.

**The query path does not grow.** Neither the host count nor the growth factor appears in it. So the query ceiling at the end of the horizon is the query ceiling today,
while ingest and storage grow. The query path also counts series, not time: a query over a long
stretch of history costs the model the same as a query over the last few minutes. No retention or
time-range term feeds it.

Drawing more futures from the model will not find any of these. Each is a term the file does not
contain, and [ch20](#the-missing-node) is about that kind of error.

## Running it yourself

```bash
python3 -m bench.run_models --model observability
python3 scripts/verify-models.py
python3 scripts/render-figures.py
python3 -m pytest tests/test_models.py
```

Two measurements are missing, and they are of different kinds.

Spans per request: take it on a system you run, and stamp it as an `estate` observation that
records the system, the window it covers and the date. With it, span rate, traces ingest, traces
stored and total ingest get values.

Collector throughput per core: a `rig` measurement, taken on the reference machine. With it, the
measured pipeline capacity gets a value. The ceiling *ingest utilisation, measured* needs both measurements.

Once a result file exists, re-run the commands above. Nothing in the model file changes: the two
nodes already name the files they read. The *not yet measured* rows in the tables then show values,
and the dashed nodes in the graph fill in.
