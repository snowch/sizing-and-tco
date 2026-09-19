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

This is the model the chapters build a few nodes at a time, and it is a **sizing model by the
rule and by its shape**. Most of it is accounting identity and physics — requests times CPU time
per request, watts times hours times price, capital plus running cost over a horizon — which is
the structure [the introduction](#preface) says sampling the inputs is sufficient for. But it
carries one measured constant and six ceilings, so `scripts/verify-models.py` classifies it a
sizing model and holds it to the stricter rules. That is the right call: a compression ratio
belongs to a codec, and a fleet asked for more than it can serve does not slow down
proportionally. [Appendix F](#appendix-f-observability-model) is the book's second model, and
shows what one looks like when a whole chain of it has not been measured.

## The graph

:::{tip} Try it
The same model, [as an interactive page](/models/web_service-reference.html): every slider comes
from a range this model file declares, moving one recomputes the whole graph immediately, and
clicking any node shows what fed it and how uncertain it is. **Resample** runs the book's own
sampler in your browser with the inputs you have moved held at their values.
:::

```{image} ../chapters/_figures/appendix-e-web-service-model-graph.svg
:alt: The web service model as a dependency graph, coloured by node kind
:width: 100%
```

Colour is kind: inputs, derived quantities, the one measured constant, and the ceilings. An
input's border says what it is claiming — solid for a fact, dashed for a vendor's claim, dotted
for an assumption. Arrows run from cause to effect, and every node sits immediately to the right
of the last thing it depends on.

Read two things off it directly. The graph is **wide at the left and narrow at the right**: a
great many quantities collapsing into a handful of answers, which is what makes a single wrong
input so hard to spot downstream. And **three separate chains reach the host count** — the
request rate, the working set and the data on disk — which is
[ch10](#bandwidth-and-the-binding-constraint)'s whole subject.

## The outputs

```{include} ../chapters/_generated/appendix-e-web-service-model-outputs.md
```

## Where each ceiling sits

```{include} ../chapters/_generated/appendix-e-web-service-model-ceilings.md
```

The verdict column is about the plan; the last two columns are about the world. A design that is
under its hard limit and inside the margin it declared has not failed — it has spent the reserve
it was keeping for the failure it has not had yet ([ch11](#headroom-and-failure-domains)).

## What moves the answer

```{image} ../chapters/_figures/appendix-e-web-service-model-tornado-chart.svg
:alt: Which input moves the five-year total most, when swung across its middle 80%
:width: 100%
```

```{include} ../chapters/_generated/appendix-e-web-service-model-tornado.md
```

Each bar swings one input across the middle of its own declared range with everything else held
still. The ordering is the useful part: it says which input to go and measure first
([ch19](#which-input-is-the-answer)). It is also a one-at-a-time analysis, so an input whose
effect only appears in combination with another gets a short bar here and can still be the thing
that sinks you.

## The answer as a distribution

```{image} ../chapters/_figures/appendix-e-web-service-model-distribution.svg
:alt: Cost per million requests, as a distribution
:width: 100%
```

Unit cost rather than total cost, because it is the figure that behaves least like people expect.
A fleet bought for growth that then arrives is cheap per request; the same fleet is expensive if
the growth never comes. The distribution carries both futures, and a single number carries
neither.

## Where the inputs came from

```{include} ../chapters/_generated/appendix-e-web-service-model-provenance.md
```

```{include} ../chapters/_generated/appendix-e-web-service-model-measured.md
```

One measured constant, and its conditions are on the row: a compression ratio belongs to a codec
and a body of data, and this one was measured over a synthetic corpus of application records that
this repository generates. The method transfers; the number does not. Point the runner at a
sample of your own records ([ch03](#where-the-numbers-come-from)).

## Two scenarios, side by side

```{include} ../chapters/_generated/appendix-e-web-service-model-scenarios.md
```

The left column buys what the point estimates recommend. The right buys for the growth case the
model thinks is plausible but not expected. The difference in capital is a number, and so is the
difference in how often each ceiling breaks. Choosing between them is a judgement somebody has to
make and defend, which is [ch21 · A TCO for a finance audience](#a-tco-for-finance).

## Running it yourself

```bash
python3 -m bench.run_models --model web_service     # evaluate, sample, stamp
python3 scripts/verify-models.py                    # units, provenance, ceilings, shape
python3 scripts/render-figures.py                   # re-render every figure above
python3 -m pytest tests/test_models.py              # the reference outputs, asserted
```

Every figure on this page came from `bench.run_models`. `verify-models.py` refuses a model that
does not typecheck, and `tests/test_models.py` is what stops any of it changing silently.
