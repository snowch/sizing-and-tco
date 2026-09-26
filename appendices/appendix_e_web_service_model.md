---
title: "The web service model, in full"
short_title: "Appendix E · Web service model"
---

(appendix-e-web-service-model)=
# Appendix E · The web service model, in full

:::{note} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | The running example, through every toolkit output |
| **Model** | `models/web_service/model.yaml` |
| **Built from** | `web_service-reference`, `web_service-sized_for_growth` |
:::

A web service and the data it keeps, on a fleet of Linux hosts, sized from a stated busy hour and
costed over five years. No product is named and none is implied: what is on this page is a
structure, and the numbers in it are placeholders for yours.

This is the model the chapters build a few nodes at a time, shown whole on this page. Most of the
model is accounting identity and physics: requests times CPU time per request, watts times hours
times price, capital plus running cost over a horizon. For that part, [ch01](#point-estimates) tells
you that sampling the inputs is sufficient. But the model carries one measured constant and six
ceilings, and either one makes a model conditional. `scripts/verify-models.py` classifies this model
conditional and holds it to stricter rules. The answer is not guaranteed to be right even if every
input is. A measured constant like a compression ratio belongs to one codec and one body of data, so
a ratio right for measured data can be wrong for yours. A ceiling marks where the system stops
acting as a chain of multiplications: a fleet asked for more than it can serve does not slow down in
proportion. [Appendix F](#appendix-f-observability-model) is the book's second model and shows what
one looks like when a whole chain of it has not been measured.

## The graph

:::{tip} Try it
The same model, [as an interactive page](/models/web_service-reference.html): inputs with a range
get sliders; the slider's range is for exploration, not the distribution used in the tornado below.
Some inputs have no range and no slider, such as *engineers, full-time equivalent*, the tornado's
top bar. Moving a slider recomputes the graph immediately; clicking any node shows its dependencies
and uncertainty. **Resample** runs the book's own sampler in your browser with the inputs you have
moved held at their values.
:::

```{image} ../chapters/_figures/appendix-e-web-service-model-graph.svg
:alt: The web service model as a dependency graph, coloured by node kind
:width: 100%
```

Colour codes the kind of box: input, derived quantity, the one measured constant, or ceiling. An
input's border tells you what it is claiming: solid for a fact, dashed for a vendor's claim, dotted
for an assumption. A bar down the left edge of an input (*you decide* in the legend) marks one you
choose, such as *hosts in the fleet*. Lines run left to right, from cause to effect. Every box sits
immediately before the first box that uses it.

The node labels are small at page width; find the names on the interactive page or in the formula
and provenance tables below. The graph is **wide at the left and narrow at the right**: many
quantities collapse into a handful of answers, which is what makes a single wrong input hard to spot
downstream. Three separate chains reach a single meeting point: the request rate, the working set,
and the data on disk each produce a host count — *hosts for requests*, *hosts for memory*, and
*hosts for storage*. These meet at *hosts the model recommends*, which takes the largest. *Hosts the
model recommends* feeds nothing else in the graph; the fleet the model prices is *hosts in the
fleet*, which you decide. Which of the three chains sets the answer is the subject of
[ch10](#bandwidth-and-the-binding-constraint).

## Every formula

The graph above, as text: every derived quantity and every ceiling, with the formula the file gives
it and the chapter that added it. The table is rendered from the model file, so it cannot disagree
with it. Each row shows the label and in backticks the name the file uses; formulas refer to nodes
by those names.

```{include} ../chapters/_generated/appendix-e-web-service-model-formulas.md
```

## The outputs

```{include} ../chapters/_generated/appendix-e-web-service-model-outputs.md
```

## Where each ceiling sits

```{include} ../chapters/_generated/appendix-e-web-service-model-ceilings.md
```

*At the plan* shows the quantity the ceiling watches, calculated at every input's point estimate,
for *hosts in the fleet*; *Allowed* is the limit minus the headroom the model declares. *Verdict*
judges the plan: *ok* at or below the allowed line, *into the margin* past allowed but before the
limit, **over** past it. *Over allowed* and *Over limit* show futures the model drew. Each is the
share of futures where the quantity crosses that line, so a percentage says how often that happens,
not how far the quantity goes beyond it.

One row has a verdict other than *ok*: *utilisation, counting coordination*, which reads *into the
margin*. It counts work the hosts do for each other, so it is always higher than plain utilisation.
None of the three chains setting *hosts the model recommends* counts this work; the fleet bought on
that recommendation keeps its margin on plain utilisation and spends it on coordination. Its *Over
limit* column shows the largest share in the table. A design under its hard limit and inside its
declared margin has not failed; it has spent the reserve it was keeping for a failure it has not yet
encountered ([ch11](#headroom-and-failure-domains)).

## What moves the answer

```{image} ../chapters/_figures/appendix-e-web-service-model-tornado-chart.svg
:alt: Which input moves the five-year total most, when swung across its middle 80%
:width: 100%
```

```{include} ../chapters/_generated/appendix-e-web-service-model-tornado.md
```

Each bar moves one input from its p10 to its p90, with every other input held at its point estimate.
The p10 and p90 come from the distribution the model draws that input from, not from the slider's
range on the interactive page. The ordering tells you which input to go and measure first
([ch19](#which-input-is-the-answer)). It is one input at a time, so an input whose effect appears
only with another can still move the answer a long way.

**Every bar is a cost input, and the demand side is not here at all.** No request rate, no growth
rate, no records held. That is not an omission in the chart. The total prices the fleet that was
bought, and the fleet is `hosts` — a number somebody decided, not one the model derived. More
data does not buy more hosts by itself; it makes the fleet you have too small, and the model says
so through the disk and cache ceilings rather than through the bill. Drag *records held, day one*
on the interactive page and watch the recommendation and those two ceilings move while the total
sits still. The panel names, for any input, which outputs it can move and which it cannot.

For demand to move the five-year total, you have to re-decide the fleet, which is what the second
scenario below does.

## The answer as a distribution

```{image} ../chapters/_figures/appendix-e-web-service-model-distribution.svg
:alt: Cost per million requests, as a distribution
:width: 100%
```

This is the cost per million requests, not the five-year total. The reference fleet was bought at
the point estimates and held fixed in every future, so its cost moves only a little from future to
future: prices and running costs shift. The number of requests moves a great deal, following the
busy-hour rate, peak-to-mean ratio and growth rate. Cost per million is the total divided by
requests, so when demand comes high the same cost spreads over many requests and each is cheap; when
demand comes low, each is expensive. The outputs table above shows the unit cost's range, against
its own middle value, is far wider than the total's. The distribution carries all these futures; a
single number carries none.

## Where the inputs came from

```{include} ../chapters/_generated/appendix-e-web-service-model-provenance.md
```

```{include} ../chapters/_generated/appendix-e-web-service-model-measured.md
```

Every input the model has is listed in the first table, with its kind — fact, vendor claim or
assumption — and the source the model file gives for it. The name in backticks is the one the
formulas use, so an input you meet in the formula table can be looked up here.

% word-ok: a sample of your own records is a handful of records, not one of the model's draws
One measured constant, and its conditions are on the row: a compression ratio belongs to a codec
and a body of data, and this one was measured over a synthetic corpus of application records that
this repository generates. The method transfers; the number does not. Point the runner at a
sample of your own records ([ch03](#where-the-numbers-come-from)).

## Two scenarios, side by side

```{include} ../chapters/_generated/appendix-e-web-service-model-scenarios.md
```

The left column buys the fleet the model recommends at the point estimates. The right column buys
the fleet the p90 growth case would need — growth that is plausible but not expected. Only *hosts in
the fleet* differs between them; *hosts the model recommends* is the same in both because the
recommendation does not depend on the fleet you buy. The difference in capital is a number, and so
is the difference in how often each ceiling goes over its limit: the right column costs more, and
four ceilings about load and space — *utilisation at the busy hour*, *utilisation with one host
down*, *working set against memory*, *disk fill at horizon* — are over their limits in far fewer of
its futures.

More hosts means more coordination between them. *Fraction of the fleet doing nothing useful* rises,
and in the right column's plan it is past that ceiling's allowed line. *Fraction of the peak already
built* reaches past one at the top of the right column's range; past it, each host added lowers
throughput. *Utilisation, counting coordination* stays over its limit in a large share of the right
column's futures and falls far less than the load and space ceilings do. *How much the queueing view
understated it* is larger in the right: the bigger fleet loses more to coordination than plain
utilisation shows. Choosing between the two is a judgement that you or whoever signs the plan must
make and defend, which is [ch21 · A TCO for a finance audience](#a-tco-for-finance).

## What this cannot tell you

**Whether the fleet is the right one.** The model prices `hosts`, and `hosts` is a decision. Every
figure on this page is conditional on it, and nothing here argues for the number: the reference
scenario takes the recommendation at the point estimates, which is how the decision is usually
taken and is not the same as it being right. The ceilings say whether that fleet survives the
model's futures; they cannot say whether a different fleet would have been a better buy. That
comparison is a second scenario and a judgement, which is [ch21](#a-tco-for-finance).

**What the structure leaves out.** The chains here are demand, memory and disk, and they meet only
at *hosts the model recommends*. Nothing connects a request to the record it writes, so the model
cannot work out whether traffic and data grow together. It assumes they do, through a single input —
*annual growth factor* — that multiplies both the busy-hour request rate and the records held. That
is a stronger assumption than a correlation: a correlation would let the two tend to grow together
while differing in any one future, but a shared factor makes them grow at the same rate in every
future the model draws. The model's two declared correlations are about other inputs: busy-hour
request rate with CPU time per request, and host price with network price per host. There is no tier
that fails differently from the others, no request that costs more than its neighbour, and no second
site. Sampling the inputs harder will not find any of that: an omission is not a wide interval, it
is a chain that was never drawn ([ch20](#the-missing-node)).

**Whether five years is the right horizon.** It is a decision too, and it sets how much of the
total is capital and how much is running cost. A different horizon does not just scale the answer;
it changes which half of the bill the argument is about ([ch15](#capex-opex-and-lifecycle)).

## Running it yourself

```bash
python3 -m bench.run_models --model web_service     # evaluate, sample, stamp
python3 scripts/verify-models.py                    # units, provenance, ceilings, shape
python3 scripts/render-figures.py                   # re-render every figure above
python3 -m pytest tests/test_models.py              # the reference outputs, asserted
```

Every figure on this page came from `bench.run_models`. `verify-models.py` refuses a model that
does not typecheck, and `tests/test_models.py` is what stops any of it changing silently.
