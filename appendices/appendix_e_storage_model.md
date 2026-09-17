---
title: "The storage cluster model, in full"
short_title: "Appendix E · Storage model"
---

(appendix-e-storage-model)=
# Appendix E · The storage cluster model, in full

:::{note} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | Cost-shaped arithmetic, classified a sizing model, through every toolkit output |
| **Model** | `models/storage_cluster/model.yaml` |
| **Built from** | `storage_cluster-reference`, `storage_cluster-sized_for_growth` |
:::

A generic scale-out storage cluster, sized from a stated workload and costed over five years. No
product is named and none is implied: what is on this page is a structure, and the numbers in it
are placeholders for yours.

This model is the book's **cost exemplar in shape and a sizing model by the rule**. Almost all of
it is accounting identity and physics — watts times hours times price, capital plus running cost
over a horizon — which is the structure [the introduction](#preface) says sampling the inputs is
sufficient for. But it carries one measured constant and two ceilings, so
`scripts/verify-models.py` classifies it a sizing model and holds it to the stricter rules. That
is the right call: the compression ratio belongs to a codec, and a cluster that runs out of space
does not fail proportionally. A model is not a cost model because most of it looks like one.
[Appendix F](#appendix-f-observability-model) shows what a model looks like when even the
arithmetic stops being a chain.

## The graph

:::{tip} Try it
The same model, [as an interactive page](/models/storage_cluster-reference.html): every slider
comes from a range this model file declares, moving one recomputes the whole graph immediately,
and clicking any node shows what fed it and how uncertain it is. It does not resample — the
intervals belong to the scenario, and the page says so when you move off it.
:::

```{image} ../chapters/_figures/appendix-e-storage-model-graph.svg
:alt: The storage cluster model as a dependency graph, coloured by node kind
:width: 100%
```

Colour is kind: inputs, derived quantities, the one measured constant, and the ceilings. An
input's border says what it is claiming — solid for a fact, dashed for a vendor's claim, dotted
for an assumption. Arrows run from cause to effect, and every node sits immediately to the right
of the last thing it depends on.

Read two things off it directly. The graph is **wide at the left and narrow at the right**: two
dozen quantities collapsing into a handful of answers, which is what makes a single wrong input so
hard to spot downstream. And **two separate chains reach the node count** — capacity and bandwidth
— which is [ch09](#bandwidth-and-the-binding-constraint)'s whole subject.

## The outputs

```{include} ../chapters/_generated/appendix-e-storage-model-outputs.md
```

## Where each ceiling sits

```{include} ../chapters/_generated/appendix-e-storage-model-ceilings.md
```

The verdict column is about the plan; the last two columns are about the world. A design that is
under its hard limit and inside the margin it declared has not failed — it has spent the reserve
it was keeping for the failure it has not had yet ([ch10](#headroom-and-failure-domains)).

## What moves the answer

```{image} ../chapters/_figures/appendix-e-storage-model-tornado-chart.svg
:alt: Which input moves the five-year total most, when swung across its middle 80%
:width: 100%
```

```{include} ../chapters/_generated/appendix-e-storage-model-tornado.md
```

Each bar swings one input across the middle of its own declared range with everything else held
still. The ordering is the useful part: it says which input to go and measure first
([ch18](#which-input-is-the-answer)). It is also a one-at-a-time analysis, so an input whose
effect only appears in combination with another gets a short bar here and can still be the thing
that sinks you.

## The answer as a distribution

```{image} ../chapters/_figures/appendix-e-storage-model-distribution.svg
:alt: Cost per usable TB per month, as a distribution
:width: 100%
```

Unit cost rather than total cost, because it is the figure that behaves least like people expect.
A cluster bought for growth that then arrives is cheap per terabyte; the same cluster is expensive
if the growth never comes. The distribution carries both futures, and a single number carries
neither.

## Where the inputs came from

```{include} ../chapters/_generated/appendix-e-storage-model-provenance.md
```

```{include} ../chapters/_generated/appendix-e-storage-model-measured.md
```

One measured constant, and its conditions are on the row: a compression ratio belongs to a codec
and a body of data, and this one was measured over a synthetic corpus this repository generates.
The method transfers; the number does not. Point the runner at a sample of your own estate
([ch02](#where-the-numbers-come-from)).

## Two scenarios, side by side

```{include} ../chapters/_generated/appendix-e-storage-model-scenarios.md
```

The left column buys what the point estimates recommend. The right buys for the growth case the
model thinks is plausible but not expected. The difference in capital is a number, and so is the
difference in how often each ceiling breaks. Choosing between them is a judgement somebody has to
make and defend, which is [ch20](#a-tco-for-finance).

## Running it yourself

```bash
python3 -m bench.run_models --model storage_cluster   # evaluate, sample, stamp
python3 scripts/verify-models.py                      # units, provenance, ceilings, shape
python3 scripts/render-figures.py                     # re-render every figure above
python3 -m pytest tests/test_models.py                # the reference outputs, asserted
```

Every figure on this page came from `bench.run_models`. `verify-models.py` refuses a model that
does not typecheck, and `tests/test_models.py` is what stops any of it changing silently.
