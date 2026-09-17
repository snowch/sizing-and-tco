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

Metrics, logs and traces, for an estate stated in [ch01](#what-a-workload-is)'s terms. Vendor
neutral: nothing on this page names a product, and the structure is what transfers.

This is the **sizing exemplar**: it shows what [Appendix E](#appendix-e-storage-model) could not.
Three multiplicative chains hang off the same few roots, so they move together whether or not
anybody says so. Label cardinality is a product of uncertain counts and therefore dominates
everything downstream of it. The control knobs are sampling and retention rather than money. Three
tiers — ingest, store and query — carry four ceilings between them, and no single number
summarises them.

And it has a hole in it, deliberately left open.

## What is not yet measured

```{include} ../chapters/_generated/appendix-f-observability-model-unmeasured.md
```

Spans per request is a property of somebody's instrumented application at a particular version.
It is not a property of any corpus, so this repository cannot derive it, and it is not a property
of any machine, so the reference rig cannot measure it either. It belongs to the `estate` target:
an observation somebody takes of a system they run.

Nobody has taken it. So the whole traces chain has no value, and the figures below show that
rather than filling it in. **This is not a gap waiting to be tidied up before publication.** It is
what an honest sizing model looks like before the work is done, and putting it on a published page
is the clearest statement this book can make about the difference between a missing number and an
invented one.

The same is true of collector throughput per core. The model declares it twice on purpose: once as
the vendor's quoted figure, which lets a ceiling be computed, and once as a measurement nobody has
taken, which leaves a second ceiling with nothing in it but the words *not yet measured*.
Reading those two rows next to each other is most of [ch02](#where-the-numbers-come-from).

## The graph

:::{tip} Try it
The same model, [as an interactive page](/models/observability-reference.html). Turn the four
knobs and watch which ceilings move — and which one does not. The
[knobs-turned-down scenario](/models/observability-knobs_turned_down.html) is the same model with
all four already moved.
:::

```{image} ../chapters/_figures/appendix-f-observability-model-graph.svg
:alt: The observability model as a dependency graph, with the unmeasured chain marked
:width: 100%
```

The unmeasured constants are drawn hollow, and everything downstream of them is dimmed. The
dimmed nodes are the answer to "what would measuring this one thing unlock", and nobody had to
write that answer down.

## The three chains

```{include} ../chapters/_generated/appendix-f-observability-model-outputs.md
```

Metrics are cheap in bytes and expensive in series. Logs are the reverse. Traces would be
somewhere in between, and the model declines to guess.

Look hardest at the active series count. A cardinality node drives it, and that node is the
product of three uncertain counts — a product of uncertain things is far more uncertain than any
of them:

```{image} ../chapters/_figures/appendix-f-observability-model-cardinality.svg
:alt: Label cardinality as a distribution — a product of uncertain counts
:width: 100%
```

## The four ceilings, one of which cannot be computed

```{include} ../chapters/_generated/appendix-f-observability-model-ceilings.md
```

Three tiers, three different mechanisms, three different margins — and that is the argument for
declaring headroom per ceiling rather than globally. The ingest and query margins are about
queueing, where response time climbs long before anything is busy
([ch05](#queueing-and-the-knee)). The store margin is about rebuild, where losing a node costs
capacity you were using ([ch10](#headroom-and-failure-domains)). They only look alike because they
are both percentages.

Two of the three that can be computed rest on an incomplete total. The `because` on each says so,
and [ch19](#the-missing-node) is about what it costs to forget.

## What moves the answer

```{image} ../chapters/_figures/appendix-f-observability-model-tornado-chart.svg
:alt: Which input moves the active series count most
:width: 100%
```

```{include} ../chapters/_generated/appendix-f-observability-model-tornado.md
```

The accidental label — the one nobody planned, added during an incident and never removed — is at
the top of the tornado. [ch07](#regime-changes) is the chapter about that, and here it is
demonstrated rather than warned about.

## Turning the knobs

```{include} ../chapters/_generated/appendix-f-observability-model-scenarios.md
```

The right-hand column doubles the scrape interval, cuts metric retention by most of a year, keeps
a tenth of the log lines and samples one trace in a hundred. Ingest and storage fall a long way.

**The query ceiling does not move at all.** Not by a little — not at all, because none of the four
knobs touches cardinality, and cardinality is what a query has to walk past. The controls a
platform gives you operate on the chains that were already affordable, and the input that decides
the size of the system is not one of them. That is the most useful thing on this page. Fixing
cardinality means a conversation with whoever added the label.

## Where the inputs came from

```{include} ../chapters/_generated/appendix-f-observability-model-provenance.md
```

```{include} ../chapters/_generated/appendix-f-observability-model-measured.md
```

## Running it yourself

```bash
python3 -m bench.run_models --model observability
python3 scripts/verify-models.py
python3 scripts/render-figures.py
python3 -m pytest tests/test_models.py
```

To close the hole: measure spans per request on a system you run, stamp it as an `estate`
observation with the system and the window disclosed, and every dimmed node on this page lights
up with no other change to the model.
