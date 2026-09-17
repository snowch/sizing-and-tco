---
title: "Bandwidth, and the binding constraint"
short_title: "ch09 Bandwidth, and the binding constraint"
---

(bandwidth-and-the-binding-constraint)=
# ch09 · Bandwidth, and the binding constraint

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch08 · Capacity](#capacity) |
| **What it produces** | How often each of the storage model's two chains decides the answer |
| **Built from** | `binding-constraint`, `storage_cluster-reference` |
:::

## The question

When two independent chains each demand a different size, which one are you actually buying?

[ch08](#capacity) followed one chain from stored bytes to machines. There is a second chain, it
disagrees with the first, and the disagreement is not something to average away.

## The material

### Two chains, sharing nothing

A storage cluster has to hold the data and it has to serve it. Those are different requirements
with different arithmetic, and neither one is derivable from the other.

The capacity chain runs from bytes stored through replication, compression and overhead to a
number of machines. The bandwidth chain runs from a peak read rate through what one machine can
sustain to a different number of machines. They share the workload and nothing else.

```{image} _figures/bandwidth-and-the-binding-constraint-capacity.svg
:alt: The node count the capacity chain asks for
:width: 100%
```

```{image} _figures/bandwidth-and-the-binding-constraint-throughput.svg
:alt: The node count the bandwidth chain asks for
:width: 100%
```

Two distributions, two different shapes, and a great deal of overlap. Neither one is the answer.

### Buy the larger, not the average, the usual winner or the sum

The count that satisfies both is the larger of the two, and problem 9.1 is that one function
call. Spend a minute on the three wrong answers first. Each of them has shipped:

**The average.** Satisfies neither chain. A cluster sized halfway between what capacity needs and
what bandwidth needs is too small for one of them by construction, and which one depends on the
day.

**The usual winner.** Take the capacity chain because it is larger most of the time. The commonest
of the three, and defensible until somebody asks the model how often "most of the time" is.

**The sum.** Buys a cluster for a workload that does not exist. The two chains describe the same
machines doing two things, not two sets of machines.

### How often each one wins

```{include} _generated/bandwidth-and-the-binding-constraint-table.md
```

Capacity decides most of the time. That matches most people's intuition, and it is why the second
chain gets dropped. The two gap rows are the reason not to drop it.

The median gap between the chains is large. These are not two estimates of the same thing that
differ slightly; they are two different questions with two different answers. The gap at the 95th
percentile is larger still.

### The shortfall, conditional on the constraint binding

A constraint that binds rarely looks harmless, and it looks harmless because of how people
summarise it. Average the shortfall across all samples — including the majority where the
neglected chain does not bind and the shortfall is zero — and you get a small number.

Compute it **conditional on the constraint binding** and you get a different number entirely,
because the cases where the neglected chain wins are exactly the cases where it wins by a lot.
That is not a coincidence. One chain only overtakes the other when its own inputs have gone
somewhere unusual, and by the time they have, the gap is wide.

So the honest summary of a rarely-binding constraint is two numbers: how often, and how badly when
it does. One of them alone is a way of not answering, and problem 9.2 computes both.

### Why this gets worse with more chains

The storage model has two. A real estate has more: rebuild bandwidth, metadata operations, a
control plane, a network fabric, a licence tier. Each is another chance for the answer to be set
by something nobody was watching.

The probability that *some* constraint binds unexpectedly rises with the number of chains, even
while the probability of any particular one doing so stays small. A model with six chains, each
binding a fraction of the time, spends most of its life with at least one of them unexpectedly in
charge.

The observability model in [Appendix F](#appendix-f-observability-model) has three parallel chains
and three separate ceilings for exactly this reason. There is no single number that summarises
them, and a model that produced one would be hiding the thing you needed.

## What this cannot tell you

**Whether there are only two chains.** This model has the two somebody thought of. A chain that is
not in the model cannot bind inside it, however often it binds outside. That is
[ch19](#the-missing-node), and nothing here addresses it.

**What a node can actually sustain.** The bandwidth chain rests on a vendor's quoted throughput
per node, marked as such in every figure. It has never been measured here and is the kind of
figure that is quoted under ideal conditions with nothing else running.

**Anything about the two chains interacting.** They are treated as independent demands on the same
machines. They are not: reading hard makes writing slower, rebuilding consumes both, and a cluster
at its capacity limit is usually also a cluster whose bandwidth is being spent on rebalancing.

**Which chain binds *for you*.** The shares above come from one model's uncertainty over one
stated workload. A read-heavy estate and an archival one are the same model with different inputs
and opposite answers.

## Problems

Two, in `tests/bandwidth_and_the_binding_constraint/`.

**9.1 — Two chains, one purchase.**
One function call. Work out what happens under each of the three obvious wrong answers before
writing the right one.

```bash
python3 -m pytest tests/bandwidth_and_the_binding_constraint/test_problem_1_both.py
```

**9.2 — The cost of forgetting the chain that usually loses.**
Compute how often the neglected chain binds, and the median shortfall *in those samples only*.
Nobody computes the second, and it is what stops a rarely-binding constraint looking harmless.

```bash
python3 -m pytest tests/bandwidth_and_the_binding_constraint/test_problem_2_cost.py
```

## Where to go next

[ch10](#headroom-and-failure-domains) is the margin that sits under both chains, and why it is two
different margins rather than one.

[ch11](#the-sizing-model) puts the whole of Part III together and produces a number.
