---
title: "Capacity"
short_title: "ch09 Capacity"
---

(capacity)=
# ch09 · Capacity

## The question

How far is what you buy from what you can use?

Further than most people's first estimate, and always in the same direction: you buy more than you
can use. Four terms separate the two, and nobody writes them down together.

## The material

### The chain

```{image} _figures/capacity-graph.svg
:alt: The chain from what you need to store to how many machines you must buy
:width: 100%
```

Four terms stand between an application's storage requirement and a purchase order. Two multiply
what you must buy, one divides it, and one is a surcharge.

**Replication.** Whole copies. Three copies cost three times the space, survive two losses, and
are the simplest thing that works. Erasure coding buys the same durability for less space by
spreading it over more pieces, and problem 9.2 is that comparison. Erasure coding is not cleverer,
only amortised: it pays for the space it saves with reads that touch more machines — a bandwidth
problem, and therefore [ch10](#bandwidth-and-the-binding-constraint)'s.

**Compression.** The only term that helps you, and the only one that is a measured constant rather
than a decision:

```{include} _generated/capacity-measured.md
```

Read the last column. That ratio belongs to one codec and one body of data — not to compression,
and not to your data. Take the method rather than the number: point the runner at a sample of your
own estate and get the ratio that belongs in your model ([ch03](#where-the-numbers-come-from)).

**Overhead.** Filesystem metadata, indexes, journals, superblocks: the space the storage layer
keeps for itself. Small per unit, and applied to everything.

**The fill limit.** People forget this one because it is not a property of the data at all. You
cannot run a storage system full, and [ch11](#headroom-and-failure-domains) is about why the
margin is a rule rather than a number. It is in the chain here because the space you hold back is
space you still have to buy.

### Every term but one makes you buy more

Compression is the only term that helps. It is also the only one measured rather than decided: the
other three are decisions, and a decision is certain, while a measurement over somebody's corpus
carries a standard error.

A sizing that treats all four as constants is optimistic in exactly one place, and that place has
the most uncertainty in it.

### Two kinds of terabyte, and the ten per cent

A drive's datasheet says a trillion bytes. A filesystem counts in powers of two. The difference is
about a tenth, both are called a terabyte in conversation, and a tenth is a large fraction of what
compression was going to buy you.

So every node in this book declares a unit, and the build converts rather than assuming. Problem 9.3 is that conversion, and this is the chapter where getting it wrong costs money.

### What comes out

```{include} _generated/capacity-outputs.md
```

Two rows need a word before they mean anything. *Fill level at horizon* is how full the cluster is
at the end of the period it was bought for, as a fraction of what it can hold. One is full. An
interval reaching past one says that in some futures the data does not fit, because the arithmetic
carries on past the point the disks stop. *Nodes purchased* shows no interval because it is not a
prediction: somebody decided it, and the rest of the table is what the model says about that
decision.

The interval on the node count spans most of an order of magnitude, and almost all of that is the
growth rate from [ch04](#peak-mean-and-growth) rather than anything in this chapter's chain. The
capacity arithmetic is the well-understood part of the problem. What it is applied to is not.

## What this cannot tell you

**What your data compresses to.** The constant above was measured over a synthetic mixture this
repository generates, and the mixture's proportions are an assumption stated in the stamped
result. For this figure, that assumption is a larger source of error than the codec, the shard
spread, or anything the standard error reports. The number has an uncertainty and the uncertainty
is about the wrong thing.

**Anything about small objects.** The chain above is a chain of bytes. A cluster storing many
small objects spends a substantial and sometimes dominant share of its capacity on metadata. The
overhead term here is a flat multiplier and cannot express that. A model of an estate with a
small-object problem needs a term this one does not have.

**What happens during a rebuild.** Every figure is a healthy cluster. Losing a node means
re-replicating its data somewhere, using capacity and bandwidth that were doing something else,
and the capacity chain has no term for the window in which that is happening
([ch11](#headroom-and-failure-domains)).

**Whether capacity is the chain that binds.** It usually is, and the model does not assume it.
[ch10](#bandwidth-and-the-binding-constraint) is the other chain, and how often each of them
decides the answer.

## Problems

Four, in `tests/capacity/`.

**9.1 — The chain.**
Four terms, one of which divides. Getting the division upside down gives an answer wrong by the
square of the compression ratio while still looking entirely plausible — check yours against a
case you can do in your head first.

```bash
python3 -m pytest tests/capacity/test_problem_1_raw.py
```

**9.2 — Erasure coding against copies, at equal safety.**
Work out the replication factor that survives the same number of losses as a given code, so the
two can be compared on space rather than on enthusiasm. Then notice what the saving grows with,
and what else grows with it.

```bash
python3 -m pytest tests/capacity/test_problem_2_erasure.py
```

**9.3 — The other kind of terabyte.**
Re-declare every capacity node in binary units and change nothing else. The outputs must come out
smaller by exactly the right ratio, and the model must still typecheck. If you find yourself
editing a value to compensate, stop.

```bash
python3 -m pytest tests/capacity/test_problem_3_binary_units.py
```

**9.4 — Turn it back into a cost model.**
Remove what made the storage model a sizing model in this chapter, keep it working, and then write
one sentence saying what the result can no longer tell anybody. If you cannot name it, you removed
something that was doing no work — and the model should not have had it.

```bash
python3 -m pytest tests/capacity/test_problem_4_classification.py
```

## Where to go next

[ch10](#bandwidth-and-the-binding-constraint) is the second chain, and the question of which of
the two you are actually buying.

[Appendix D](#appendix-d-units) is the terabyte problem and the rest of the conversions that bite.
